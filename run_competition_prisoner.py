import time
import os
import sys
import json
import copy
from tqdm import tqdm
from chatarena.config import ArenaConfig
from chatarena.arena_new import Arena
from prompts.prisoner_prompt import topic_template, role_desc_pgm
# load previous game settings



class Competition_Prisoner():
    def __init__(self):
        self.win_count = {"win":0, "lose":0}

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


        for game_id in tqdm(range(0,num_of_game)):
            
            
            # 获取当前文件的绝对路径
            current_file = os.path.abspath(__file__)

            # 获取当前文件的目录
            current_dir = os.path.dirname(current_file)     
        
            result_path = os.path.join(current_dir, 'results/prisoner/setting/')
            
            final_path = result_path + str(game_id) +'.json'
            
            with open(final_path) as f:
                gs = json.load(f)
            fname = f"{save_dir}/{game_id}.json"
            arena_config = copy.deepcopy(arena_config_base)
            test_player_name = gs["test_player_name"]
            arena_config["environment"]["competition"]["test_player_name"] = test_player_name
            arena_config["environment"]["competition"]["random"] = False
            arena_config["environment"]["competition"]["topic_values"] = copy.deepcopy(gs["topic_values"])
            arena_config["environment"]["competition"]["topic"] = topic_template.format(
                cooperate=gs["topic_values"]["cooperate"], 
                defect=gs["topic_values"]["defect"], 
                one_defect=gs["topic_values"]["one_defect"],
                two_defect=gs["topic_values"]["two_defect"]
                )
            if test_player_model_name.find("-pgm")>=0:
                arena_config["environment"]["env_type"] = "prisoner_pgm"
            arena_config["environment"]["competition"]["test_player"]["model"] = test_player_model_name

            for player_config in arena_config["players"]:
                
                player_config["role"] = "test_player" if player_config["name"] == test_player_name else "non-test_player"
                if player_config["name"] == gs["test_player_name"]:
                    player_config["backend"]["model"] = arena_config["environment"]["competition"]["test_player"]["model"]
                else:
                    player_config["backend"]["model"] = arena_config["environment"]["competition"]["non-test_player"]["model"]
                if player_config["backend"]["model"].find("pgm")>=0:
                    player_config["role_desc"] = role_desc_pgm
                    player_config["backend"]["max_tokens"] = 256

                if player_config["backend"]["model"].startswith("llama"):
                    player_config["backend"]["backend_type"] = "llama"

            arena = Arena.from_config(arena_config)
            arena.run(num_steps=100)
            result = arena.environment.log_game(fname)
            self.win_count[result] += 1

        exit()

        #
