import pandas as pd
import string
from scraper import scrapy
from tourney import Bracket

# grabbing the world cup teams and games from the scraper object
team_url = "https://play.fifa.com/json/bracket_predictor/squads.json"
team_data = scrapy(team_url).findData()
# team name preprocessing
for d in team_data:
    if d["name"] == "Bosnia-Herzegovina":
        d["name"] = "Bosnia and Herzegovina"
    else:
        continue

games_url = "https://play.fifa.com/json/bracket_predictor/rounds.json"
games_data = scrapy(games_url).findData()

historical_matches_data = pd.read_csv(r"/Users/nickbourgeois/Documents/python/world-cup-tournament-challenge/data/ranked_team_schedules.csv")

rank_data = pd.read_csv(r"/Users/nickbourgeois/Documents/python/world-cup-tournament-challenge/data/latest_fifa_rankings.csv")


bad_count = 0
good_count = 0
winner_results = []
top_24_results = []
for i in range(100):
    try:
        world_cup = Bracket(team_data, games_data, historical_matches_data, rank_data)
        post_gs_teams, post_gs_games = world_cup.group_play()
        gt, top_32 = world_cup.commissioner()
        top_16 = world_cup.round_32(top_32)
        top_8 = world_cup.knockout_stage(top_16)
        top_4 = world_cup.knockout_stage(top_8)
        top_2 = world_cup.knockout_stage(top_4)
        top_1 = world_cup.knockout_stage(top_2)

        winning_team = world_cup.knockout_stage(top_1)
        print(winning_team.name)
        
        # creating the results list objects
        winner_results.append(winning_team.name)
        top_24 = {i: [val.name for val in top_32[lister][:2]] for i, lister in zip(string.ascii_uppercase, top_32)}
        top_24_results.append(top_24)

        good_count+=1
    
    except ValueError:
        bad_count += 1


print(f"{bad_count} simulations didn't work because of a ValueError")
print(f"{good_count} simulations worked")

# stats of the simulation
winner_set = set(winner_results)
winner_data = [(team, sum([1 for name in winner_results if name == team]) / good_count) for team in winner_set]
winner_data.sort(key=lambda x: x[1], reverse=True)
print(winner_data[:5])