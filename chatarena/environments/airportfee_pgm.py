from typing import List, Dict, Union
import random
import openai
import re
import json
import os

from .base import Environment, TimeStep
from ..message import Message, MessagePool
from ..agent import SIGNAL_END_OF_CONVERSATION
from ..config import EnvironmentConfig
from prompts.airportfee_prompt import *
DEFAULT_TOPIC = """

Fixed Airport Fee: $1,000,000

Airline Usage Frequency Data:

Airline A:
Number of Flights: 100/month
Number of Passengers: 10,000/month
Average Flight Duration: 2 hours
Flight Size: Primarily medium aircraft

Airline B:
Number of Flights: 50/month
Number of Passengers: 7,500/month
Average Flight Duration: 1.5 hours
Flight Size: Primarily small aircraft

Airline C:
Number of Flights: 150/month
Number of Passengers: 12,500/month
Average Flight Duration: 3 hours
Flight Size: Primarily large aircraft

"""



class Airport_Fee_Allocation_PGM(Environment):
    type_name = "airport_fee_allocation_pgm"

    def __init__(self, player_names: List[str], topic_codes: Dict[str, List[str]] = None, competition=None, **kwargs):
        super().__init__(player_names=player_names, topic_codes=topic_codes, **kwargs)


        # The "state" of the environment is maintained by the message pool
        self.message_pool = MessagePool()

        # Randomly sample a topic, code and chameleon player
        self.topic = DEFAULT_TOPIC
        self.chameleon_name = None
        self.competition = competition
        self.max_turns = competition["max_turns"]
        self.nego_turn = 0
        self.negotiate_template=negotiate_template
        self.pgm_prompt = pgm
        self.pgm_decision = pgm_decision
        
        # Game states
        self._current_turn = 0
        self._next_player_idx = 0
        self._current_phase = "negotiate"  # "negotiate", "vote"
        self._players_votes = None
        self._initialized = False
        
        self.player_models = []
        self.player_backends={}
        self.single_pgm = True

        self._single_history=False
        self.result = None
        self.test_start=True

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
                "topic": self.topic, 
                "test_player_name": self.test_player_name,
                "player_backends": self.player_backends, 
                "history": message_rows,
                "nego_turn": self.nego_turn,
                "result": self.result,
                "proposal": self.proposal,
                "vote": self._players_votes,
                }, f, indent=4)
        
        return self.result
        

    def reset(self):
        """
        sample topic, code and chameleon code
        """

        self._current_turn = 0
        self._next_player_idx = 0
        self._current_phase = "negotiate"
        self.test_player_name = self.competition["test_player_name"]
        self.topic = self.competition["topic"]
        for p in self.player_names:
            if p == self.test_player_name:
                self.player_backends[p] = self.competition["test_player"]["model"]
            else:
                self.player_backends[p] = self.competition["non-test_player"]["model"]
        self.player_models = list(self.player_backends.values())
        
        self.proposal = {"Player 1":[], "Player 2":[], "Player 3":[]}

        self.message_pool.reset()

        self._moderator_speak(f"Now the game starts! The background is: {self.topic}")

        self._moderator_speak(
            f"Now everyone propose the cost distribution."
            f"We will start with {self.player_names[0]}.")
        request_msg = self.negotiate_template
        self._current_turn = 1

        self._players_votes = {name: 0 for name in self.player_names}

        self._initialized = True



        init_timestep = TimeStep(observation=self.get_observation(),
                                 reward=self.get_zero_rewards(),
                                 request_msg=request_msg,
                                 terminal=False)

        return init_timestep

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

    def print(self):
        self.message_pool.print()

    # def get_observation(self, player_name=None) -> List[Message]:
    #     """
    #     get observation for the player
    #     """
    #     if player_name is None:
    #         return self.message_pool.get_all_messages()
    #     else:
    #         return self.message_pool.get_visible_messages(player_name, turn=self._current_turn)

    def get_observation(self, player_name=None) -> List[Message]:
        """
        get observation for the player
        """
        if player_name is None:
            return self.message_pool.get_all_messages()
        else:
            messages = self.message_pool.get_visible_messages(player_name, turn=self._current_turn)
            if self.single_pgm and self._current_phase=="negotiate":
                pgm_messages = self.message_pool.get_pgm_messages(player_name, turn=self._current_turn)
                if len(pgm_messages)>0:
                    messages.append(pgm_messages[-1])
            return messages

    def _text2vote(self, text) -> str:
        """
        convert text to vote, return a player's name
        """
        pattern = r"Player \d+"
        match = re.search(pattern, text)
        if match:
            return match.group(0)
        else:
            print("cannot parse the text:", text)
            print("use gpt3.5 to parse")
            prompt= text + "According to the above text, tell me which player is voted, please reply only with Player xx"
            response = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                        messages=[{'role':'user','content':prompt}],                                    
                                        temperature = 0,
                                        n=3,
                                       max_tokens=5)

            user = response['choices'][0]['message']['content']
            match = re.search(pattern, user)
            if match is None:
                return "Player 1"
            else:
                return match.group(0)

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

    def check_agreement(self, votes):
        vote_values = list(votes.values())
        vote_of_first_player = vote_values[0]
        proposal_vote_by_first_player = list(self.proposal[vote_of_first_player].values())

        for idx, vote in enumerate(vote_values):
            if idx == 0:
                continue
            if vote != vote_of_first_player:
                if list(self.proposal[vote].values()) != proposal_vote_by_first_player:                    
                    return False
        return True

    def parse_proposal(self, text):
        costs = {"A":None,"B":None,"C":None}
        # pattern = r"Airline (\S+): \$(\d+,*\d*)"
        pattern = r"Airline (\S+): (\d.+)%"
        # pattern = r"Airline (\S+): \$(\d+,*\d*|\d+\%)"
        for line in text.split("\n"):
            match = re.search(pattern, line)
            # print(match)
            if match:
                airline_name = match.group(1)
                money = match.group(2)
                costs[airline_name] = money
            # for pattern in patterns:

            #     match = re.search(pattern, line)
            #     if match:
            #         airline_name = match.group(1)
            #         money = match.group(2)
            #         costs[airline_name] = money
                
        # print(costs)
        return costs
    

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
        request_msg=None


        assert player_name == self.get_next_player(), f"Wrong player! It is {self.get_next_player()} turn."
        if self._current_phase == "negotiate":
            message = Message(agent_name=player_name, content=action, turn=self._current_turn)
            self.message_pool.append_message(message)
            self._current_turn += 1
            self.proposal[self.player_names[self._next_player_idx]] = self.parse_proposal(action)

            if self._next_player_idx < len(self.player_names) - 1:
                self._next_player_idx += 1
                request_msg = self.negotiate_template
                
            else:
                self._next_player_idx = 0
                self._current_phase = "vote"
                self._moderator_speak("Now vote which proposal is the suitable one you agree with. You must respond with the template \"I vote for Player xx's proposal\".(do not include explanantions)")
                self._current_turn += 1
                self.nego_turn += 1


            timestep = TimeStep(observation=self.get_observation(),
                                reward=self.get_zero_rewards(),
                                request_msg=request_msg,
                                terminal=terminal)  # Return all the messages
        elif self._current_phase == "vote":
            message = Message(agent_name=player_name, content=action, turn=self._current_turn,
                              visible_to='all')
            self._current_turn += 1
            self.message_pool.append_message(message)
            # analyse the vote result and record
            vote = self._text2vote(action)
            self._players_votes[self.player_names[self._next_player_idx]] = vote

            if self._next_player_idx < len(self.player_names) - 1:
                self._next_player_idx += 1
            else:
                # print(self._players_votes)
                # print(self.proposal)
                agree = self.check_agreement(self._players_votes)
            
                if agree:
                    self._moderator_speak(f"You all already agree the same proposal ")
                    self._current_turn += 1
                    self.result = "agree"
                    terminal = True
                else:
                    # self._moderator_speak(f"You all haven't achieve the consistent proposal, please continue to negotiate")
                    if self.nego_turn >=self.max_turns:
                        terminal=True
                        self._moderator_speak(f"You have negotiated for {self.max_turns} turn, no consistency achieved, negotiation failed.")
                        self._current_turn += 1
                        self.result = "fail"
                    else:
                        self._moderator_speak(f"At {self.nego_turn}'s round, you all haven't achieve the consistency. Please continue a new round of negotiation. ")
                        self._current_turn += 1
                        self._current_phase = "pgm"
                        self._next_player_idx = 0
                        self._next_player_idx = self.find_next_pgm_player(self._next_player_idx)
                        if self._next_player_idx is not None:
                            player_name = self.player_names[self._next_player_idx] 
                            oth_players = [p for p in self.player_names if p!= player_name]
                            request_msg = self.pgm_prompt.format(player_name=player_name, oth_player1=oth_players[0], oth_player2=oth_players[1])
            timestep = TimeStep(observation=self.get_observation(), reward=self.get_zero_rewards(), request_msg=request_msg, terminal=terminal)

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
                self._current_phase = "negotiate"
                if self.is_pgm_player(self._next_player_idx):
                    request_msg = self.pgm_decision 
                else:
                    request_msg = self.negotiate_template


            timestep = TimeStep(observation=self.get_observation(),
                                reward=self.get_zero_rewards(),
                                request_msg=request_msg,
                                terminal=terminal)  # Return all the messages


        else:
            raise ValueError(f"Unknown phase: {self._current_phase}")

        # Check if the player signals the end of the conversation
        if self.is_terminal():
            timestep.terminal = True

        return timestep