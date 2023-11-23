import numpy as np
import copy
# class PGM:
#     agent_name: str
#     is_chameleon: bool
#     pgm: Dict # it can be an image or a text
#     def __init__(self, player_name, player_names, is_chameleon):
#         self.player_num = len(player_names)
#         if is_chameleon:
#             pgm = {}
#         else:
#             pgm = {}
#     def init_pgm():
#         if self.is_chameleon:
#             pgm 
#         pass
#     def print(self):
#         print(f"{self.agent_name}'s PGM: ")
#         for player_name in self.pgm:
#             print(f"{player_name}->{self.pgm[player_name]}")
        

class PGM_List:
    def __init__(self, player_names, chameleon_name):
        self.player_names = player_names
        self.player_num = len(self.player_names)
        self.chameleon_name = chameleon_name
        self.chameleon_idx = self.player_names.index(chameleon_name)
        self._pgm_list = {}
        self.init_pgm()


    def init_pgm(self):
        
        for sub_idx, sub_player_name in enumerate(self.player_names):
            if sub_player_name == self.chameleon_name:
                is_chameleon = True
            else:
                is_chameleon = False
            cur_player_pgm = {}
            for obj_player_name in self.player_names:
                if obj_player_name ==  sub_player_name:
                    if is_chameleon:
                        cur_player_pgm[obj_player_name] = np.zeros(len(self.player_names))
                        cur_player_pgm[obj_player_name][sub_idx] = 1.0
                    else:
                        cur_player_pgm[obj_player_name] = 1/(len(self.player_names)-1)*np.ones(len(self.player_names))
                        cur_player_pgm[obj_player_name][sub_idx] = 0.0
                else:
                    cur_player_pgm[obj_player_name] = 1/len(self.player_names)*np.ones(len(self.player_names))
            self._pgm_list[sub_player_name] =  copy.deepcopy(cur_player_pgm)
        
            
    # def reset(self):
    #     pass
        
    
    def update(self, player_name, pgm):
        self._pgm_list[player_name] = pgm