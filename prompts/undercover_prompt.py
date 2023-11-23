pgm_template_v5 = '''You are playing undercover game with other two player. The player who gets a different word from other players is the undercover while others are non-undercovers.
{clues}
According to the above clues, please answer the following question(s):
'''

pgm_template_questions ={
    "is_undercover": '''1. You are {player}, your word is {code}. Guess what are the words {other_player_1} and {other_player_2} are describing?  Compare your word with their clues, what role do you think you are?(Only when other two players both give clues that are different from your word, you can take you self as undercover)''',
    "self_pgm_non_under": "{idx}. You are {player}, your word is {code}, guess who is more possible to be the undercover from your own perspective. (hint: use the format, I think Player xx is undercover, because...)\n",
    "other_pgm_non_under": "{idx}. You are {player}, your word is {code}. Now try to guess now who {other_player} thinks is the undercover. (hint: use the format, I think {other_player} thinks Player xx is undercover, because...)\n",
    "other_pgm_under": "{idx}. You are {player}, your word is {code}, you think you are undercover. Now try to guess now who {other_player} thinks is the undercover. (hint: use the format, I think {other_player} thinks Player xx is undercover, because...)\n",
    "under_plan": "{idx}. I think the word of other player may be ... I will try to give my next clue as ..., which is similar to them to hide my self.",
    "non_under_plan": "{idx}. I will try to a more specific clue about my word as... to help identify who is undercover."
}


analysis_demo_v1 = '''[Moderator->all]: Now the game starts! The topic is: Countries
[Moderator->Player 1]: Your word is: coke zero
[Moderator->Player 2]: Your word is: coke zero
[Moderator->Player 3]: Your word is: coke
[Moderator->all]: Now everyone gives one clue (but never include the secret word). You cannot repeat what others has said. We will start with Player 1.
[Player 1->all]: It's a less sugary version of a popular drink.
[Player 2->all]: It's often associated with a diet.
[Player 3->all]: It's a black beverage in a red can.
[Player 1->Player 1]: As Player 1, I think:
Player 2 is less suspicious, because Player 2's clue mentions diet, which seems to be describing coke zero, which is the same with mine word, so both of us should be non-undercover.
Player 3 is more suspicious, because Player 3 didn't mention typical healthy feature of the word, his word could be coke instead of coke zero.
As for other players' perspectives:
I think now Player 2 think:
Player 1 is less suspicious, because my clue may be indicating the same word to Player 2's.
Player 3 is more suspicious.
I think now Player 3 think:
Player 1 is no change.
Player 2 is no change, because he may be considering himself as undercover.'''

undercover_view_demo_undercover='''
Here are several demos to teach how to analyze whether you are the undercover:
### demo 1 ###
Player 1: It's something you get at a salon
Player 2: It's often used in theater productions
Player 3: It's a way to change your appearance.
1. You are Player 2, your word is wig, guess the words other players are describing. Do you think you are the undercover? 
Not sure, I can be the undercover. Because, first Player 1 is not quite related to wig, since we won't think about salon when talking about wig. Second, Player 3's clue is a little general, it can be applied to many things instead of only the wig. Therefore I need to wait for more rounds, and give clue cautiously.

### demo 2 ###
Player 1: My clue is: minimalism
Player 2: My clue is precision.
Player 3: My clue is target.
1. You are Player 1, your word is simplicity, guess the words other players are describing. Do you think you are the undercover? 
Yes, I am the undercover, because Player 2's precision is not describing simplicity but could be something related to accuracy. Player3's "target" is related but is not the first thing you think about simplicity.

### demo 3 ###
Player 1: My clue is: television.
Player 2: My clue is: radio.
Player 3: My clue is: audience.
1. You are Player 3, your word is listener, guess the words other players are describing. Do you think you are the undercover? 
No, I am not the undercover, since Player 2 's clue "radio" is specific to listener, so I think his word is the same to min. Player 1's clue "television" is related to vision instead of sound.
'''

clue_templ_active_unclear_v2="{player}, according to your previous analysis, you are not sure who is undercover, give not too specific clue and don't reveal the word you have."
clue_templ_active_non_undercover_v2="{player} according to your previous analysis, you think {target_player} is undercover. Try to increase {target_player}'s suspiciousness. For example, by giving more specific and different clues compared to the clue of {target_player}. You can give a clue based on your above analysis. "
clue_templ_active_undercover_v2='''{player}, according to your previous analysis above to give your clue. '''

undercover_clue_demo = {
    "undercover":"",
    "non-undercover": ""
}


undercover_view_demo = {
    "undercover":"",
    "non-undercover": "",
}

global_prompt_undercover = '''You are playing a game of the Undercover. Here are the game rules:

## Information and roles
There are two roles in the game, undercover and non-undercover.
Each Player will get one word but the one undercover get will be different from other players'.

## Objectives
First you should guess who is undercover based on everyone's clues. 
Don't give too specific clue in case expose your own role.
After you have guessed your own role, then your objective in the game depends on your role:
- If your are not a undercover, your goal is to reveal the undercover without exposing your own word.
- If you are a undercover, your aim is to blend in with other players, avoid being caught.

## Stages
There are two stages in the game:
1. The giving clues stage: each player will describe the clues about their own words. This stage will continue for several rounds.
2. The accusation stage: In this stage, each player will vote for another player who is most likely the undercover. The undercover should vote for other players.
'''


global_prompt_undercover_pgm = '''You are playing a game of the Undercover. Here are the game rules:

## Information and roles
There are two roles in the game, undercover and non-undercover.
Each Player will get one word but the one undercover get will be different from other players'.

## Objectives
First you should guess who is undercover based on everyone's clues. 
Don't give too specific clue in case expose your own role.
After you have guessed your own role, then your objective in the game depends on your role:
- If your are not a undercover, your goal is to reveal the undercover without exposing your own word.
- If you are a undercover, your aim is to blend in with other players, avoid being caught.

## Stages
There are two stages in the game:
1. The giving clues stage: each player will describe the clues about their own words. This stage will continue for several rounds.
2. The accusation stage: In this stage, each player will vote for another player who is most likely the undercover. The undercover should vote for other players.

## Analysis
To analyze whether you are the undercover, you need to carefully distinguish the subtle differences among all the clues
-If most of the other players' clues are consistent but yours are a little different, you may be the undercover.
-The two words for undercover and non-undercovers are very similar, you should be careful and don't be too confident in the role you think you are.
'''

metric_pgm_template_questions ={
    "general": "Please answer the following questions.\n",
    "consistency": "Tell me which Player you are and whether you are the undercover according to all the above clues. If you cannot decide please answer with not sure. Please answer with the template \"I am Player xx, my role is undercover/non-undercover/not sure, because...\"",
    "self_pgm": "{idx}. Guess who is more possible to be the undercover from your own perspective. (hint: use the format, I think Player xx is undercover, because...)\n",
    "inter_pgm": "{idx}. Now try to guess now who {other_player} thinks is the undercover. (hint: use the fomat, I think {other_player} thinks Player xx is undercover, because...)\n",
}

