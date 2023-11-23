from typing import List, Dict, Union
import random
import re
import json
import time
import os
import numpy as np
from .base import Environment, TimeStep
from ..message import Message, MessagePool
from ..agent import SIGNAL_END_OF_CONVERSATION
from ..config import EnvironmentConfig
from prompts.undercover_prompt import *



class Undercover_Competition(Environment):
    type_name = "undercover_competition"
 
    def __init__(self, player_names: List[str], topic_codes: Dict[str, List[str]] = None, competition=None, **kwargs):
        super().__init__(player_names=player_names, topic_codes=topic_codes, **kwargs)

        self.topic_codes = topic_codes

        self.message_pool = MessagePool()

        # Topic setting
        self.undercover_code = None
        self.non_undercover_code = None
        self.undercover_name = None
        self.non_undercover_names = None 
        
        self.add_pgm_metric = False
        self.metric_templates = metric_pgm_template_questions
        

        # Game states
        self._current_turn = 0
        self._next_player_idx = 0
        self._current_phase = "give clues"  # "give clues", "accuse", "guess"
        self._metric_turn = 0
        self._next_clue_player_idx = 0

        self._players_votes = None
        self._initialized = False
        self._win_group = -1
        self.player_backends = {}
        self.competition = competition
        self.game_setting = None
        self.rewrite_game_setting = False
        self._max_round = 2
        self._current_round = 0
        self._single_history=False
        self.test_start = False

        self.fix_partial = True if "fix_partial" not in competition else competition["fix_partial"]  # Partially fix the response
        self.add_pgm_metric = True  if "add_pgm_metric" not in competition else competition["add_pgm_metric"]  # Do pgm metric at the same time.
        self.only_pgm_metric = False if "only_pgm_metric" not in competition else competition["only_pgm_metric"]  # Only do pgm metric, no clue, no pgm, no
        if self.add_pgm_metric and self.only_pgm_metric: # we fix all the input when only calculate pgm metric
            self.fix_partial = False
    

        self.reset()  # To initialize the game (select topic, code, undercover)

    def get_next_player(self) -> str:
        """
        get the next player
        """
        if self._current_phase != "guess":
            return self.player_names[self._next_player_idx]
        else:
            return self.undercover_name
    
    def log_game(self, path, source_path=None):
        """
        save the game history and results:
        game setting, backend setting, game history and result
        """
        
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
                "is_pgm": message.is_pgm,
            }
            message_rows.append(message_row)
        
        if not self.only_pgm_metric:
            assert self._win_group >= 0
            result = "non-undercover" if self._win_group == 0 else "undercover"
        else:
            result = None
        
        if source_path:
            with open(source_path) as f:
                d = json.load(f)
            result = d["result"]
            self._win_group  = d["win_flag"]
            self._vote_for_each_player = d["player_vote"]

        with open(path, "w") as f:
            json.dump({
                "undercover": self.undercover_name, 
                "game_setting": self.game_setting,
                "player_backends": self.player_backends, 
                "history": message_rows,
                "win_flag": self._win_group,
                "result": result,
                "player_vote": self._vote_of_each_player,
                "consistency_metric": self.consisteny_dict,
                "pgm_metric": self.pgm_metric_dict,
                }, 
                f, indent=4)

    def get_win_group(self):
        assert self._win_group >= 0
        return "non-undercover" if self._win_group == 0 else "undercover"

    def save_game_setting(self, game_setting):
        now = time.strftime("%m%d%H%M%S", time.localtime(time.time()))
        fname = f"results/game_settings/{now}"
        if os.path.exists(fname):
            k = 1
            while True:
                nfname = f"{fname}-{k}"
                if not os.path.exists(nfname):
                    break
                k += 1
            fname = nfname
            
        with open(fname,"w") as f:
            json.dump(game_setting, f)
    
    def reset(self):
        """
        sample topic, code and undercover code
        """
        if self.competition["random"]:
            topic_group_idx = random.choice(range(len(self.topic_codes))) 
            self.undercover_code, self.non_undercover_code = np.random.choice(self.topic_codes[topic_group_idx], size=2, replace=False)
            self.undercover_name = random.choice(self.player_names)
        else:
            self.undercover_code = self.competition["undercover_code"]
            self.non_undercover_code = self.competition["non_undercover_code"]
            self.undercover_name = self.competition["undercover_name"]
        self.undercover_idx = self.player_names.index(self.undercover_name)
        self.game_setting = {"undercover_code": self.undercover_code, "non_undercover_code": self.non_undercover_code, "undercover_name": self.undercover_name}

        self.non_undercover_names = [name for name in self.player_names if name != self.undercover_name]
        
        # reset the players' backends depends on their roles
        self.player_backends = {}
        if self.competition:
            for player_name in self.player_names:
                if player_name == self.undercover_name:
                    self.player_backends[player_name] = self.competition["undercover"]
                else:
                    self.player_backends[player_name] = self.competition["non-undercover"]

        self._current_turn = 0
        self._next_player_idx = 0
        self._current_phase = "give clues"
        self._current_round = 0
        self._metric_turn = 0
        self._next_clue_player_idx = 0
        self.consisteny_dict={}
        self.pgm_dict={}
        self.pgm_metric_dict={}
        self.test_start = False

        self.message_pool.reset()

        self._moderator_speak(f"Now the game starts!")
        self._moderator_speak(f"Your word is: {self.undercover_code}",
                              visible_to=self.undercover_name)
        for player_name in self.non_undercover_names:
            self._moderator_speak(f"Your word is: {self.non_undercover_code}",
                              visible_to=player_name)
        self._moderator_speak(
            f"Now everyone gives one clue (but never include the secret word). "
            f"You cannot repeat what others has said. We will start with {self.player_names[0]}.")
        self._current_turn = 1
        self.update_test_start(0)

        self._players_votes = {name: 0 for name in self.player_names}
        self._vote_of_each_player= {name: None for name in self.player_names}
        self._win_group = -1 # 0, none undercover; 1(right vote, guessed right),2(wrong vote),3(even vote)

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

    def _text2vote(self, text) -> str:
        """
        convert text to vote, return a player's name
        """
        # lower = text.lower().replace("[", "").replace("]", "").replace(".", "")
        text = text.lower()
        for name in self.player_names:
            candidates = [name.lower(), name.lower().replace(" ", ""), name.lower().replace(" ", "_")]
            if any([candidate in text for candidate in candidates]):
                return name
        return ""

    def _is_test_player(self, player):
        if self.player_backends[player]["model"].find("fix")<0:
            return True
        else:
            return False


    def _is_true_code(self, text) -> bool:
        """
        Check whether the text is the true code
        """
        # Get the word enclosed by quote marks with regex
        pattern = r"\"(.+?)\""
        match = re.search(pattern, text)
        if match:
            return match.group(1).lower().replace(" ", "") == self.code.lower().replace(" ", "")
        else:
            # if no quote marks, check whether the last k words match the code
            words = text.split()
            if len(words) >= len(self.code.split()):
                guessed_term = "".join(words[-len(self.code.split()):]).lower().replace(".", "")
                return guessed_term == self.code.lower().replace(" ", "").replace(".", "")
            else:
                return False

    def _moderator_speak(self, text: str, visible_to: Union[str, List[str]] = "all"):
        """
        moderator say something
        """
        message = Message(agent_name="Moderator", content=text, turn=self._current_turn, visible_to=visible_to)
        self.message_pool.append_message(message)

    def get_rewards(self, undercover_win: bool) -> Dict[str, float]:
        """
        get rewards for each player
        """
        rewards = {}
        for name in self.player_names:
            # The winner gets 1, the loser gets 0
            rewards[name] = float((name == self.undercover_name) == undercover_win)

        return rewards

    def is_terminal(self) -> bool:
        """
        check if the conversation is over
        """
        # If the last message is the signal, then the conversation is over
        if self.message_pool.last_message.content.startswith(SIGNAL_END_OF_CONVERSATION):
            return True


    def parse_consistency(self, text, player, role):
        pattern_ind = r"I am (Player \d+)"
        pattern_role =  r"my role is ([ \w|-]+)"
        words_to_remove = r'\b(?:the|a|an)\b'

        flag = [0, 0]

        match = re.search(pattern_ind, text)
        if match:
            parse_player = match.group(1)
            if parse_player == player:
                flag[0] = 1

        match = re.search(pattern_role, text)
        if match:
            parse_role = match.group(1)
            parse_role = re.sub(words_to_remove, '', parse_role, flags=re.IGNORECASE)
            parse_role = parse_role.strip().lower()
            if parse_role == role:
                flag[1] = 1

        if sum(flag) == 2:
            # print("right identification")
            return 1
        else:
            # if flag[0] == 0:
            #     print("wrong player")
            # if flag[1] == 0:
            #     print("wrong role")
            return 0

    def parse_pgm(self, text):
        """
        convert text to change on chameleon.
        """
        pattern = r"Player \d+"
        pattern1 = r'I think Player \d+ is *[undercover|the undercover]'
        pattern2 = r'I think Player \d+ thinks Player \d+ is *[undercover|the undercover]'
        num_players = len(self.player_names)

        lines = text.split("\n")
        factor = np.zeros((num_players, num_players))
        changes = {"no change":0, "more suspicious":1, "less suspicious":-1}
        cur_player = self.player_names[self._next_player_idx]
        for line in lines:
            if line == "\n" :
                continue
            
            if re.search(pattern1, line):
                cur_view_player_idx = self.player_names.index(cur_player)
                cur_to_eval_player_idx = self.player_names.index(re.findall(pattern, re.search(pattern1, line).group(0))[0])
                factor[cur_view_player_idx][cur_to_eval_player_idx] = changes["more suspicious"]

            elif re.search(pattern2, line):
                players = re.findall(pattern, re.search(pattern2, line).group(0))
                assert len(players) == 2
                cur_view_player_idx = self.player_names.index(players[0])
                cur_to_eval_player_idx = self.player_names.index(players[1])
                factor[cur_view_player_idx][cur_to_eval_player_idx] = changes["more suspicious"]
            else:
                print("cannot parse the line: ", line)
        # print(factor)
        return factor
    
    def compute_pgm_metric(self, factors):
        # print(factors)
        num_players = len(self.player_names)
        gold = [0 if pi == self.undercover_idx else 1 for pi in range(num_players)]
        pgm_gold = [factors[pi][pi] for pi in range(num_players)]
        # compute match with gold
        gold_metric = [0,0,0]

        for pi,pgm in enumerate(pgm_gold):
            if np.argmax(pgm) == self.undercover_idx:
                gold_metric[pi] = 1
            

        # compute match with pgm gold
        gold_pgm_metric = [0,0,0]
        for pi in range(num_players):
            flag = [0,0,0]
            for pj in range(num_players):
                if pi==pj: 
                    continue
                if np.argmax(factors[pi][pj]) == np.argmax(pgm_gold[pj]):
                    flag[pj] = 1
                 
            if sum(flag) == 2:
                gold_pgm_metric[pi] = 1
        # print(gold_metric, gold_pgm_metric)
        return gold_metric, gold_pgm_metric

    def update_test_start(self, player_idx):
        if self.fix_partial:
            if not self.test_start:
                self.test_start = self._is_test_player(self.player_names[self._next_player_idx])



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
        

        # self.message_pool.print()
        # print(f"undercover: {self.undercover_name}, Code: {self.code}, Topic: {self.topic}")
        assert player_name == self.get_next_player(), f"Wrong player! It is {self.get_next_player()} turn."

        terminal= False
        request_msg = None
        rewards = 0
        if self._current_phase == "give clues":
            message = Message(agent_name=player_name, content=action, turn=self._current_turn, msg_type="clue")
            self.message_pool.append_message(message)

            # Update the counters
            self._current_turn += 1
            if self._next_player_idx < len(self.player_names) - 1:
                self._next_player_idx += 1
                self.update_test_start(self._next_player_idx)
                # print("test start==========>", self.test_start)
            else:
                self._next_player_idx = 0
                self._current_round += 1
                if self.add_pgm_metric:
                    self._current_phase = "metric_consistency"
                    request_msg = self.metric_templates["general"] + self.metric_templates["consistency"]
                else:

                    if self._current_round == self._max_round:
                        if self.only_pgm_metric:
                            terminal = True
                        else:
                            self._current_phase = "accuse"
                            self._moderator_speak("Now vote which of the other players (excluding yourself) is the undercover. "
                                            "You cannot vote for yourself.")
                            self._current_turn += 1
                    else:
                        self._current_phase = "give clues"
                        self._moderator_speak(f"Now we starting another round of giving clue, we still start from {self.player_names[0]}")
                        self._current_turn += 1

            timestep = TimeStep(observation=self.get_observation(),
                                reward=self.get_zero_rewards(),
                                request_msg=request_msg,
                                terminal=terminal)  # Return all the messages

        elif self._current_phase == "accuse":
            message = Message(agent_name=player_name, content=action, turn=self._current_turn,
                              visible_to=[player_name],msg_type="accuse")
            self.message_pool.append_message(message)
            vote = self._text2vote(action)
            self._vote_of_each_player[player_name] = vote
            if vote in self.player_names:
                self._players_votes[vote] += 1

            if self._next_player_idx < len(self.player_names) - 1:
                self._next_player_idx += 1
                rewards = self.get_zero_rewards()
                terminal = False
            else:
                accuse_correct, even_vote = True, False
                max_vote_player = max(self._players_votes, key=self._players_votes.get)
                # detach if other players has the same number of votes
                for name, vote in self._players_votes.items():
                    if name != max_vote_player and vote == self._players_votes[max_vote_player]:
                        accuse_correct, even_vote = False, True
                if max_vote_player != self.undercover_name:
                    accuse_correct = False

                if not accuse_correct:
                    if even_vote:
                        self._moderator_speak(f"There are even votes. The accusation does not stand. "
                                              f"{self.undercover_name} is the undercover. {self.undercover_name} won the game!")
                        self._win_group = 2
                    else:
                        self._moderator_speak(
                            f"The most-voted player is {max_vote_player}. The accusation is incorrect. "
                            f"{self.undercover_name} is the undercover. {self.undercover_name} won the game!"
                        )
                        self._win_group = 1
                    rewards = self.get_rewards(undercover_win=True)
                else:
                    self._moderator_speak(
                            f"The most-voted player is {max_vote_player}. The accusation is correct. "
                            f"{self.undercover_name} is the undercover. {self.undercover_name} won the game!"
                        )
                    self._win_group = 0
                    rewards = self.get_rewards(undercover_win=False)
                terminal = True

            timestep = TimeStep(observation=self.get_observation(), reward=rewards, terminal=terminal)
        

        elif self._current_phase == "metric_pgm":
            message = Message(agent_name=player_name, content=action, turn=self._current_turn, is_show=False, msg_type="metric_pgm")
            self.message_pool.append_message(message)
            self._current_turn += 1
            pgm_factor = self.parse_pgm(action)
            if self._metric_turn not in self.pgm_dict:
                self.pgm_dict[self._metric_turn] = {}
                self.pgm_metric_dict[self._metric_turn] = {} 

            self.pgm_dict[self._metric_turn][self.player_names[self._next_player_idx]] = pgm_factor

            if self._next_player_idx < len(self.player_names) - 1:
                self._next_player_idx += 1
                request_msg = self.metric_templates["general"] 
                other_players = [p for p in self.player_names if p != self.player_names[self._next_player_idx]]
                ques_id = 1
                request_msg += self.metric_templates["self_pgm"].format(idx=ques_id)
                for p in other_players:
                    ques_id += 1
                    request_msg += self.metric_templates["inter_pgm"].format(idx=ques_id, other_player=p)
            else:
                factors =[d[1] for d in sorted(self.pgm_dict[self._metric_turn].items(), key=lambda k:k[0])]
                gold_pgm_metric, inter_pgm_metric = self.compute_pgm_metric(factors)
                self.pgm_metric_dict[self._metric_turn] = {"gold": gold_pgm_metric, "inter": inter_pgm_metric}
                self._metric_turn += 1
                self._next_player_idx = 0
                if self._current_round < self._max_round:
                    self._moderator_speak(f"Now we starting another round of giving clue, we still start from {self.player_names[0]}")
                    self._current_turn += 1
                    self._current_phase="give clues"
                else:
                    if self.only_pgm_metric:
                        terminal = True
                    else:
                        self._current_phase = "accuse"
                        self._moderator_speak("Now vote which of the other players (excluding yourself) is the undercover. "
                                        "You cannot vote for yourself.")
                        self._current_turn += 1

            timestep = TimeStep(observation=self.get_observation(),
                                reward=self.get_zero_rewards(),
                                terminal=terminal,
                                request_msg=request_msg)

        elif self._current_phase == "metric_consistency":
            message = Message(agent_name=player_name, content=action, turn=self._current_turn, is_show=False, is_consistency=True, msg_type="metric_consistency")
            self.message_pool.append_message(message)
            self._current_turn += 1
            consistency_flag = self.parse_consistency(action, self.player_names[self._next_player_idx], "undercover" if self._next_player_idx == self.undercover_idx else "non-undercover")
            if self._metric_turn not in self.consisteny_dict:
                self.consisteny_dict[self._metric_turn] = {}
            self.consisteny_dict[self._metric_turn][self.player_names[self._next_player_idx]] = consistency_flag
            
            if self._next_player_idx < len(self.player_names) - 1:
                self._next_player_idx += 1
                request_msg = self.metric_templates["general"] + self.metric_templates["consistency"]
            else:
                self._current_phase = "metric_pgm"
                self._next_player_idx = 0
                request_msg = self.metric_templates["general"] 
                other_players = [p for p in self.player_names if p != self.player_names[self._next_player_idx]]
                ques_id = 1
                request_msg += self.metric_templates["self_pgm"].format(idx=ques_id)
                for p in other_players:
                    ques_id += 1
                    request_msg += self.metric_templates["inter_pgm"].format(idx=ques_id, other_player=p)
                    
            timestep = TimeStep(observation=self.get_observation(), reward=rewards, terminal=terminal, request_msg=request_msg)


        else:
            raise ValueError(f"Unknown phase: {self._current_phase}")
        
        # print(self._win_group)

        # Check if the player signals the end of the conversation
        if self.is_terminal():
            timestep.terminal = True
        

        return timestep
