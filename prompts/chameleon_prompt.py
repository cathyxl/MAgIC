
chameleon_demo='''
To help you know how to analyze roles, here is an example:
=====Demo: Player 2 Chameleon=====
[Moderator->all]: 
[Moderator->all]: Now the game starts! The topic is: Countries
[Moderator->Player 2]: You are the chameleon!
[Moderator->all]: Now Player 1, we can start from you to give the clue. Never inclue secret word.
[Player 1->all]: The clue is: Stars and Stripes

[Player 2->Player 2]: 
I think now the secret code is "United States", because stars and stripes are typical features of US flag.

As for other players's views:
I think now Player 1 thinks:
Player 2 is no change because I haven't given the clue.
Player 3 is no change because he also hasn't given the clue

I think now Player 3 thinks:
Player 1 is less suspicious because Player 1 give a very specific clue.
Player 2 is more suspicious because Player 3 may consider Player 1 and himself/herself are non-chameleons, so I could be chamemelon.
Next I will give a clue about the fast food of "United States".

[Player 2->all]: It is known for its fast food
====End of Demo====
'''

non_chameleon_clue_demo_post_old ='''
To help you know how to analyze roles, here is an example:
====Demo: Player 3 Non-Chameleon====
[Moderator->all]: Now the game starts! The topic is: Countries
[Moderator->['Player 3']]: You are not chameleon. The word is: United States
[Moderator->all]: Now Player 1, we can start from you to give the clue. Never inclue secret word.
[Player 1->all]: The clue is: Stars and Stripes
[Player 2->all]: It is known for its fast food

[Player 3->Player 3]: As Player 3, compare all the clues:
I think:
Player 1 first gave a clue that is specific to the secret code "United States", so Player 1 is less suspicious.
Player 2 could be the chameleon, since in my mind me and Player 1 should be non-chameleons, so Player 2 is more suspicious.

I think now Player 1 thinks:
Player 2's clue about fast food is actually a feature of US, so Player 2 is less suspicious.
Player 3 hasn't given the clue, so Player 3 is no change.

I think now Player 2 thinks:
Player 1 gave a very specific clue, so Player 1 is less suspicious.
Player 3 hasn't given a clue yet, so Player 3 is no change.

Next I will give clue about one US's famous thing, Hollywood.

[Player 3->all]: My clue is: Hollywood
====End of Demo====
'''
non_chameleon_demo_post='''
To help you know how to analyze roles, here is an example:
====Demo: Player 3 Non-Chameleon====
[Moderator->all]: Now the game starts! The topic is: Fruits
[Moderator->['Player 3']]: You are not chameleon. The word is:  Apple
[Moderator->all]: Now Player 1, we can start from you to give the clue. Never inclue secret word.
[Player 1->all]: It is sweet and sour.
[Player 2->all]: It's the main ingredient in a popular pie.

[Player 3->Player 3]: As Player 3, compare all the clues:
I think:
Player 1's clue about sweet and sour taste can be applied to many fruits, instead of only Apple, so Player 1 is more suspicious.
Player 2's clue is more specific to the secret code "Apple", so Player 2 is less suspicous.

I think now Player 1 thinks:
Player 2 gave a more specific clue about "Apple" than Player 1, so Player 2 is less suspicious.
Player 3 is no change because Player 3 hasn't given the clue.

I think now Player 2 thinks:
Player 1 hasn't seen Player 3's clue, and hard to decide Player 1 or 3 to be the chamelon, so Player 1 is no change.
Player 3 is no change because Player 2 hasn't given a clue yet.
Next I plan to give a clue about the taste of Apple, crispy and juicy.
====End of Demo====
'''


non_chameleon_demo_pre='''
To help you know how to analyze roles, here is an example:
====Demo: Player 3 Non-Chameleon====
[Moderator->all]: Now the game starts! The topic is: Fruits
[Moderator->['Player 3']]: You are not chameleon. The word is:  Apple
[Moderator->all]: Now Player 1, we can start from you to give the clue. Never inclue secret word.
[Player 1->all]: It is sweet and sour.
[Player 2->all]: It's the main ingredient in a popular pie.

[Player 3->Player 3]: As Player 3, compare all the clues:
I think:
Player 1 is more suspicous, because Player 1's clue about sweet and sour taste can be applied to many fruits, instead of only Apple.
Player 2 is less suspicous because the clue may be describing Apple pie, which is more specific to the secret code "Apple".

I think now Player 1 thinks:
Player 2 is less suspicious because Player 2's clue is more specific to secret code than Player 1.
Player 3 is no change because Player 3 hasn't given the clue.

I think now Player 2 thinks:
Player 1 is no change because for Player 2 it is hard to decide Player 1 or 3 to be the chamelon.
Player 3 is no change because Player 2 hasn't given a clue yet.
Next I will give a clue about the taste of Apple, crispy and juicy.

[Player 3->all]: It taste crispy and juicy.
====End of Demo====
'''



view_demo = {
    "chameleon": chameleon_demo,
    "non-chameleon": non_chameleon_demo_post,
}




