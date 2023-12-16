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
from prompts.chameleon_prompt import *


DEFAULT_TOPIC_CODES = {
    "Fruits": [
        "Apple",
        "Banana",
        "Orange",
        "Grape",
        "Strawberry",
        "Pineapple",
        "Mango",
        "Watermelon",
    ],
    "Animals": [
        "Lion",
        "Elephant",
        "Giraffe",
        "Monkey",
        "Zebra",
        "Tiger",
        "Bear",
        "Kangaroo",
    ],
    "Sports": [
        "Soccer",
        "Basketball",
        "Tennis",
        "Baseball",
        "Swimming",
        "Cycling",
        "Volleyball",
        "Golf",
    ],
    "Countries": [
        "United States",
        "Canada",
        "Brazil",
        "United Kingdom",
        "France",
        "Germany",
        "Japan",
        "Australia",
    ],
}


class Chameleon_Competition(Environment):
    type_name = "chameleon_competition"

    def __init__(self, player_names: List[str], topic_codes: Dict[str, List[str]] = None, competition=None, **kwargs):
        super().__init__(player_names=player_names, topic_codes=topic_codes, **kwargs)

        if topic_codes is None:
            topic_codes = DEFAULT_TOPIC_CODES
        self.topic_codes = topic_codes

        # The "state" of the environment is maintained by the message pool
        self.message_pool = MessagePool()

        # Randomly sample a topic, code and chameleon player
        self.topic = None
        self.code = None
        self.chameleon_name = None
        self.non_chameleon_names = None
        self.metric_pgm_template = {"chameleon": metric_pgm_chameleon_wformat, "non-chameleon": metric_pgm_non_chameleon_wformat}
        self.metric_consistency_template = metric_consistency

        # Game states
        self._current_turn = 0
        self._next_player_idx = 0
        self._current_phase = "give clues"  # "give clues", "accuse", "guess"
        self._players_votes = None
        self._initialized = False
        self._win_group = -1
        self.player_backends = {}
        self.competition = competition
        self.game_setting = None
        self.rewrite_game_setting = False


        self.test_start = False

        self.fix_partial = True if "fix_partial" not in competition else competition["fix_partial"]  # Partially fix the response
        self.add_pgm_metric = True  if "add_pgm_metric" not in competition else competition["add_pgm_metric"]  # Do pgm metric at the same time.
        self.only_pgm_metric = False if "only_pgm_metric" not in competition else competition["only_pgm_metric"]  # Only do pgm metric, no clue, no pgm, no
        
        if self.add_pgm_metric and self.only_pgm_metric: # we fix all the input when calculate pgm metric
            self.fix_partial = False

        self.reset()  # To initialize the game (select topic, code, chameleon)

    def get_next_player(self) -> str:
        """
        get the next player
        """
        if self._current_phase != "guess":
            return self.player_names[self._next_player_idx]
        else:
            return self.chameleon_name
    
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
            }
            message_rows.append(message_row)
        if not self.only_pgm_metric:
            assert self._win_group >= 0
            result = "non-chameleon" if self._win_group == 0 else "chameleon"
        else:
            result = None
    
        if source_path:
            with open(source_path) as f:
                d = json.load(f)
            result = d["result"]
            self._win_group  = d["win_flag"]
            self._vote_for_each_player = d["player_votes"]

        with open(path, "w") as f:
            json.dump({
                "chameleon": self.chameleon_name, 
                "game_setting": self.game_setting,
                "player_backends": self.player_backends, 
                "history": message_rows,
                "win_flag": self._win_group,
                "player_votes": self._vote_for_each_player,
                "result": result,
                "consistency_metric": self.consisteny_dict,
                "pgm_metric": self.pgm_metric_dict,
                }, 
                f, indent=4)

        

    def get_win_group(self):
        assert self._win_group >= 0
        return "non-chameleon" if self._win_group == 0 else "chameleon"

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
        sample topic, code and chameleon code
        """
        self.game_path = None 
         if self.competition["random"]:
            self.topic = random.choice(list(self.topic_codes.keys()))
            self.code = random.choice(self.topic_codes[self.topic])
            self.chameleon_name = random.choice(self.player_names)
        else:
            self.topic = self.competition["topic"]
            self.code = self.competition["code"]
            self.chameleon_name = self.competition["chameleon_name"]

        self.player_backends = {}
        if self.competition:
            for player_name in self.player_names:
                if player_name == self.chameleon_name:
                    self.player_backends[player_name] = self.competition["chameleon"]
                else:
                    self.player_backends[player_name] = self.competition["non-chameleon"]

       
        self.game_setting = {"topic": self.topic, "code": self.code, "chameleon_name": self.chameleon_name}
        self.non_chameleon_names = [name for name in self.player_names if name != self.chameleon_name]
        self.chameleon_idx = self.player_names.index(self.chameleon_name)

        self._current_turn = 0
        self._next_player_idx = 0
        self._next_clue_player_idx = 0
        
        self._metric_turn = 0
        self.consisteny_dict = {}
        self.pgm_metric_dict = {}
        self.pgm_dict = {}

        self.message_pool.reset()

        self._moderator_speak(f"Now the game starts! The topic is: {self.topic}")
        self._current_turn += 1
        self._moderator_speak(f"You are not chameleon. The word is: {self.code}",
                              visible_to=self.non_chameleon_names)
        self._current_turn += 1
        self._moderator_speak(f"You are the chameleon!", visible_to=self.chameleon_name)
        self._current_turn += 1
        
        self.update_test_start(0)

        if self.add_pgm_metric:
            self._current_phase = "metric_consistency"  # "give clues", "accuse", "guess"
            request_msg  = self.metric_consistency_template
        else:
            self._current_phase = "give clues"
            self._moderator_speak(
                f"Now everyone gives one clue (but never include the secret word). "
                f"You cannot repeat what others has said. We will start with {self.player_names[0]}.")
            self._current_turn += 1
            request_msg = None

        self._players_votes = {name: 0 for name in self.player_names}
        self._win_group = -1 # 0, none chameleon; 1(right vote, guessed right),2(wrong vote),3(even vote)
        self._vote_for_each_player = {name: None for name in self.player_names}
       
        self._initialized = True

        
        init_timestep = TimeStep(observation=self.get_observation(),
                                 reward=self.get_zero_rewards(),
                                 request_msg=request_msg,
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


    def _is_test_player(self, player):
        if self.player_backends[player]["model"].find("fix")<0:
            return True
        else:
            return False

    def update_test_start(self, player_idx):
        if self.fix_partial:
            if not self.test_start:
                self.test_start = self._is_test_player(self.player_names[self._next_player_idx])
        

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
            #     # print("wrong player")
            # if flag[1] == 0:
            #     # print("wrong role")
            return 0

    def parse_pgm(self, text):
        """
        convert text to change on chameleon.
        """
        pattern = r'Player \d+'
        lines = text.split("\n")
        num_players = len(self.player_names)
        factor = np.zeros((num_players, num_players))
        changes = {"no change":0, "more suspicious":1, "less suspicious":-1}
        cur_player = self.player_names[self._next_player_idx]
        for line in lines:
            if line.startswith("Now I guess the secret word is "):
                guess_code = re.findall(r'"([^"]*)"', line)[0]
                if guess_code.lower() == self.code.lower():
                    self.is_leak = True
            
            if line.startswith("As Player"):
                cur_player = re.search(pattern, line).group(0)
            if line.startswith("I think now Player"):
                if re.search(pattern, line) is not None:
                    cur_player = re.search(pattern, line).group(0)
            if line.startswith("Player"):
                try:
                    cur_to_eval_player = re.search(pattern, line).group(0)
                    cur_eval = 0
                    for c in changes:
                        if c in line:
                            cur_eval = changes[c]
                except:
                    print("no change text detected")
                cur_player_idx = self.player_names.index(cur_player)
                # print(cur_player, cur_to_eval_player, cur_eval)
                cur_to_eval_player_idx = self.player_names.index(cur_to_eval_player)
                factor[cur_player_idx][cur_to_eval_player_idx] = cur_eval
        return factor

    def compute_pgm_metric(self, factors):
        # print(factors)
        num_players = len(self.player_names)
        gold = [0 if pi == self.chameleon_idx else 1 for pi in range(num_players)]
        pgm_gold = [factors[pi][pi] for pi in range(num_players)]
        # compute match with gold
        gold_metric = [0,0,0]

        for pi,pgm in enumerate(pgm_gold):
            if np.argmax(pgm) == self.chameleon_idx:
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
        request_msg = None
        terminal= False
        rewards= 0
        assert player_name == self.get_next_player(), f"Wrong player! It is {self.get_next_player()} turn."
        if self._current_phase == "give clues":
            message = Message(agent_name=player_name, content=action, turn=self._current_turn, msg_type="clue")
            self.message_pool.append_message(message)
            self._current_turn += 1
            if self.add_pgm_metric:
                self._current_phase = "metric_pgm"
                self._next_clue_player_idx = self._next_player_idx + 1
                self._next_player_idx = 0
                request_msg = self.metric_pgm_template["chameleon"] if self._next_player_idx == self.chameleon_idx else self.metric_pgm_template["non-chameleon"]
                request_msg = request_msg.format(player=self.player_names[self._next_player_idx])
            else:
                if self._next_player_idx < len(self.player_names) -1:
                    self._next_player_idx += 1
                    self.update_test_start(self._next_player_idx)
                else:
                    if self.only_pgm_metric:
                        terminal = True
                    else:
                        self._current_phase = "accuse"
                        self._next_player_idx = 0
                        self._moderator_speak("Now vote which of the other players (excluding yourself) is the chameleon. "
                                            "You cannot vote for yourself. You must use the template \"I vote for Player xx.\"")
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
            self._vote_for_each_player[player_name] = vote
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
                if max_vote_player != self.chameleon_name:
                    accuse_correct = False
                if not accuse_correct:
                    if even_vote:
                        self._moderator_speak(f"There are even votes. The accusation does not stand. "
                                              f"{self.chameleon_name} is the chameleon. {self.chameleon_name} won the game!")
                        self._win_group = 3
                    else:
                        self._moderator_speak(
                            f"The most-voted player is {max_vote_player}. The accusation is incorrect. "
                            f"{self.chameleon_name} is the chameleon. {self.chameleon_name} won the game!"
                        )
                        self._win_group = 2
                    rewards = self.get_rewards(chameleon_win=True)
                    terminal = True
                else:
                    self._moderator_speak(f"The accusation is correct! {self.chameleon_name} is the chameleon! "
                                          f"Now {self.chameleon_name} can guess the secret code. "
                                          "You should say: I guess the code is \"...\"")
                    
                    self._current_phase = "guess"
                    rewards = self.get_zero_rewards()
                    terminal = False
                self._current_turn += 1

            timestep = TimeStep(observation=self.get_observation(), reward=rewards, terminal=terminal)

        elif self._current_phase == "guess":
            message = Message(agent_name=player_name, content=action, turn=self._current_turn,
                              visible_to=player_name)
            self.message_pool.append_message(message)
            if self._is_true_code(action):
                self._moderator_speak(f"{player_name} guessed the code correctly! The secret word is {self.code}. "
                                      f"{self.chameleon_name} won!")
                self._win_group = 1
                rewards = self.get_rewards(chameleon_win=True)
            else:
                self._moderator_speak(f"{player_name} guessed the code wrong! The secret word is {self.code}. "
                                      f"{self.non_chameleon_names} won!")
                self._win_group = 0
                rewards = self.get_rewards(chameleon_win=False)

            timestep = TimeStep(observation=self.get_observation(),
                                reward=rewards,
                                terminal=True)

        elif self._current_phase == "metric_consistency":
            message = Message(agent_name=player_name, content=action, turn=self._current_turn, is_show=False, is_consistency=True,msg_type="metric_consistency")
            self.message_pool.append_message(message)
            self._current_turn += 1

            consistency_flag = self.parse_consistency(action, self.player_names[self._next_player_idx], "chameleon" if self._next_player_idx == self.chameleon_idx else "non-chameleon")
            if self._metric_turn not in self.consisteny_dict:
                self.consisteny_dict[self._metric_turn] = {}
            self.consisteny_dict[self._metric_turn][self.player_names[self._next_player_idx]] = consistency_flag
            
            if self._next_player_idx < len(self.player_names) - 1:
                self._next_player_idx += 1
                request_msg = self.metric_consistency_template
            else:
                if self._next_clue_player_idx == 0:
                    self._moderator_speak(
                        f"Now everyone gives one clue (but never include the secret word). "
                        f"You cannot repeat what others has said. We will start with {self.player_names[0]}.")
                    self._current_turn += 1
                
                self._next_player_idx = self._next_clue_player_idx
                self.update_test_start(self._next_player_idx)
                self._current_phase = "give clues"

            timestep = TimeStep(observation=self.get_observation(), reward=rewards, terminal=terminal, request_msg=request_msg)

        elif self._current_phase == "metric_pgm":
            terminal = False
            message = Message(agent_name=player_name, content=action, turn=self._current_turn, is_show=False, is_pgm=True, msg_type="metric_pgm")
            self.message_pool.append_message(message)
            self._current_turn += 1
            pgm_factor = self.parse_pgm(action)
            
            if self._metric_turn not in self.pgm_dict:
                self.pgm_dict[self._metric_turn] = {}
                self.pgm_metric_dict[self._metric_turn] = {} 

            self.pgm_dict[self._metric_turn][self.player_names[self._next_player_idx]] = pgm_factor
            
            if self._next_player_idx < len(self.player_names) - 1:
                self._next_player_idx += 1
                request_msg = self.metric_pgm_template["chameleon"] if self._next_player_idx == self.chameleon_idx else self.metric_pgm_template["non-chameleon"] 
                request_msg = request_msg.format(player=self.player_names[self._next_player_idx])
            else:
                factors =[d[1] for d in sorted(self.pgm_dict[self._metric_turn].items(), key=lambda k:k[0])]
                gold_pgm_metric, inter_pgm_metric = self.compute_pgm_metric(factors)
                self.pgm_metric_dict[self._metric_turn] = {"gold": gold_pgm_metric, "inter": inter_pgm_metric}
                if self._next_clue_player_idx >= len(self.player_names):
                    self._next_player_idx = 0
                    if self.only_pgm_metric and self.add_pgm_metric:
                        terminal = True
                    else:
                        self._current_phase = "accuse"
                        self._moderator_speak("Now vote which of the other players (excluding yourself) is the chameleon. "
                                            "You cannot vote for yourself. You must use the template \"I vote for Player xx.\"")
                        self._current_turn += 1
                else:
                    self._metric_turn += 1
                    self._next_player_idx = 0
                    self._current_phase = "metric_consistency"
                    request_msg = self.metric_consistency_template
            timestep = TimeStep(observation=self.get_observation(), reward=rewards, terminal=terminal, request_msg=request_msg)

        else:
            raise ValueError(f"Unknown phase: {self._current_phase}")
        

        # Check if the player signals the end of the conversation
        if self.is_terminal():
            timestep.terminal = True
        

        return timestep
