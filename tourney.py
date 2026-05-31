import numpy as np
import pandas as pd
from itertools import combinations
from collections import Counter
from scraper import scrapy

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

class Team(object):
    def __init__(self, name, group, id, points, goals_for, goals_against, world_rank, historical_games):
        self.name = name
        self.group = group
        self.id = id
        self.points = points
        self.goals_for = goals_for
        self.goals_against = goals_against
        self.world_rank = world_rank
        self.historical_games = historical_games
    
    def rank_mean_goals(self, opponent_rank):
        rank_mover = 10
        while True:
            if (opponent_rank - rank_mover) > 0:
                l_bound = opponent_rank - 20
            else:
                l_bound = 1
            
            if (opponent_rank + rank_mover) < 212:
                u_bound = opponent_rank + 20
            else:
                u_bound = 211
            mask = (self.historical_games["Opp Rank"] >= l_bound) & (self.historical_games["Opp Rank"] <= u_bound)
            similar_teams = self.historical_games[mask]

            if len(similar_teams) > 0:
                break
            else:
                rank_mover += 1

        return np.sum(similar_teams["GF"]) / len(similar_teams)
    
    def __str__(self):
        return f"{self.name} finished in group {self.group} with {self.points} points, {self.goals_for} goals for, and {self.goals_against} goals against."



class Match(object):
    def __init__(self, team_one, team_two):
        self.team_one = team_one
        self.team_two = team_two
        
    def calc_score(self):
        rng = np.random.default_rng()
        team_one_lam = self.team_one.rank_mean_goals(self.team_two.world_rank)
        team_two_lam = self.team_two.rank_mean_goals(self.team_one.world_rank)
        self.team_one_goals = rng.poisson(lam=team_one_lam)
        self.team_two_goals = rng.poisson(lam=team_two_lam)

        return (self.team_one_goals, self.team_two_goals)
    
    def __str__(self):
        return f"{self.team_one.name} scored {self.team_one_goals} goals, {self.team_two.name} scored {self.team_two_goals} goals."



