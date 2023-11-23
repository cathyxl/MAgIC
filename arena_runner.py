from run_competition_chameleon import Competition_Chameleon
from run_competition_undercover import Competition_Under_Cover
from run_competition_airportfee import Competition_Airportfee
from run_competition_prisoner import Competition_Prisoner
from run_competition_public_good import Competition_Public_Good

import openai

import time
import copy
import os


# 获取当前文件的绝对路径
current_file = os.path.abspath(__file__)

# 获取当前文件的目录
current_dir = os.path.dirname(current_file)


# 获取utils目录的路径
utils_dir = os.path.join(current_dir, 'utils')


config_dir= os.path.join(current_dir, 'config_release')

print(config_dir)
print('!!!!!\n\n')
chameleon_competition='competition_as_chameleon'
non_chameleon_competition='competition_as_non_chameleon'
undercover_competition='competition_as_undercover'
non_undercover_competition='competition_as_non_undercover'
airport_competition='competition_airportfee'
prisoner_competition='competition_prisoner'
public_good_competition='competition_public_good'

save_dir=os.path.join(current_dir, 'results')


def run(chatbox, path):
     
    if chatbox is not None:
        global_config.chatbox = chatbox
    
    test_player_model_name='gpt-3.5-turbo'
    
    # if you want to test the pgm version, add the postfix"-pgm" after the name of the openai models.
    # test_player_model_name='gpt-3.5-turbo-pgm'
    
    num_of_game=1

    print('>>>>>>>>>>>>>>> We are running Chameleon game') 
    competition_chameleon = Competition_Chameleon()
    competition_chameleon.run(config_dir, non_chameleon_competition, save_dir+'/chameleon', test_player_model_name, num_of_game=num_of_game)
    
    print('>>>>>>>>>>>>>>> We are running Chameleon game')    
    competition_chameleon = Competition_Chameleon()
    competition_chameleon.run(config_dir, chameleon_competition, save_dir+'/chameleon', test_player_model_name, num_of_game=num_of_game)

    print('>>>>>>>>>>>>>>> We are running undervocer game')
    competition_undercover = Competition_Under_Cover()
    competition_undercover.run(config_dir, undercover_competition, save_dir+'/undercover', test_player_model_name, num_of_game=num_of_game)

    print('>>>>>>>>>>>>>>> We are running undervocer game')
    competition_chameleon = Competition_Under_Cover()
    competition_chameleon.run(config_dir, non_undercover_competition, save_dir+'/undercover', test_player_model_name, num_of_game=num_of_game)

    print('>>>>>>>>>>>>>>> We are running airport game')
    competition_airportfee = Competition_Airportfee()
    competition_airportfee.run(config_dir, airport_competition, save_dir+'/airportfee', test_player_model_name, num_of_game=num_of_game)

    print('>>>>>>>>>>>>>>> We are running Prisoner game')
    competition_pirportfee = Competition_Prisoner()
    competition_pirportfee.run(config_dir, prisoner_competition, save_dir+'/prisoner', test_player_model_name, num_of_game=num_of_game)


    print('>>>>>>>>>>>>>>> We are running pulic good game')
    competition_pirportfee = Competition_Public_Good()
    competition_pirportfee.run(config_dir, public_good_competition, save_dir+'/public_good', test_player_model_name, num_of_game=num_of_game)
    
    from metrics_release import Metric
    
    print('>>>>>>>>>>>>>>> Calculating the assessment results')
    Metric_cal = Metric(num_of_game=num_of_game)
    Metric_cal.metric_calculation(path, test_player_model_name)
    

run(None, "gpt-3.5-turbo_metrics.json")