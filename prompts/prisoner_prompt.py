topic_template = """
The scoring is as follows:
- If all three choose to cooperate, they each get {cooperate} points.
- If all three choose to defect, they each get {defect} point.
- If one chooses to defect and the others choose to cooperate, the betrayer gets  {one_defect} points and the collaborators each get 0 points.
- If two choose to defect and the other chooses to cooperate, the betrayers each get {two_defect} points, and the collaborator gets 0 points.
The game is played for 5 rounds, and the total score is calculated at the end to determine the winner.
"""

# role_desc_pgm ='''You play as Player 1. Your task is to analyze how other players may behave based on the previous decisions made by all the players. You will be asked to give analysis or give a decision. 
# - analysis, follow the template to give an anlysis. 
# - decision, choose to betray the others (Defect, D) or cooperate with them (Cooperate, C) in each round. '''

role_desc_pgm ='''You play as Player 1. Your will be asked to give a decision or give analysis about how other players may behave based on the previous decisions made by all the players.
- analysis, follow the template to give an anlysis.
- decision, choose to betray the others (Defect, D) or cooperate with them (Cooperate, C) in each round based on previous decisions of players and your own analysis.'''


pgm='''Please try to analyze how other players will choose to defect or corporate in next round from you own perspective and others' perspective. 
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

pgm_decision='''Based on your own analysis about others and other's thoughts
- Remember to be strategic, establishing trust is to defect before others plan to do it to get highest score.
- choose "defect" or "cooperate" to achieve the highest points for yourself.
You must reply with \"Cooperate\" or \"Defect\"'''