class Bracket(object):
    def __init__(self, teams, games, historical_matches, ranks):
        self.teams = teams
        self.games = games
        self.historical_matches = historical_matches
        self.ranks = ranks
    
    def group_play(self):
        initial_team_ids = []
        self.teams_list = []
        for stage in self.games[:3]:
            for game in stage["tournaments"]:
                home_team_id = game["homeSquadId"]
                away_team_id = game["awaySquadId"]
                
                if home_team_id not in initial_team_ids:
                    initial_team_ids.append(home_team_id)
                    team_data = next((item for item in self.teams if item["id"] == home_team_id), None)
                    past_matches = self.historical_matches[self.historical_matches["Team"] == team_data["name"]]
                    rank_row = self.ranks[self.ranks["team_name"] == team_data["name"]]["rank"]
                    rank = rank_row.values[0]
                    home_team = Team(team_data['name'], team_data['group'], home_team_id, 0, 0, 0, rank, past_matches)
                    self.teams_list.append(home_team)
                else:
                    home_team = next((obj for obj in self.teams_list if obj.id == home_team_id), None)
                
                if away_team_id not in initial_team_ids:
                    initial_team_ids.append(away_team_id)
                    team_data = next((item for item in self.teams if item["id"] == away_team_id), None)
                    past_matches = self.historical_matches[self.historical_matches["Team"] == team_data["name"]]
                    rank_row = self.ranks[self.ranks["team_name"] == team_data["name"]]["rank"]
                    rank = rank_row.values[0]
                    away_team = Team(team_data['name'], team_data['group'], away_team_id, 0, 0, 0, rank, past_matches)
                    self.teams_list.append(away_team)
                else:
                    away_team = next((obj for obj in self.teams_list if obj.id == away_team_id), None)

                match = Match(home_team, away_team)
                homeGoals, awayGoals = match.calc_score()
                game["homeScore"] = homeGoals
                game["awayScore"] = awayGoals
                home_team.goals_for += homeGoals
                home_team.goals_against += awayGoals
                away_team.goals_for += awayGoals
                away_team.goals_against += homeGoals

                if homeGoals > awayGoals:
                    home_team.points += 3
                    game["winner"] = home_team.name
                elif homeGoals < awayGoals:
                    away_team.points += 3
                    game["winner"] = away_team.name
                else:
                    home_team.points += 1
                    away_team.points += 1
                
                print(match)
        
        return self.teams_list, self.games
    
    def commissioner(self):
        groups = set([team.group for team in self.teams_list])
        sorted_groups = sorted(groups)
        grouped_teams = {group: [team for team in self.teams_list if team.group == group] for group in sorted_groups}

        top_32 = {}
        gd_combs = {}
        gf_combs = {}
        bottom_12 = []
        for sort_group in grouped_teams:
            grouped_teams[sort_group] = sorted(grouped_teams[sort_group], key=lambda team: (team.points), reverse=True)
            
            combs = list(combinations(grouped_teams[sort_group], 2))
            i = 0
            gf_list = []
            for game in combs:
                gd_team1 = game[0].goals_for - game[0].goals_against
                gd_team2 = game[1].goals_for - game[1].goals_against
                if gd_team1 > gd_team2:
                    combs[i] = (game, game[0])
                    i+=1
                elif gd_team1 < gd_team2:
                    combs[i] = (game, game[1])
                    i+=1
                else:
                    combs[i] = (game, "tied")
                    i+=1
                    
                gd_combs[sort_group] = combs
                gf_list.append(((game[0], game[1]), (game[0].goals_for, game[1].goals_for)))
                gf_combs[sort_group] = gf_list
            
            # should go through every group and ensure that even the ties are ordered based off of goal_diff and goals_for characteristics
            group_points_list = [team.points for team in grouped_teams[sort_group]]
            points_count = Counter(group_points_list)
            for num in points_count:
                count = points_count[num]
                if count > 1:
                    tied_teams = [team for team in grouped_teams[sort_group] if team.points == num]
                    tied_combs = list(combinations(tied_teams, 2))
                else:
                    continue
                
                
                for game in gd_combs[sort_group]:
                    for tied_comb in tied_combs:
                        if ((tied_comb[0], tied_comb[1]) == game[0]):
                            tiebreaker1 = game[1]
                            gf_tie_game = [game_list for game_list in gf_combs[sort_group] if game_list[0] == (tied_comb[0], tied_comb[1])][0]
                            max_index = [i for i in range(len(gf_tie_game[1])) if max(gf_tie_game[1]) == gf_tie_game[1][i]]
                            if len(max_index) == 1: tiebreaker2 = gf_tie_game[0][max_index[0]]
                        elif ((tied_comb[1], tied_comb[0]) == game[0]):
                            tiebreaker1 = game[1]
                            gf_tie_game = [game_list for game_list in gf_combs[sort_group] if game_list[0] == (tied_comb[1], tied_comb[0])][0]
                            max_index = [i for i in range(len(gf_tie_game[1])) if max(gf_tie_game[1]) == gf_tie_game[1][i]]
                            if len(max_index) == 1: tiebreaker2 = gf_tie_game[0][max_index]
                        else:
                            continue

                        if tiebreaker1 != "tied":
                            other_team = [team for team in tied_comb if team != tiebreaker1][0]
                            tb1_index = grouped_teams[sort_group].index(tiebreaker1)
                            ot_index = grouped_teams[sort_group].index(other_team)
                            if tb1_index > ot_index:
                                grouped_teams[sort_group][tb1_index], grouped_teams[sort_group][ot_index] = grouped_teams[sort_group][ot_index], grouped_teams[sort_group][tb1_index]
                        else:
                            other_team = [team for team in tied_comb if team != tiebreaker2][0]
                            tb2_index = grouped_teams[sort_group].index(tiebreaker2)
                            ot_index = grouped_teams[sort_group].index(other_team)
                            if tb2_index > ot_index:
                                grouped_teams[sort_group][tb2_index], grouped_teams[sort_group][ot_index] = grouped_teams[sort_group][ot_index], grouped_teams[sort_group][tb2_index]

            top_32[sort_group] = grouped_teams[sort_group][:3]
            bottom_12.append(top_32[sort_group][2])

        sorted_bottom_12 = sorted(bottom_12, key=lambda team: (team.points, team.goals_for - team.goals_against, team.goals_for), reverse=True)
        delete_teams = sorted_bottom_12[8:]
        for group in top_32:
            team_3 = top_32[group][2]
            if team_3 in delete_teams:
                top_32[group].remove(team_3)
            else:
                continue

        return grouped_teams, top_32

    
    def round_32(self, top_32):
        top_16 = {
            0: ["1e", "3a/3b/3c/3d/3f"],
            1: ["1i", "3c/3d/3f/3g/3h"],
            2: ["2a", "2b"],
            3: ["1f", "2c"],
            4: ["2k", "2l"],
            5: ["1h", "2j"],
            6: ["1d", "3b/3e/3f/3i/3j"],
            7: ["1g", "3a/3e/3h/3i/3j"],
            8: ["1c", "2f"],
            9: ["2e", "2i"],
            10: ["1a", "3c/3e/3f/3h/3i"],
            11: ["1l", "3e/3h/3i/3j/3k"],
            12: ["1j", "2h"],
            13: ["2d", "2g"],
            14: ["1b", "3e/3f/3g/3i/3j"],
            15: ["1k", "3d/3e/3i/3j/3l"]
        }
        for game_num in top_16:
            for rank in top_16[game_num]:
                if len(rank) == 2:
                    print()
                else:
                    print()


                


world_cup = Bracket(team_data, games_data, historical_matches_data, rank_data)

post_gs_teams, post_gs_games = world_cup.group_play()

gt, top_32 = world_cup.commissioner()
for group in top_32:
    print(f"\nGROUP {group.upper()} STANDINGS")
    for team in top_32[group]:
        print(team)








""" Extra Code """
# if len(top_teams) == 1:
#     top_24[sort_group] = [(1, top_teams[0])]
#     for team in top_teams:
#         grouped_teams[sort_group].remove(team)
# elif len(top_teams) == 2:
#     top_24[sort_group] = top_teams
#     for team in top_teams:
#         grouped_teams[sort_group].remove(team)
# elif len(top_teams) == 3:

# top_2_group = grouped_teams[sort_group][:1]
# if top_2_group[0].points != top_2_group[1].points
#     top_24[sort_group] = top_2_group
#     grouped_teams[sort_group].pop(top_2_group[0])
#     grouped_teams[sort_group].pop(top_2_group[1])
# else:

# , team.goals_for - team.goals_against, team.goals_for
# max_points = max([team.points for team in grouped_teams[sort_group]])
# top_teams = [team for team in grouped_teams[sort_group] if team.points == max_points]

# gf_combs[sort_group] = [(team.name, team.goals_for) for team in grouped_teams[sort_group]]