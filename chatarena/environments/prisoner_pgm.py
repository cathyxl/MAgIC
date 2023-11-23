from typing import List, Dict, Union
import random
import openai
import json
import re

from .base import Environment, TimeStep
from ..message import Message, MessagePool
from ..agent import SIGNAL_END_OF_CONVERSATION
from ..config import EnvironmentConfig
from prompts.prisoner_prompt import *
DEFAULT_TOPIC = """

The scoring is as follows:
- If all three choose to cooperate, they each get 3 points.
- If all three choose to defect, they each get 1 point.
- If one chooses to defect and the others choose to cooperate, the betrayer gets 100 points and the collaborators each get 0 points.
- If two choose to defect and the other chooses to cooperate, the betrayers each get 2 points, and the collaborator gets 0 points.

The game is played for 5 rounds, and the total score is calculated at the end to determine the winner.

"""


class Prinsoner_Dilemma_PGM(Environment):
    type_name = "prisoner_pgm"

    def __init__(self, player_names: List[str], topic_codes: Dict[str, List[str]] = None, competition=None, **kwargs):
        super().__init__(player_names=player_names,  topic_codes=topic_codes, **kwargs)


        # The "state" of the environment is maintained by the message pool
        self.message_pool = MessagePool()
        self._decide_rounds = 0
        self.score = [0,0,0]
        self.decision = {'Player 1':'','Player 2':'','Player 3':''}
        self.mapping = {0:'Player 1',1:'Player 2',2:'Player 3'}

        # Randomly sample a topic, code and chameleon player
        self.topic = DEFAULT_TOPIC
        self.competition = competition
        
        # Game states
        self._current_turn = 0
        self._next_player_idx = 0
        self._current_phase = "decide"  # "negotiate", "vote"
        self._players_votes = None
        self._initialized = False
        self._single_history = False
        self.decision_command = "You must reply with \"Cooperate\" or \"Defect\""
        self.pgm_prompt = pgm
        self.pgm_decision = pgm_decision
        self.single_pgm = True
        self.test_start = False

        
        self.reset()  # To initialize the game (select topic, code, chameleon)

    def get_next_player(self) -> str:
        """
        get the next player
        """
        return self.player_names[self._next_player_idx]
        #if self._current_phase != "negotiate":
        #    return self.player_names[self._next_player_idx]
        #else:
        #    return self.chameleon_name

    def reset(self):
        """
        sample topic, code and chameleon code
        """
        self.topic = self.competition["topic"]
        
        self.test_player_name = self.competition["test_player_name"]
        self.decision_scores = self.competition["topic_values"]
        self.game_setting = self.competition

        self.player_models = [self.game_setting["test_player"]["model"] if p == self.test_player_name else self.game_setting["non-test_player"]["model"] for p in self.player_names]
    
        
        self._current_turn = 0
        self._next_player_idx = 0
        self._current_phase = "decide"
        self.score = [0,0,0]
        self.decision = {'Player 1':'','Player 2':'','Player 3':''}

        self.message_pool.reset()

        self._moderator_speak(f"Now the game starts!")
        self._moderator_speak(self.topic)


        self._moderator_speak(
            f"This the first round. Now everyone give your decision. "
            f"We will start with {self.player_names[0]}.")
        self._current_turn = 1

        self._players_votes = {name: 0 for name in self.player_names}

        self._initialized = True
        request_msg = self.decision_command
        init_timestep = TimeStep(observation=self.get_observation(),
                                 reward=self.get_zero_rewards(),
                                 request_msg=request_msg,
                                 terminal=False)
        

        return init_timestep

    def print(self):
        self.message_pool.print()
    def log_game(self, path):
        max_score = max(self.score) 
        winner = []
        for pi in range(len(self.score)):
            if self.score[pi] == max_score:
                winner.append(pi)
        # print(self.player_names, self.test_player_name)
        if self.player_names.index(self.test_player_name) in winner:
            result = "win"
        else:
            result = "lose"
        # if result == "win":
        #     print(f"Test player: {self.test_player_name} win the game")
        # else:
        #     print(f"Non test player win the game")
        messages = self.get_observation()
        message_rows = []
        for message in messages:
            message_row = {
                "agent_name": message.agent_name,
                "content": message.content,
                "turn": message.turn,
                "timestamp": str(message.timestamp),
                "visible_to": message.visible_to,
                "msg_type": message.msg_type,
            }
            message_rows.append(message_row)
        with open(path, "w") as f:
            json.dump({
                "test_player_name": self.test_player_name, 
                "game_setting": self.game_setting,
                "history": message_rows,
                "result": result,
                "scores": self.score,
                }, 
                f, indent=4)
        return result


    def get_observation(self, player_name=None) -> List[Message]:
        """
        get observation for the player
        """
        if player_name is None:
            return self.message_pool.get_all_messages()
        else:
            messages = self.message_pool.get_visible_messages(player_name, turn=self._current_turn)
            if self.single_pgm and self._current_phase=="decide":
                pgm_messages = self.message_pool.get_pgm_messages(player_name, turn=self._current_turn)
                if len(pgm_messages)>0:
                    messages.append(pgm_messages[-1])
            return messages
        

    
    def _scoring(self, decision):

        
        # 处理决策：转换为小写并移除.<EOS>
        processed_decisions = {}
        for player, dec in decision.items():
            dec = re.sub(r'\.<eos>$|\.$', '', dec.lower())
            if dec.find("cooperate")>=0:
                processed_decisions[player] = "cooperate"
            else:
                processed_decisions[player] = "defect"
            
            
        # processed_decisions = {key: re.sub(r'\.<eos>$|\.$', '', value.lower()) for key, value in decision.items()}
        
        # copy = copy.deepcopy(self.score)
        cur_score = [0,0,0]

        # 计算cooperate和defect的数量
        cooperate_count = sum(1 for decision in processed_decisions.values() if decision == 'cooperate')
        defect_count = sum(1 for decision in processed_decisions.values() if decision == 'defect')
        assert cooperate_count + defect_count == len(self.player_names)

        # 根据规则更新分数
        if cooperate_count == 3:
            cur_score = [self.decision_scores["cooperate"], self.decision_scores["cooperate"], self.decision_scores["cooperate"]]
        elif defect_count == 3:
            cur_score = [self.decision_scores["defect"], self.decision_scores["defect"], self.decision_scores["defect"]]
        elif cooperate_count == 2 and defect_count == 1:
            betrayer_index = next(i for i, decision in enumerate(processed_decisions.values()) if decision == 'defect')
            cur_score[betrayer_index] = self.decision_scores["one_defect"]
        elif cooperate_count == 1 and defect_count == 2:
            betrayers_indices = [i for i, decision in enumerate(processed_decisions.values()) if decision == 'defect']
            for index in betrayers_indices:
                cur_score[index] = self.decision_scores["two_defect"]
        else:
            print("do not support")


        self.score = [a + b for a, b in zip(self.score, cur_score)]


    def _moderator_speak(self, text: str, visible_to: Union[str, List[str]] = "all"):
        """
        moderator say something
        """
        message = Message(agent_name="Moderator", content=text, turn=self._current_turn, visible_to=visible_to)
        self.message_pool.append_message(message)

    def get_rewards(self, chameleon_win: bool) -> Dict[str, float]:
        """
        get rewards for each player
        """
        rewards = {}
        for name in self.player_names:
            # The winner gets 1, the loser gets 0
            rewards[name] = float((name == self.chameleon_name) == chameleon_win)

        return rewards

    def is_terminal(self) -> bool:
        """
        check if the conversation is over
        """
        # If the last message is the signal, then the conversation is over
        if self.message_pool.last_message.content.startswith(SIGNAL_END_OF_CONVERSATION):
            return True

    def are_all_values_same(self, dictionary):
        values = list(dictionary.values())
        first_value = values[0]
        
        for value in values[1:]:
            if value != first_value:
                return False
        
        return True

    def find_next_pgm_player(self, next_player_idx):
        if next_player_idx == len(self.player_names):
            return None
        for pi in range(next_player_idx, len(self.player_names)):
            if self.player_models[pi].find("pgm") < 0:
                continue
            else:
                return pi 
        return None

    def is_pgm_player(self, next_player_idx):
        if self.player_models[next_player_idx].find("pgm") < 0:
            return False
        else:
            return True
        
    def step(self, player_name: str, action: str) -> TimeStep:
        """
        step function that is called by the arena
        Args:
            player_name: the name of the player that takes the action
            action: the action that the agents wants to take
        """
        # If not initialized, reset the environment
        if not self._initialized:
            self.reset()

        terminal = False
        request_msg = None
        assert player_name == self.get_next_player(), f"Wrong player! It is {self.get_next_player()} turn."
        
        if self._current_phase == "decide":
            
            message = Message(agent_name=player_name, content=action, turn=self._current_turn, visible_to="Moderator")
            self.message_pool.append_message(message)

            # Update the counters
            self._current_turn += 1
                        
            self.decision[self.mapping[self._next_player_idx]] = action
            
            
            if self._next_player_idx < len(self.player_names) - 1:
                self._next_player_idx += 1
                if self.is_pgm_player(self._next_player_idx):
                    request_msg = self.pgm_decision 
                else:
                    request_msg = self.decision_command
            else:
                self._next_player_idx = 0
                self._decide_rounds += 1  # Increase the decide rounds counter
                
                # Check if 5 rounds of decision have been completed
                
                if self._decide_rounds < 5:
                    self._moderator_speak(f"Round {self._decide_rounds} is over.\nPlayer 1 said: {self.decision['Player 1']} \nPlayer 2 said: {self.decision['Player 2']}  \nPlayer 3 said: {self.decision['Player 3']}\nYou can look around others' decisions and think your decision for next round. Now let us move to next round")
                    self._current_turn += 1
                else:
                    self._current_phase = "Terminate"
                    terminal=True
                    self._moderator_speak("5 rounds of decisions have been completed.")
                    self._current_turn += 1
                
                self._scoring(self.decision)
                # print(self.score)
                self.decision = {'Player 1':'','Player 2':'','Player 3':''}

                self._current_phase = "pgm"
                self._next_player_idx = self.find_next_pgm_player(self._next_player_idx)
                if self._next_player_idx is not None:
                    player_name = self.player_names[self._next_player_idx] 
                    oth_players = [p for p in self.player_names if p!= player_name]
                    request_msg = self.pgm_prompt.format(player_name=player_name, oth_player1=oth_players[0], oth_player2=oth_players[1])
                    # print(request_msg)
                else:
                    self._next_player_idx=0
                    self._current_phase = "decide"
                    if self.is_pgm_player(self._next_player_idx):
                        request_msg = self.pgm_decision 
                    else:
                        request_msg = self.decision_command
                    

            # print("request_msg=================> ", request_msg)
            timestep = TimeStep(observation=self.get_observation(),
                                reward=self.get_zero_rewards(),
                                request_msg=request_msg,
                                terminal=terminal)  # Return all the messages


        elif self._current_phase == "pgm":
            message = Message(agent_name=player_name, content=action, turn=self._current_turn, visible_to=self.player_names[self._next_player_idx], is_pgm=True, is_show=False)
            self.message_pool.append_message(message)
            self._current_turn += 1
            self._next_player_idx += 1
            self._next_player_idx = self.find_next_pgm_player(self._next_player_idx)
            if self._next_player_idx is not None:
                player_name = self.player_names[self._next_player_idx] 
                oth_players = [p for p in self.player_names if p!= player_name]
                request_msg = self.pgm_prompt.format(player_name=player_name, oth_player1=oth_players[0], oth_player2=oth_players[1])
            else:
                self._next_player_idx = 0
                self._current_phase = "decide"
                # request_msg = self.pgm_decision 
                if self.is_pgm_player(self._next_player_idx):
                    request_msg = self.pgm_decision 
                else:
                    request_msg = self.decision_command


            timestep = TimeStep(observation=self.get_observation(),
                                reward=self.get_zero_rewards(),
                                request_msg=request_msg,
                                terminal=terminal)  # Return all the messages

        else:
            print("do not support the phase, ", self._current_phase)

        return timestep