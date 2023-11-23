import time
import os
import json
import copy
from tqdm import tqdm
from chatarena.config import ArenaConfig
from chatarena.arena_new import Arena
import sys

# load previous game settings



class Competition_Chameleon():
    def __init__(self):
        
        
        # 获取当前文件的绝对路径
        current_file = os.path.abspath(__file__)

        # 获取当前文件的目录
        current_dir = os.path.dirname(current_file)
        
        self.setting_dir = os.path.join(current_dir, 'topics_release/chameleon/settings')
        
        self.win_count = {"chameleon":0, "non-chameleon":0}
    def run(self,config_dir, competition, path, test_player_model_name, num_of_game=20):
        
        # if len(sys.argv) > 1:
        #     if len(sys.argv) != 4:
        #         print("require 4 arguments!")
        #     else:
        #         config_dir=sys.argv[1]
        #         competition=sys.argv[2]
        #         save_root=sys.argv[3]
        #         test_player_model_name =sys.argv[4]
        #         postfix=""

        # else:
        #     config_dir="config_release"
        #     competition = "competition_as_chameleon"
        #     save_root = "results/chameleon"
        #     test_player_model_name = "gpt-3.5-turbo"
        #     postfix="-test"
            
        config_dir=config_dir
        competition = competition
        save_root = path
        test_player_model_name = test_player_model_name
        postfix=""
        #test_player_model_name = "gpt-4-turbo"


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


        for game_id in tqdm(range(0,num_of_game)):
            gs_name = f"{self.setting_dir}/{game_id}.json"
            if not os.path.exists(gs_name):
                print("setting not exist", gs_name)
                continue
            arena_config = copy.deepcopy(arena_config_base)
            fname = f"{save_dir}/{game_id}{postfix}.json"
            if os.path.exists(fname):
                game_id += 1
                continue
           
            with open(gs_name) as f:        
                
                d = json.load(f)
                if "game_setting" in d:
                    gs = d["game_setting"]
                else:
                    gs = d
                
                chameleon_name = gs["chameleon_name"]
                arena_config["environment"]["competition"]["random"] = False
                arena_config["environment"]["competition"]["topic"] = gs["topic"]
                arena_config["environment"]["competition"]["code"] = gs["code"]
                arena_config["environment"]["competition"]["chameleon_name"] = gs["chameleon_name"]


                if test_player_model_name.find("-pgm")>=0:
                    arena_config["environment"]["env_type"] = "chameleon_competition_pgm"
                if "non_chameleon" in competition:
                    arena_config["environment"]["competition"]["non-chameleon"]["model"] = test_player_model_name
                elif "chameleon" in competition:
                    arena_config["environment"]["competition"]["chameleon"]["model"] = test_player_model_name
                else:
                    print("The competition name is not legal", competition)

                for player_config in arena_config["players"]:
                    if "clue" not in d:
                        player_config["clue"] = None
                    else:
                        player_config["clue"] = d["clue"][player_config["name"]]
                    # if "game_path" in gs:
                    #     with open(gs["game_path"]) as f:
                    #         hist = json.load(f)["history"]
                    #     for msg in hist:
                    #         if msg["agent_name"] == player_config["name"]:
                    #             player_config["clue"] = msg["content"]
                    #             break

                    player_config["role"] = "chameleon" if player_config["name"] == chameleon_name else "non-chameleon"
                    if player_config["name"] == gs["chameleon_name"]:
                        player_config["backend"]["model"] = arena_config["environment"]["competition"]["chameleon"]["model"]
                    else:
                        player_config["backend"]["model"] = arena_config["environment"]["competition"]["non-chameleon"]["model"]
                    if player_config["backend"]["model"].startswith("llama"):
                        player_config["backend"]["backend_type"] = "llama"
                        
            arena = Arena.from_config(arena_config)

            arena.run(num_steps=500)
            win_group = arena.environment.get_win_group()
            self.win_count[win_group] += 1
            arena.environment.log_game(fname)
