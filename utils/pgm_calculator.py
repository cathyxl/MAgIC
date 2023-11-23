import numpy as np
import random
def softmax(x):
    "softmax in last axis"
    e_x = np.exp(x-np.max(x, axis=-1, keepdims=True))
    return e_x/e_x.sum(axis=-1, keepdims=True)

class PGM:
    def __init__(self, is_chameleon, num_players, player_idx):
        self.player_idx = player_idx
        self.factor_scale = 0.1
        self.is_chameleon = is_chameleon
        self.num_players = num_players

        self.pgm = np.ones((num_players, num_players))
        # pgm from self's perspective
        if is_chameleon:
            self.pgm[player_idx] = self.pgm[player_idx] * 0.0
            self.pgm[player_idx][self.player_idx] = 1.0
        else:
            self.pgm[player_idx] = self.pgm[player_idx] * (1/(num_players-1))
            self.pgm[player_idx][self.player_idx] = 0.0
        # pgm from other players' perspectives
        for pi in range(num_players):
            if pi == player_idx:
                continue
            if is_chameleon:
                self.pgm[pi] = self.pgm[pi] * (1/(num_players-1))
                self.pgm[pi][pi] = 0.0
            else:
                self.pgm[pi] = self.pgm[pi] * (1/(num_players))

    def _get_self_pgm(self):
        return self.pgm[self.player_idx]
    
    def update(self, factor, mul=True):
        """
            factor: np.array(num_player, num_player)
        """

        if mul:
            factor = np.ones((self.num_players, self.num_players)) + self.factor_scale*factor
            self.pgm *= factor
            self.pgm = softmax(self.pgm)
        else:
            self.pgm += (self.factor_scale*factor)
        
    
    def get_target(self):
        # print(self.pgm)
        my_score = self.pgm[:,self.player_idx]
        # print("my_score: ", self.player_idx, my_score)
        if not self.is_chameleon:
            target = np.argsort(my_score)[-1]
            if target == self.player_idx:
                target = np.argsort(my_score)[-2]

        else:
            target = np.argsort(my_score)[0]
            # print(target, self.player_idx)
            if target == self.player_idx:
                target = np.argsort(my_score)[1]
        # print(self.is_chameleon, target)
        return int(target)


    
    def print(self):
        print(self.pgm)

    def _to_vote(self):
        pos = np.argsort(self.pgm[self.player_idx])
        if self.is_chameleon:
            if pos[-1] == self.player_idx:
                return pos[-2]
        return pos[-1]
            




# initialize pgm

# update pgm with factors


class UndercoverPGM:
    def __init__(self, num_players, player_idx):
        self.player_idx = player_idx
        self.factor_scale = 0.1
        self.num_players = num_players
        self.pgm = np.ones((num_players, num_players))/num_players
        
    def _get_self_pgm(self):
        return self.pgm[self.player_idx]
    
    def update(self, factor, mul=True):
        """
            factor: np.array(num_player, num_player)
        """

        if mul:
            factor = np.ones((self.num_players, self.num_players)) + self.factor_scale*factor
            self.pgm *= factor
            self.pgm = softmax(self.pgm)
        else:
            self.pgm += (self.factor_scale*factor)
    
    def get_target(self):
        # print(self.pgm)
        my_score = self.pgm[:,self.player_idx]
        my_view = self.pgm[self.player_idx]
        think_is_undercover = self.is_undercover()
        # if think is undercover, choose the one who suspect myself the least, and deceive him
        if think_is_undercover == "yes":
            target = np.argsort(my_score)[-1]
            if target == self.player_idx:
                target = np.argsort(my_score)[-2]
        # if think is not undercover, choose the one who I think are most suspicious, and increase his suspiciousness
        elif think_is_undercover == "no":
            target = np.argsort(my_view)[-1]
            if target == self.player_idx:
                target = np.argsort(my_view)[-2]
        else:
            target = -1
        
        return think_is_undercover, int(target)
    
    def is_undercover(self,threshold=0.0001):
        my_view = self._get_self_pgm()
        # print("Player ", self.player_idx+1, my_view, np.std(my_view))
        if np.std(my_view) <= threshold:
            return "not sure"
        if np.argmax(my_view) == self.player_idx:
            return "yes"
        else:
            return "no"


    
    def print(self):
        print(self.pgm)

    def _to_vote(self):
        # print(self.pgm[self.player_idx])
        my_view = self._get_self_pgm()
        pos = np.argsort(my_view)
        vote_pos = pos[-1]
        if vote_pos == self.player_idx:
            if my_view[pos[-3]] != my_view[vote_pos] : 
                vote_pos = pos[-2]
                return vote_pos
            else: # there are even notes
                return None

        else:
            # if the max score is not self, directly return
            return vote_pos
        # # if there are same score in other players, random one.
        # even_pos = []
        # for vi, val in enumerate(my_view):
        #     if val == my_view[vi] and vi != self.player_idx:
        #         even_pos.append(vi)
        # print(even_pos)
        # if len(even_pos) > 0:
        #     vote_pos = random.choice(even_pos)

        # return vote_pos          
            
