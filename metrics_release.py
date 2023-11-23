import json
import re
import os


all_scores = []
player_names =["Player 1","Player 2","Player 3"]

class Metric():
    def __init__(self, num_of_game=21):
        self.players = ["Player 1", "Player 2", "Player 3"]
        self.all_scores = {}

        self.num_of_game = num_of_game
        print(self.num_of_game)
        self.data = [
            {
            "train_split": {
                "Win Rate": 0,
                "Judgement": 0,
                "Reasoning": 0,
                "Deception": 0,
                "Self-Awareness": 0,
                "Cooperation": 0,
                "Coordination": 0,
                "Rationality": 0,
                "Total": 1000
            }
            }
        ]
        

    def chameleon_score(self,role, win_flag_dict):
        score = 0
        if self.num_of_game >= 21:
            n = 20
        else:
            n = self.num_of_game
        for win_flag in win_flag_dict:
            flag_num = win_flag_dict[win_flag]
            if win_flag == 0:
                if role=="chameleon":
                    score += 0*flag_num
                else:
                    score += 2*flag_num
            elif win_flag == 1:
                if role=="chameleon":
                    score += 1*flag_num
                else:
                    score += 1*flag_num
            elif win_flag == 2:
                if role=="chameleon":
                    score += 2*flag_num
                else:
                    score += 0*flag_num
            elif win_flag == 3:
                if role=="chameleon":
                    score += 1*flag_num
                else:
                    score += 1*flag_num
            else:
                print(f"win flag {win_flag} not supported")
        print(score, n*2)
        return score/(n*2)


    def undercover_score(self, role, win_flag_dict):
        score = 0
        if self.num_of_game >= 21:
            n = 20
        else:
            n = self.num_of_game
        for win_flag in win_flag_dict:
            flag_num = win_flag_dict[win_flag]
            if win_flag == 0:
                if role=="undercover":
                    score += 0*flag_num
                else:
                    score += 3*flag_num
            elif win_flag == 1:
                if role=="undercover":
                    score += 3*flag_num
                else:
                    score += 0*flag_num
            elif win_flag == 2:
                if role=="undercover":
                    score += 2*flag_num
                else:
                    score += 1*flag_num
            else:
                print(f"win flag {win_flag} not supported")
        print(score, n*3)
        return score/(n*3)


    def judge(self, result_path, postfix):
        non_right_vote = 0
        non_total_vote = 0
        scores = []
            
        for path, post in zip(result_path, postfix):
            print(path, post)
            non_chameleon_right_vote = 0
            non_chameleon_vote = 0  
            win_flag_dict = {}
            

            for game_id in range(self.num_of_game):
                fname = f"{path}/{game_id}{post}.json"
                #print(fname)
                if not os.path.exists(fname):
                    continue
                #print(fname)
                with open(fname) as f:
                    d = json.load(f)
                    chameleon = d["undercover"] if "undercover" in d else d["chameleon"]
                    votes = d["player_vote"] if "player_vote" in d else d["player_votes"]
                    k = 0
                    print(chameleon)
                    print(votes)
                    for pl in votes:
                        if pl != chameleon:
                            if votes[pl] == chameleon:
                                non_chameleon_right_vote += 1
                                k += 1
                            non_chameleon_vote +=1 
                    win_flag = d["win_flag"]
                    if win_flag not in win_flag_dict:
                        win_flag_dict[win_flag] = 0
                    win_flag_dict[win_flag] += 1
            if "chameleon" in path:
                role = "non-chameleon" if ("non-chameleon" in path or "non_chameleon" in path) else "chameleon"
                cur_score = self.chameleon_score(role, win_flag_dict)
            elif "undercover" in path:
                role = "non-undercover" if ("non-undercover" in path or "non_undercover" in path) else "undercover"
                cur_score = self.undercover_score(role, win_flag_dict)
            else:
                print("do not support this type of game")

            print(non_chameleon_right_vote, non_chameleon_vote)
            print("vote acc:", non_chameleon_right_vote/non_chameleon_vote)
            
            print("score: ", cur_score)
            non_right_vote += non_chameleon_right_vote
            non_total_vote += non_chameleon_vote
            scores.append(cur_score)
        
        print("judgement:", non_right_vote/non_total_vote) 
        self.data[0]["train_split"]['Judgement'] = round(non_right_vote/non_total_vote,3)
        return scores
        


    def decept(self,result_path, postfix):
        print(result_path)
        scores = []
        win_num = 0.0
        total_num = 0.0
        guess_right_num = 0.0
        guess_num = 0.0


        for path, post in zip(result_path, postfix):
            print(path)
            win_flag_dict = {}
            
            for game_id in range(self.num_of_game):
                fname =f"{path}/{game_id}{post}.json"
                if not os.path.exists(fname):
                    continue
                # if role == "non-chameleon":
                with open(fname) as f:
                    d = json.load(f)
                    if d["win_flag"] not in win_flag_dict:
                        win_flag_dict[d["win_flag"]] = 0
                    win_flag_dict[d["win_flag"]] += 1

            if "chameleon" in path:
                role = "non-chameleon" if ("non-chameleon" in path or "non_chameleon" in path) else "chameleon"
                cur_score = self.chameleon_score(role, win_flag_dict)
            elif "undercover" in path:
                role = "non-undercover" if ("non-undercover" in path or "non_undercover" in path) else "undercover"
                cur_score = self.undercover_score(role, win_flag_dict)
            else:
                print("do not support this type of game", path)
                exit()


            if role == "non-chameleon":
                for tag in win_flag_dict:
                    if tag in [0, 1]:
                        guess_num += 1
                        if tag == 1:
                            guess_right_num += 1    
            else:
                for tag in win_flag_dict:
                    if tag != 0:
                        win_num += win_flag_dict[tag]
                    total_num += win_flag_dict[tag]
            
            print(win_flag_dict)
            if role != "non-chameleon":
                print("score:", cur_score)
                scores.append(cur_score)
        print(win_num, total_num)
        print("deception:", win_num/total_num+0.25*(guess_right_num/guess_num))
        self.data[0]["train_split"]['Deception'] = round(win_num/total_num+0.25*(guess_right_num/guess_num),3)
        return scores


    def collabration(self, result_path, postfix):
        print(result_path)
        win_num = 0.0
        total_num = 0.0
        cost = 0.0
        agreed_proposal = 0.0

        for path, post in zip(result_path, postfix):
            win_results = {}
            
            for game_id in range(self.num_of_game):

                fname =f"{path}/{game_id}{post}.json"
                # print(fname)
                if not os.path.exists(fname):
                    continue
                # print(fname)
                with open(fname) as f:
                    d = json.load(f)
                    if d["result"]=="agree":
                        if "vote" in d:
                            vote = list(d["vote"].values())[0]
                        else:
                            pattern = r"I vote for (Player \d+)"
                            match = re.search(pattern,  d["history"][-2]["content"])
                            assert match is not None
                            vote = match.group(1)

                        test_play_idx = player_names.index(d["test_player_name"])
                        voted_proposal = list(d["proposal"][vote].values())
                        print(voted_proposal,list(d["proposal"][d["test_player_name"]].values()))
                        if voted_proposal == list(d["proposal"][d["test_player_name"]].values()):
                            agreed_proposal += 1
                            
                        if "%" in voted_proposal[test_play_idx]:
                            cur_cost = float(voted_proposal[test_play_idx].replace("%",""))
                        elif "," in voted_proposal[test_play_idx]:
                            cur_cost = 100*(float(voted_proposal[test_play_idx].replace(",",""))/1000000)
                        else:
                            try:
                                cur_cost = float(voted_proposal[test_play_idx])
                            except:
                                print("cannot parse", voted_proposal[test_play_idx])
                                cur_cost = 30

                        cost += cur_cost

                    if d["result"] not in win_results:
                        win_results[d["result"]] = 0
                    win_results[d["result"]] += 1

            for tag in win_results:
                if tag == "agree":
                    win_num += win_results[tag]
                total_num += win_results[tag]

            print(win_results)
        print(agreed_proposal)
        print("Coordination: ", agreed_proposal/win_results["agree"])
        self.data[0]["train_split"]['Coordination'] = round(agreed_proposal/win_results["agree"],3)
        print(cost)
        print("Cost:", cost/win_results["agree"])
        print(win_num, total_num)
        win_rate = win_num/total_num
        print("Collaboration/sucess rate: ", win_rate)
        self.data[0]["train_split"]['Cooperation'] = round(win_rate,3)
        return [win_rate]

    def consist_pgm(self, result_path, postfix):
        print(result_path)
        consist_num = 0.0
        total_num = 0.0
        player_names = ["Player 1", "Player 2", "Player 3"]

        gold_pgm_num = 0.0
        total_gold_pgm_num = 0.0

        inter_pgm_num = 0.0
        total_inter_pgm_num = 0.0

        for path, post in zip(result_path, postfix):
            
            if "chameleon" in path:
                if "non-chameleon" in path or "non_chameleon" in path:
                    eval_role = "non-chameleon"
                else:
                    eval_role = "chameleon"
            elif "undercover" in path:
                if "non-undercover" in path or "non_undercover" in path:
                    eval_role = "non-undercover"
                else:
                    eval_role = "undercover"
            else:
                print("cannot find the game for ", path)
            print(eval_role)
            for game_id in range(self.num_of_game):
                target_players = []
                fname = f"{path}/{game_id}{post}.json"
                if not os.path.exists(fname):
                    continue
                with open(fname) as f:
                    d = json.load(f)
                    
                    if eval_role in d:
                        target_players.append(d[eval_role])
                    else:
                        target_players = [p for p in player_names if p != d[eval_role.replace("non-","")]]
                    target_player_inds = [player_names.index(p) for p in target_players]
                    #print(target_players, target_player_inds)
                    for t in d["consistency_metric"]:
                        #print("in 1")
                        consist_num += sum([d["consistency_metric"][t][p] for p in target_players])
                        total_num += len(target_players) 
                    
                    for t in d["pgm_metric"]:
                        #print("in 2")
                        gold_pgm_num += sum([d["pgm_metric"][t]["gold"][p] for p in target_player_inds])  # pgm acc compared to gold roles 
                        total_gold_pgm_num += len(target_players)
                        inter_pgm_num += sum([d["pgm_metric"][t]["inter"][p] for p in target_player_inds])  # pgm acc compared to interview roles
                        total_inter_pgm_num += len(target_players) 

        print(consist_num, total_num)
        print(gold_pgm_num, total_gold_pgm_num)
        print(inter_pgm_num, total_inter_pgm_num)

        print("gold reasoning: ", gold_pgm_num/total_gold_pgm_num)
        print("inter reasoning: ", inter_pgm_num/total_inter_pgm_num,)
        print("Consistency: ", consist_num/total_num)
        print("Reasoning:", (gold_pgm_num+inter_pgm_num)/(total_inter_pgm_num+total_gold_pgm_num))
        self.data[0]["train_split"]['Reasoning'] = round((gold_pgm_num+inter_pgm_num)/(total_inter_pgm_num+total_gold_pgm_num),3)
        self.data[0]["train_split"]['Self-Awareness'] = round(consist_num/total_num, 3)
        

    
    def rational(self, result_path, postfix):
        
        print(result_path, postfix)
        win_rates =[]

        def norm_decision(dec):
            dec = re.sub(r'\.<eos>$|\.$', '', dec.lower())
            if dec.find("cooperate")>=0:
                return "cooperate"
            else:
                return "defect"
        def extract_contribute(dec):
            #print(dec)
            pattern =r"contribute (\d+)"
            match = re.search(pattern, dec)
            if match:
                bid = match.group(1)
            else:
                #print(dec)
                print("cannot parse the decision")
                bid = "0"
            # print(bid)
            
            return int(bid) if bid.isdigit() else 0

        decisions = {'non-rational':0, "rational":0}
        
        for path, post in zip(result_path, postfix):
            win_num = 0
            total_num = 0
            test_game="public_good"
            if path.find("prisoner")>=0:
                test_game="prisoner"
            for game_id in range(self.num_of_game):
                fname = f"{path}/{game_id}{post}.json"
                if not os.path.exists(fname):
                    continue
                target_players = []
                with open(fname) as f:
                    d = json.load(f)
                    test_player_name = d["test_player_name"]
                    test_player_idx = self.players.index(test_player_name)
                if d["result"] == "win":
                    win_num += 1   
                total_num += 1

                if test_game=="prisoner":
                    for msg in d["history"]:
                        if msg["agent_name"].startswith("Player") and msg["visible_to"] == "Moderator" and msg["agent_name"]==test_player_name:
                            if norm_decision(msg["content"])=="defect":
                                decisions["rational"] += 1
                            else:
                                decisions["non-rational"] += 1
                else:
                    cur_round_contributes = []
                    for msg in d["history"]:
                        if msg["agent_name"].startswith("Player") and msg["visible_to"] == "Moderator":
                            cur_round_contributes.append(extract_contribute(msg["content"]))
                            if len(cur_round_contributes) == 3:
                                min_contribute = min(cur_round_contributes)
                                if cur_round_contributes[test_player_idx] == min_contribute:
                                    decisions["rational"] += 1
                                else:
                                    decisions["non-rational"] += 1
                                cur_round_contributes = []

            win_rates.append(win_num/total_num)
        print("Rationality:", decisions["rational"]/sum(decisions.values()))
        self.data[0]["train_split"]['Rationality'] = round(decisions["rational"]/sum(decisions.values()),3)
        return win_rates


    def metric_calculation(self,path, test_player_model_name):
        current_path = os.path.abspath(__file__)
        directory_path = os.path.dirname(current_path)

        model_results ={
            "non-chameleon":{
                "gpt3.5": {"path":f"{directory_path}/results/chameleon/{test_player_model_name}_competition_as_non_chameleon_vs_gpt4", "post":""},
            },
            "chameleon":{
                "gpt3.5": {"path":f"{directory_path}/results/chameleon/{test_player_model_name}_competition_as_chameleon_vs_gpt4", "post":""},
            },

            "non-undercover":{
                "gpt3.5": {"path":f"{directory_path}/results/undercover/{test_player_model_name}_competition_as_non_undercover_vs_gpt4", "post":""},
            
            },
            "undercover":{
                "gpt3.5": {"path":f"{directory_path}/results/undercover/{test_player_model_name}_competition_as_undercover_vs_gpt4", "post":""},
            
            },
            "prisoner":{
                "gpt3.5": {"path":f"{directory_path}/results/prisoner/{test_player_model_name}_competition_prisoner_vs_gpt4", "post":""},
        
            },
            "public_good":{
                "gpt3.5": {"path":f"{directory_path}/results/public_good/{test_player_model_name}_competition_public_good_vs_gpt4", "post":""},
            },
            "airport":{
                "gpt3.5": {"path":f"{directory_path}/results/airportfee/{test_player_model_name}_competition_airportfee_vs_gpt4", "post":""},
            }
        }


        
        models = list(model_results["chameleon"].keys())
        for m in models:
            if m not in self.all_scores:
                self.all_scores[m] = []
        "Judgement"
        print("=============Judgement===========")
        for model in models:
            result_path = [model_results["non-chameleon"][model]["path"],model_results["non-undercover"][model]["path"]]
            postfix = [model_results["non-chameleon"][model]["post"],model_results["non-undercover"][model]["post"]]

            scores = self.judge(result_path, postfix)
            self.all_scores[model] += scores


        print("=============Deception===========")
        for model in models:
            result_path = [model_results["chameleon"][model]["path"],model_results["undercover"][model]["path"], model_results["non-chameleon"][model]["path"]]
            postfix = [model_results["chameleon"][model]["post"],model_results["undercover"][model]["post"], model_results["non-chameleon"][model]["post"]]

            scores = self.decept(result_path, postfix)    
            self.all_scores[model] += scores
            
        print("=============Conistency and Reasoning===========")
        for model in models:
            #if "pgm" not in model:
            #    continue
            result_path = [model_results["chameleon"][model]["path"],model_results["undercover"][model]["path"],model_results["non-chameleon"][model]["path"],model_results["non-undercover"][model]["path"]]
            postfix = [model_results["chameleon"][model]["post"],model_results["undercover"][model]["post"],model_results["non-chameleon"][model]["post"],model_results["non-undercover"][model]["post"]]
            self.consist_pgm(result_path, postfix)

        print("=============Collaboration===========")
        for model in models:
            result_path = [model_results["airport"][model]["path"]]
            postfix = [model_results["airport"][model]["post"]]
            sucess_rate = self.collabration(result_path, postfix)
            self.all_scores[model] += sucess_rate
        print("=============Rationality===========")


        for model in models:
            result_path = [model_results["prisoner"][model]["path"],model_results["public_good"][model]["path"]]
            postfix = [model_results["prisoner"][model]["post"],model_results["public_good"][model]["post"]]
            win_rates = self.rational(result_path, postfix)
            self.all_scores[model] += win_rates
        for m in self.all_scores:
            assert len(self.all_scores[m]) == 7
            print(f"Model: {m}, win rate: ", sum(self.all_scores[m])/len(self.all_scores[m]))
            self.data[0]["train_split"]['Win Rate'] = round(sum(self.all_scores[m])/len(self.all_scores[m]),3)
        
        print(self.data)
        
        with open(path,'w') as f:
            f.write(json.dumps(self.data))
        

        exit()

#Metric_cal = Metric()
#Metric_cal.metric_calculation('result.json')