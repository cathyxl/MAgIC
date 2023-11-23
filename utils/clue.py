import numpy as np
import random
class Clue:
    def __init__(self, clue_text, target_player_tuples, is_chameleon, player_names, player_name, clue_turn):
        self.player_idx = player_names.index(player_name)
        self.player_name = player_name
        self.num_players = len(player_names)
        self.is_chameleon = is_chameleon
        self.player_names = player_names
        self.clue_text = clue_text
        # self.target = np.zeros((self.num_players,))
        self.target = target_player_tuples

        self.clue_turn = clue_turn
        self._good_clue = False
        self._is_leak = False
        self._realized_target = None
        self._success_reason_templs = [
            "this clue sucessfully <ACT> the suspicousness of <OBJ> from <SUB>'s eyes",
            ]
        self._fail_reason_templs = [
            "this clue failed to <ACT> the suspicousness of <OBJ> from <SUB>'s eyes",
            ]
        
        
    def is_good_clue(self, factors, is_leak):
        """
        factors:[[0,1,1],[0,..],...], the current view of all the players
        at least one tuple in the target should be fulfilled to be a good clue.
        """
        # calculate the relative change of target player pair
        is_good_list = []
        for tup in self.target:
            sub, obj, val = tup
            if val == -1:
                change = factors[sub][obj]- max(factors[sub])
                is_good_list.append(change < 0)
            elif val == 1:
                change = factors[sub][obj]- min(factors[sub])
                is_good_list.append(change > 0)
            else:
                print(val, "is not supported")
        self._realized_target = is_good_list
        self._good_clue = sum(is_good_list) > 0

        # if the clue leak the secret code, also not good 
        if not self.is_chameleon and is_leak:
            self._good_clue = False
        self._is_leak = is_leak
        

        return self._good_clue

    

    def _to_text(self):

        clue_eval = "good clue" if self._good_clue else "bad clue"
        s = f"{self. player_name}: {self.clue_text}, [{clue_eval}]"

        reason_eval = ", because "
        if self._good_clue:
            is_first = True
            for tup, real in zip(self.target, self._realized_target):
                if real:
                    templ = random.choice(self._success_reason_templs)
                    if is_first:
                        cur_reason = self._target_to_text(tup, templ)
                        is_first = False
                    else:
                        cur_reason = " and " + self._target_to_text(tup, templ)
                    reason_eval += cur_reason
        else:
            is_first = True
            if not self.is_chameleon:
                if self._is_leak:
                    reason_eval = ", because the clue give away the secret code "
                    is_first = False            
            
            for tup, real in zip(self.target, self._realized_target):
                if not real:
                    templ = random.choice(self._fail_reason_templs)
                    if is_first:
                        cur_reason = self._target_to_text(tup, templ)
                        is_first = False
                    else:
                        cur_reason = " and " + self._target_to_text(tup, templ)
                    reason_eval += cur_reason
        s += reason_eval

        return s


            
    def _target_to_text(self, tup, templ):

        sub, obj, val = tup
        if val == -1:
            act = "decrease"
        elif val == 1:
            act = "increase"
        else:
            print(val, "is not supported")
            return
        templ = templ.replace("<ACT>", act)
        templ = templ.replace("<OBJ>", self.player_names[obj])
        templ = templ.replace("<SUB>", self.player_names[sub])
        return templ

    
    def print(self):
        
        print(f"{self. player_name}: {self.clue_text}, is good clue or not", self._good_clue)
        for tup in self.target:
            templ = f"{self.player_name} is trying to <ACT> <OBJ>'s suspiciousness in <SUB>'s eye."
            templ = self._target_to_text(tup, templ)
            print(templ)
        
                

