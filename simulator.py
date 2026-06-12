import pandas as pd
import json
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
historical_matches_data.drop_duplicates(ignore_index=True, inplace=True)

rank_data = pd.read_csv(r"/Users/nickbourgeois/Documents/python/world-cup-tournament-challenge/data/latest_fifa_rankings.csv")


bad_count = 0
good_count = 0
winner_results = []
top_24_results = []
for i in range(1000):
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
        group_letters = [letter for letter, num in zip(string.ascii_uppercase, range(12))]
        top_24 = {i: [val.name for val in top_32[lister][:2]] for i, lister in zip(group_letters, top_32)}
        top_24_results.append(top_24)

        good_count+=1
    
    except ValueError:
        bad_count += 1


if __name__ == "__main__":
    print(f"{bad_count} simulations didn't work because of a ValueError")
    print(f"{good_count} simulations worked")

    # stats of the simulation
    def stat_collector(team_list, good_count):
        team_set = set(team_list)
        team_data = [(team, sum([1 for name in team_list if name == team]) / good_count) for team in team_set]
        team_data.sort(key=lambda x: x[1], reverse=True)

        return team_data

    winner_data = stat_collector(winner_results, good_count)

    group_positions = {}
    for group in group_letters:
        first_place_list = []
        second_place_list = []
        for d in top_24_results:
            first_place_list.append(d[group][0])
            second_place_list.append(d[group][1])

            first_probs = stat_collector(first_place_list, good_count)
            second_probs = stat_collector(second_place_list, good_count)
            group_positions[group] = (first_probs, second_probs)

    # saving the results to be manipulated in plots
    first_file_path = "/Users/nickbourgeois/Documents/python/world-cup-tournament-challenge/data/winner_data.json"
    second_file_path = "/Users/nickbourgeois/Documents/python/world-cup-tournament-challenge/data/group_positions.json"

    with open(first_file_path, "w") as first_file:
        json.dump(winner_data, first_file)
    
    with open(second_file_path, "w") as second_file:
        json.dump(group_positions, second_file, indent=4)