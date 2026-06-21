import pandas as pd
import json
import string
from scraper import scrapy
from tourney import Bracket

# 2026 knockouts start at the Round of 32 (first 48-team World Cup).
# `furthest_stage` is an ordinal: the last round a team reached.
STAGE_ORDER = {
    "group": 0,      # eliminated in the group stage
    "r32": 1,        # reached the Round of 32
    "r16": 2,        # reached the Round of 16
    "qf": 3,         # reached the Quarterfinals
    "sf": 4,         # reached the Semifinals
    "final": 5,      # reached the Final (runner-up)
    "champion": 6,   # won the tournament
}

# defining function to find team's furthest stage
def find_stage(teams_list, team_object):
    amt_in_teams_list = sum([1 for team in teams_list if team.name == team_object.name])
    if amt_in_teams_list == 0:
        return "group"
    elif amt_in_teams_list == 1:
        return "r32"
    elif amt_in_teams_list == 2:
        return "r16"
    elif amt_in_teams_list == 3:
        return "qf"
    elif amt_in_teams_list == 4:
        return "sf"
    elif amt_in_teams_list == 5:
        return "final"
    else:
        return "champion"

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
bad_index_count = 0
good_count = 0
winner_results = []
top_24_results = []
rows = []
for i in range(1000):
    try:
        world_cup = Bracket(team_data, games_data, historical_matches_data, rank_data)
        post_gs_teams, post_gs_games = world_cup.active_group_play()
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

        # creating parquet file for site
        round_32_teams = [t for group in top_16 for t in top_16[group]]
        round_16_teams = [t for group in top_8 for t in top_8[group]]
        qf_teams = [t for group in top_4 for t in top_4[group]]
        sf_teams = [t for group in top_2 for t in top_2[group]]
        final_teams = [t for group in top_1 for t in top_1[group]]
        knockout_teams = round_32_teams + round_16_teams + qf_teams + sf_teams + final_teams
        knockout_teams.append(winning_team)
        for group in gt:
            for team in gt[group]:
                gp = gt[group].index(team)
                stage = find_stage(knockout_teams, team)
                rows.append(
                    {
                        "sim": i,
                        "team": team.name,
                        "group": team.group,
                        "group_pos": gp + 1,
                        "furthest_stage": STAGE_ORDER[stage]
                    }
                )

        good_count+=1
    
    except ValueError:
        bad_count += 1
    
    except IndexError:
        bad_index_count += 1


if __name__ == "__main__":
    print(f"{bad_count} simulations didn't work because of a ValueError")
    print(f"{bad_index_count} simulations didn't work because of an IndexError")
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
    
    # Compact dtypes keep the file small and loading fast.
    sim_df = pd.DataFrame(rows)

    sim_df["team"] = sim_df["team"].astype("category")
    sim_df["group"] = sim_df["group"].astype("category")
    sim_df["group_pos"] = sim_df["group_pos"].astype("int8")
    sim_df["furthest_stage"] = sim_df["furthest_stage"].astype("int8")

    # requires pyarrow
    par_file_path = "/Users/nickbourgeois/Documents/python/WorldCupSimPage/data/results_04_after-matchday-10.parquet"
    sim_df.to_parquet(par_file_path, index=False)