import time
import os
import sys
import json
import copy
from tqdm import tqdm
from chatarena.config import ArenaConfig
from chatarena.arena_new import Arena
from prompts.airportfee_prompt import role_desc_pgm, global_prompt



class Competition_Airportfee():
    def __init__(self):
        
        self.first_msg_template='''As Player {player}, representing Airline {airline}, I propose the following cost distribution:
        Airline A: {a}%
        Airline B: {b}%
        Airline C: {c}%\"
        '''
        self.win_count = {"agree":0, "fail":0}
        self.max_turns=5
        
        # 获取当前文件的绝对路径
        current_file = os.path.abspath(__file__)

        # 获取当前文件的目录
        current_dir = os.path.dirname(current_file)        
        
        self.setting_dir = os.path.join(current_dir, 'topics_release/airportfee/settings')
        
        #self.setting_dir = "topics_release/airportfee/settings"

    def run(self,config_dir, competition, path, test_player_model_name, num_of_game=21):

        config_dir=config_dir
        competition = competition
        save_root = path
        test_player_model_name = test_player_model_name
        postfix=""

        config_path = f"{config_dir}/{competition}.json"
        if not os.path.exists(config_path):
            print("Cannot find the config path:", config_path)
            exit()

        with open(config_path) as f:
            config = json.load(f)
        arena_config_base = ArenaConfig(config)


        save_dir = f"{save_root}/{test_player_model_name}_{competition}_vs_gpt4"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        player_names =["Player 1","Player 2","Player 3"]
        airlines = ["Airline A", "Airline B","Airline C"]
        for game_id in tqdm(range(0,num_of_game)):
            with open(f"{self.setting_dir}/{game_id}.json") as f:
                gs = json.load(f)

            fname = f"{save_dir}/{game_id}.json"
            if os.path.exists(fname):
                print("skip: ", fname)
                continue

            # print(gs["topic"]) 
            arena_config = copy.deepcopy(arena_config_base)
            test_player_name = gs["test_player_name"]
            arena_config["global_prompt"] = global_prompt.format(max_turns=self.max_turns)
            arena_config["environment"]["competition"]["test_player_name"] = test_player_name
            arena_config["environment"]["competition"]["random"] = False
            arena_config["environment"]["competition"]["topic"] = gs["topic"]
            arena_config["environment"]["competition"]["max_turns"] = self.max_turns
            if test_player_model_name.find("-pgm")>=0:
                arena_config["environment"]["env_type"] = "airport_fee_allocation_pgm"
            arena_config["environment"]["competition"]["test_player"]["model"] = test_player_model_name

            for player_config in arena_config["players"]:
                
                pr = gs["proposal"][player_config["name"]]
                pi = player_names.index(player_config["name"])
                player_config["first_msg"] = self.first_msg_template.format(player=player_config["name"], airline=airlines[pi], a=pr[0],b=pr[1],c=pr[2])


                player_config["role"] = "test_player" if player_config["name"] == test_player_name else "non-test_player"
                if player_config["name"] == gs["test_player_name"]:
                    player_config["backend"]["model"] = arena_config["environment"]["competition"]["test_player"]["model"]
                else:
                    player_config["backend"]["model"] = arena_config["environment"]["competition"]["non-test_player"]["model"]

                    
                if player_config["backend"]["model"].find("pgm")>=0:
                    pidx = player_names.index(test_player_name)
                    player_config["role_desc"] = role_desc_pgm.format(player=player_names[pidx], airline=airlines[pidx])
                    player_config["backend"]["max_tokens"] = 256

                if player_config["backend"]["model"].startswith("llama"):
                    player_config["backend"]["backend_type"] = "llama"

            arena = Arena.from_config(arena_config)
            arena.run(num_steps=100)
            result = arena.environment.log_game(fname)
            self.win_count[result] += 1

        exit()

#
