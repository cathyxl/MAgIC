from typing import List, Dict, Union
import random
import openai
import re

from .base import Environment, TimeStep
from ..message import Message, MessagePool
from ..agent import SIGNAL_END_OF_CONVERSATION
from ..config import EnvironmentConfig
import os
import json
import re

DEFAULT_TOPIC = """

You have 100 starting points to contribute to the communal pool each round. You need to remember how much money you still have after each round and avoid to exceed the all 100 points in {game_round} rounds.
"""


class Public_Good(Environment):
    type_name = "public_good"

    def __init__(self, player_names: List[str], topic_codes: Dict[str, List[str]] = None, competition=None, **kwargs):
        super().__init__(player_names=player_names, topic_codes=topic_codes, **kwargs)


        # The "state" of the environment is maintained by the message pool
        self.message_pool = MessagePool()
        self._decide_rounds = 0
        self.score = [100,100,100]
        self.decision = {'Player 1':'','Player 2':'','Player 3':''}
        self.mapping = {0:'Player 1',1:'Player 2',2:'Player 3'}

        # Randomly sample a topic, code and chameleon player
        self.topic = DEFAULT_TOPIC.format(game_round=competition["game_round"])
        self.competition = competition
        self.game_round = competition["game_round"]
        self.interest_multiplier = competition["multiplier"]
        self.chameleon_name = None
        
        # Game states
        self._current_turn = 0
        self._next_player_idx = 0
        self._current_phase = "decide"  # "negotiate", "vote"
        self._players_votes = None
        self._initialized = False
        self._single_history = False
        self.test_start = True
        self.pool_total = 0
        self.share=0
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

    def reset(self):
        """
        sample topic, code and chameleon code
        """

        self._current_turn = 0
        self._next_player_idx = 0
        self._current_phase = "decide"
        self.pool_total = 0
        self.share=0
        self.score = [100,100,100]
        self.decision = {'Player 1':'','Player 2':'','Player 3':''}
        self.game_round = self.competition["game_round"]
        self.interest_multiplier = self.competition["multiplier"]
        self.test_player_name = self.competition["test_player_name"]
        self.game_setting = self.competition

        self.message_pool.reset()

        self._moderator_speak(f"Now the game starts! The background is: {self.topic}")

        self._moderator_speak(
            f"Now everyone gives your decision"
            f"We will start with {self.player_names[0]}.")
        self._current_turn = 1

        self._players_votes = {name: 0 for name in self.player_names}

        self._initialized = True
        init_timestep = TimeStep(observation=self.get_observation(),
                                 reward=self.get_zero_rewards(),
                                 terminal=False)

        return init_timestep

    def print(self):
        self.message_pool.print()

    def get_observation(self, player_name=None) -> List[Message]:
        """
        get observation for the player
        """
        if player_name is None:
            return self.message_pool.get_all_messages()
        else:
            return self.message_pool.get_visible_messages(player_name, turn=self._current_turn)

    def _text2vote(self, text, player_name) -> str:
        """
        convert text to vote, return a player's name
        """
        # lower = text.lower().replace("[", "").replace("]", "").replace(".", "")

        openai.api_key = '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'

        prompt = "Help me to identify which player's opinion they agree with in their expression\n\n" + player_name + ' says: ' + text + "\n\n only give me 'A', 'B' or 'C' to show which opinion of the player they agree with, don't add any other words"
        
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                        messages=[{'role':'user','content':prompt}],                                    
                                        temperature = 0,
                                        n=3,
                                       max_tokens=2000)

        # print(prompt)
        # print(response['choices'][0]['message']['content'].lower())
        # print('!!!!!')

        return response['choices'][0]['message']['content'].lower()
    
    def _scoring(self, decision):
        def extract_bid(player_sentence):
            prompt = [{'role':'user','content':"help me to extract how many points contributed in below sentence: \n ' "+ player_sentence + "' \nonly give me the number, do not say any other words"}]
            # print(prompt)
            # 调用OpenAI API
            openai.api_key = os.environ.get("OPENAI_API_KEY")
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=prompt,
                temperature=0,
                max_tokens=50,
                stop=None
            )
            
            bid = response.choices[0]['message']['content']
            #bid = player_sentence
            bid = ''.join(filter(str.isdigit, bid))  # 提取数字
            # print(bid)
            
            return int(bid) if bid.isdigit() else 0

        def extract_bid_re(player_sentence):
            # pattern =r"I will contribue (\d+)"
            # match = re.search(pattern, player_sentence)
            # if match:
            #     bid = match.group(1)
            # else:
            #     print("cannot parse the decision")
            #     bid = 0
            # print("++++++>", bid)
            # return int(bid) if bid.isdigit() else 0

            pattern = r'\b\d+\b'
            points = re.findall(pattern, player_sentence)
            number_of_points = int(points[0])
            # print("Number of points:", number_of_points)
            return number_of_points

        # print('begin')
        # print(self.score)
        for i, player in enumerate(decision):
            player_sentence = decision[player]
            bid_amount = extract_bid_re(player_sentence)
            self.pool_total += bid_amount
            # print(player,bid_amount)
            # print("==========>", bid_amount)
            self.score[i] -= bid_amount
        
        # print('after')
        # print(self.score)

        return self.score
    
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

        terminal=False


        assert player_name == self.get_next_player(), f"Wrong player! It is {self.get_next_player()} turn."
        if self._current_phase == "decide":

            message = Message(agent_name=player_name, content=action, turn=self._current_turn, visible_to="Moderator")
            #message = Message(agent_name=player_name, content=action, turn=self._current_turn)
            self.message_pool.append_message(message)

            # Update the counters
            self._current_turn += 1
            
            # print(self._next_player_idx)
            
            self.decision[self.mapping[self._next_player_idx]] = action
            
            
            if self._next_player_idx < len(self.player_names) - 1:
                self._next_player_idx += 1
            else:
                self._next_player_idx = 0
                self._decide_rounds += 1  # Increase the decide rounds counter
                
                # Check if 5 rounds of decision have been completed
                self._scoring(self.decision)
                # print('outside')
                # print("after bid: ", self.score)

                if self._decide_rounds < self.game_round:
                    self._moderator_speak(f"Round {self._decide_rounds} is over. \n Player 1 said: {self.decision['Player 1']} \nPlayer 2 said: {self.decision['Player 2']} \nPlayer 3 said: {self.decision['Player 3']} \n You can look around others' decisions and think your decision for next round. Now let us move to next round")
                    
                    self._current_turn += 1
                else:
                    self._current_phase = "Terminate"
                    self._moderator_speak(f"{self.game_round} rounds of decisions have been completed.")
                    self._current_turn += 1
                    # calculate the share
                    # print()
                    self.share = self.pool_total* self.interest_multiplier/len(self.player_names)
                    self.score = [s + self.share for s in self.score]
                    # print("at the end of the game,", self.score)

                    terminal = True
                
                
                self.decision = {'Player 1':'','Player 2':'','Player 3':''}

            timestep = TimeStep(observation=self.get_observation(),
                                reward=self.get_zero_rewards(),
                                terminal=terminal)  # Return all the messages
        # ... (rest of the code remains the same)
        # elif self._current_phase == "Terminate":
            
        #     if len(set(self.score)) == 1:
        #         self._moderator_speak(f"Player0 is the winner")
        #     else:
        #         max_value = max(self.score)

        #         # 找到最大值的索引
        #         max_index = self.score.index(max_value)
            
        #         self._moderator_speak(f"Player{max_index+1} is the winner")
        #     terminal = True
            
        #     timestep = TimeStep(observation=self.get_observation(), reward=self.get_zero_rewards(), terminal=terminal)

        # # Check if the player signals the end of the conversation
        # if self.is_terminal():
        #     timestep.terminal = True

        return timestep