chameleon_clue_demo='''
To help to improve your ability to give good clues, here is an example:
[Moderator->all]: Now the game starts! The topic is: Sports
=======Demo: Player 3 as chameleon========
[Moderator->['Player 1', 'Player 2']]: You are not chameleon. The word is: Cycling
[Moderator->Player 3]: You are the chameleon!
[Player 1->all]: two wheels
[Player 2->all]: you will need helmet
[Player 3->all]:
good clue: my clue is speed
bad clue: it requires teamwork
=======End of Demo========
'''

non_chameleon_clue_demo='''
To help to improve your ability to give good clues, here is an example:
[Moderator->all]: Now the game starts! The topic is: Animals
====Demo: Player 2 as non-chameleon====
[Moderator->['Player 1', 'Player 2']]: You are not chameleon. The word is: Elephant
[Moderator->Player 3]: You are the chameleon!
[Player 1->all]: It's large.
[Player 2->all]:
good clue: 
It eats plants.
It has thick skin.
bad clue: 
It has long nose. (too specific)
It's a mammal. (too general)
====End of Demo====
'''


clue_demo ={
    "chameleon": chameleon_clue_demo,
    "non-chameleon": non_chameleon_clue_demo
}

view_templ_active_chameleon_wcode_v2_fm= '''{player}, deduce the secret code based only on {other_player_1} and {other_player_2}'s clues and analyze who is more suspicious from the perspective of other players based on all the clues given. Your must follow the format in the demo.'''


view_templ_active_non_chameleon_v2_wformat_fm = '''{player}, based on the all the given clues, evaluate who is more suspicious to be chameleon from your thought and the thoughts of other players you think. If you haven't seen a player's clue, don't think up one for him.
You must follow the following format
As {player},
I think:
{other_player_1} is ..., because ...
{other_player_2} is ..., because ...
...
As for other players' thoughts:
I think now {other_player_1} thinks:
{player} is ..., because ...
{other_player_2} is ..., because ...
...
I think now {other_player_2} thinks:
{player} ..., because ...
{other_player_1} ..., because ...
...
'''

metric_pgm_non_chameleon_wformat = '''{player}, based on the all the given clues, evaluate who is more suspicious to be chameleon from your thought and the thoughts of other players you think. If you haven't seen a player's clue, don't think up one for him.
You must follow the following format.
-Choose your evaluation for each player with phrases from ["more suspicious","less suspicious", "no change"].
As {player},
I think:
Player xx is ..., because ...
Player xx is ..., because ...
...
As for other players' thoughts:
I think now Player xx thinks:
Player xx is ..., because ...
Player xx is ..., because ...
...
I think now Player xx thinks:
Player xx is ..., because ...
Player xx is ..., because ...
...
'''

metric_pgm_chameleon_wformat= '''{player}, deduce the secret code from all other players' clues and analyze who is more suspicious from the perspective of other players. 
-Remember to guess secret code by combining other players clues, you can repeat your secret code guess every time.
-Choose your evaluation for each player with phrases from ["more suspicious","less suspicious", "no change"].
You must respond in the following format:
I guess the secret code is "...", because...
As for other players' view now:
I think now Player xx think:
Player xx is ...
Player xx is ...
...
I think now Player xx think:
Player xx is ...
Player xx is ...
...
'''


metric_consistency="Tell me which Player you are and what is your role in the game. Please use the template \"I am Player xx, my role is chameleon/non-chameleon\""




clue_templ_active_v2_fm = "{player}, you are non-chameleon, your target is to increase the suspiciousness of the {target_player}. For example, by giving more specific clues than the {target_player}. Remember don't reveal the secret code; "

clue_templ_active_chameleon_v2_fm = '''{player}, you are chameleon, your target is to blend in and defraud trust from the {target_player}, try to describing the same word as other players. 
-If you are the first clue giver, try to be general in case exposing yourself.
-If you guessed the secret code, try to give a specific clue about the word. 
-If other players' clue are general, try give a clue similar to the {target_player}'s.'''



chameleon_global_prompt_pgm='''You are playing a game of the Chameleon. Here are the game rules:

## Information and roles
There are two roles in the game, chameleon and non-chameleon.
The topic of the secret word will be first revealed to all the players.
Then the secret word will be revealed to non-chameleons.
The chameleon does not know the secret word.

## Objectives
Your objective in the game depends on you role:
- If you are not a chameleon, your goal is to reveal the chameleon without exposing the secret word.
- If you are a chameleon, your aim is to blend in with other players, avoid being caught, and figure out the secret word.

## Stages
There are three stages in the game:
1. The giving clues stage: each player will describe the clues about the secret word.
2. The accusation stage: In this stage, each player will vote for another player who is most likely the chameleon. The chameleon should vote for other players.
3. The guess stage: If the accusation is correct, the chameleon should guess the secret word given the clues revealed by other players.

## Role evaluation
To help youself better analyze the roles of other players, there will be system command to ask you evaluate who is more suspicious as chameleon from your own perspective or other players' perspectives.
You should only analyze the exsiting clue, don't make up a clue for any other players.
You should choose your evaluation from the following choices:
- more suspicious is used when you suspect the player as chameleon since his/her clue is not related to the secret code.
- less suspicious is used when you think the player's clue exactly applies to the secret code.
- no change is used when you think it is hard to decide the player's role or the player hasn't given any clue.
'''

