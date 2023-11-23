role_desc_pgm='''As {player}, you represent {airline}. Based on the number of flights or passengers your airline handles, you need to negotiate and agree upon a proposal with other airlines. You aim to achieve a balance between fairness and cost-effectiveness for your airline. 
- You will be asked to analyze players' future possible adjustments within this game from the perspectives of your own and other players.
- Then,  you decide how to adjust your proposal based on your own analysis to ensure a higher possibility of agreement from other players.'''

negotiate_template='''Please give or adjust you proposal, the stride should be 5%, You must use the template\"As Player xx, representing Airline xx, I propose the following cost distribution:
Airline A: xx%
Airline B: xx%
Airline C: xx%\"
'''

global_prompt='''You are participating in the 'Airport Fee Allocation' game. You will each represent an airline and split the fix cost of the airport.
## Information: 
- The total cost of the airport is fixed, and all airlines must collectively cover this cost. 
- Airlines have their unique usage frequencies at the airport, determined by factors like flight size and passenger volume. Airlines with higher usage frequencies are responsible for a larger portion of the cost.
## Objectives:
- As an airline representative, you goal is to negotiate and agree upon a cost distribution that is both fair and favorable for your airline.
## Rules:
The negotiation will be continue for {max_turns} rounds. In each round:
- Proposa: Each airline proposes a cost distribution that you think are .
- Vote: Each player must vote a cost distribution they find acceptable and strive to reach a consensus with other players' votes.
- The game ends successfully when all airlines vote for the same proposal. If after {max_turns} rounds of voting no consensus is reached, the game fails. Strive for a successful outcome.'''



pgm = '''Please try to analyze how will players adjust their proposal from your perspective and other players in the next round. 
You must follow the template below ( make your comments concise):
As {player_name},
I think {oth_player1} will...
I think {oth_player2} will...
As for other players,
I think {oth_player1} thinks:
{player_name} will...
{oth_player2} will...
I think {oth_player2} thinks
{player_name} will...
{oth_player1} will...
'''

pgm_decision='''According to your own analysis about other players' possible decisions, try to adjust your proposal in the next round so that other players will all agree with you.
- If some players are stick to their decision and you think it is fair, you can follow their proposals to make sure agreement among you.
'''