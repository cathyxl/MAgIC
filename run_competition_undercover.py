import time
import os
import json
import copy
import sys
from tqdm import tqdm
from chatarena.arena_new import Arena
from chatarena.config import ArenaConfig


class Competition_Under_Cover():
    def __init__(self):
        # load previous game settings
        self.random_setting = False
        self.win_count = {"undercover":0, "non-undercover":0}
        
        
        # 获取当前文件的绝对路径
        current_file = os.path.abspath(__file__)

        # 获取当前文件的目录
        current_dir = os.path.dirname(current_file)        
        
        self.setting_dir = os.path.join(current_dir, 'topics_release/undercover/settings')
        
        
    def run(self,config_dir, competition, path, test_player_model_name, num_of_game=20):
        
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

        for game_id in tqdm(range(0,num_of_game)):
            gs_name = f"{self.setting_dir}/{game_id}.json"
            if not os.path.exists(gs_name):
                print(f"cannot find the setting: {gs_name}")
                continue
            arena_config = copy.deepcopy(arena_config_base)
            fname = f"{save_dir}/{game_id}{postfix}.json"
            # if os.path.exists(fname):
            #     print("skip", fname)
            #     game_id += 1
            #     continue
            with open(gs_name) as f:
                d = json.load(f)
                gs = d["game_setting"]
                undercover_name = gs["undercover_name"]
                arena_config["environment"]["competition"]["random"] = False
                arena_config["environment"]["competition"]["undercover_code"] = gs["undercover_code"]
                arena_config["environment"]["competition"]["non_undercover_code"] = gs["non_undercover_code"]
                arena_config["environment"]["competition"]["undercover_name"] = gs["undercover_name"]

                if test_player_model_name.find("-pgm")>=0:
                    arena_config["environment"]["env_type"] = "undercover_competition_pgm"
                if "non_undercover" in competition:
                    arena_config["environment"]["competition"]["non-undercover"]["model"] = test_player_model_name
                elif "undercover" in competition:
                    arena_config["environment"]["competition"]["undercover"]["model"] = test_player_model_name
                else:
                    print("The competition name is not legal", competition)

                for player_config in arena_config["players"]:
                    if "clues" in d:
                        player_config["clues"] = d["clues"][player_config["name"]]
                    # elif "fname" in d:
                    #     game_path = "%s/%s" % (fix_dir, d["fname"])
                    #     clues = []
                    #     with open(game_path) as f:
                    #         hist = json.load(f)["history"]
                    #     for msg in hist:
                    #         if msg["agent_name"] == player_config["name"] and msg["visible_to"] == "all":
                    #             clues.append(msg["content"])
                    #     player_config["clues"] = clues         
                    else:
                        player_config["clues"] = None     

                    player_config["role"] = "undercover" if player_config["name"] == undercover_name else "non-undercover"
                    if player_config["name"] == undercover_name:
                        player_config["backend"]["model"] = arena_config["environment"]["competition"]["undercover"]["model"]
                    else:
                        player_config["backend"]["model"] = arena_config["environment"]["competition"]["non-undercover"]["model"]

                    if player_config["backend"]["model"].startswith("llama"):
                        #print("change llama: ", player_config["name"], player_config["backend"]["model"] )
                        player_config["backend"]["backend_type"] = "llama"

            

            arena = Arena.from_config(arena_config)
            arena.run(num_steps=50)
            win_group = arena.environment.get_win_group()
            self.win_count[win_group] += 1
            
            arena.environment.log_game(fname)



