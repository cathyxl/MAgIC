
global_prompt='''Welcome to the 'Public Good' game. Here is the game setting and rules.

- Each of you starts with 100 monetary points. In each of the {game_round} rounds, you will publicly decide how much to contribute to a communal pool. 
- The total contributions from all the players to this pool are times with {multiplier} and then evenly divided among all players. Contributions are public and known to all players after each round. 
- The winner is determined at the end of the {game_round} rounds, and is the player whose total of remaining points and the points earned from the communal pool is the highest. 
- Be mindful of the final stage where you can have chance to vote to penalize others, typically driven by perceptions of unfair contributions throughout the game.'''

global_prompt_nopenalty='''Welcome to the 'Public Good' game. Here is the game setting and rules.

- Each of you starts with 100 monetary points. In each of the {game_round} rounds, you will publicly decide how much to contribute to a communal pool. 
- The total contributions from all the players to this pool are times with {multiplier} and then evenly divided among all players. Contributions are public and known to all players after each round. 
- The winner is determined at the end of the {game_round} rounds, and is the player whose total of remaining points and the points earned from the communal pool is the highest. '''


global_prompt_nopenalty_v1 ='''Welcome to the 'Public Good' game. Below are the game's settings and rules:
- Each player begins with 100 monetary points. Over {game_round} rounds, you decide how many points to contribute to a communal pool at each round.
- After {game_round} rounds of decision-making, the points in the communal pool will be multiplied by a factor of {multiplier} and distributed equally among all players.
- A player's final score is determined by adding their remaining points to the shared points from the communal pool.
- The player with the highest score wins the game. Aim to be the winner!'''


# global_prompt_nopenalty_v2 ='''Welcome to the 'Public Good' game. Below are the game's settings and rules:
# - Each player begins with 100 monetary points. Over {game_round} rounds, you decide how many points to contribute to a communal pool at each round.
# - After {game_round} rounds of decision-making, the points in the communal pool will be multiplied by a factor of {multiplier} and distributed equally among all players.
# - A player's final points is the sum of their remaining points and the shared points from the communal pool. The player who gets the highest final points wins the game.
# - Every player must strategically invest your points to the communal pool to get more shared points and also be the one who invest the least to win the game.''

global_prompt_nopenalty_v2 ='''Welcome to the 'Public Good' game. Below are the game's settings and rules:
- Each player begins with 100 monetary points. Over {game_round} rounds, you decide how many points to contribute to a communal pool at each round.
- After {game_round} rounds of decision-making, the points in the communal pool will be multiplied by a factor of {multiplier} and distributed equally among all players.
- A player's final points is the sum of their remaining points and the shared points from the communal pool. The player who gets the highest final points wins the game.
- Every player must strategically invest your points to the communal pool to get more shared points and also be the one who invest the least to win the game.
- Usually you can get more payback by investing more when the factor is larger.
'''

# role_desc_pgm ='''You play as {player_name}. Your task is to analyze how other players may behave based on the previous decisions made by all the players. You will be asked to give analysis or give a decision. 
# - analysis, follow the template to give an anlysis. 
# - decision, choose to betray the others (Defect, D) or cooperate with them (Cooperate, C) in each round. '''


role_desc_pgm='''As {player_name}, you will be asked to decide how much of the 100 starting points to contribute to the communal pool at each round and analyze how other players will change their contributions based on the previous contributions of all players. 
- decision, decide how much money to contribute at each round and aim to maximize both your remaining points and earnings from the pool. Contributions are public. 
- analysis, follow the template to give your analysis.
'''

pgm='''Please try to analyze whether other player will "reduce" or "increase" their contributes in next round from you own perspective and others' perspective. 
- Remember, the payment in the communal pool is evenly shared by all players at the end of the game, so you need to make sure you invest the least of the money to get the highest repay.
You must use the template:
In my opinion:
As {player_name},
I think {oth_player1} will xx, because...
I think {oth_player2} will xx, because...
As for other players,
I think {oth_player1} thinks:
{player_name} will...
{oth_player2} will...
I think {oth_player2} thinks
{player_name} will...
{oth_player1} will...
'''

# pgm_decision='''Based on your own analysis about others and other's thoughts, make the decision about your own contribution to achieve the highest points for yourself. 
# - Remember, the payment in the communal pool is evenly shared by all players at the end of the game, so you need to make sure you invest the least of the money to get the highest repay.
# You must answer with the template "I contribute xx". '''

# pgm_decision='''Based on your own analysis about others and other's thoughts, make the decision about your own contribution to achieve the highest points for yourself. 
# - Remember, you target is to get highest replayment and win as much more repayment by encouraging other player to invest.
# - Remember, the payment in the communal pool is evenly shared by all players at the end of the game, so you need to make sure you invest the least of the money to get the highest repay.
# You must answer with the template "I contribute xx". '''

pgm_decision='''Based on your own analysis about others and other's thoughts, make the decision about your own contribution to achieve the highest replayment for yourself. Remember
- Your total investment should the least to win the game;
- Your target is to get highest points and also promote the commumal repayment to get as much as more points at the end.
You must answer with the template "I contribute xx". '''