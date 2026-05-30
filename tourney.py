import numpy as np
import pandas as pd
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
    def __init__(self, name, group, id, points, world_rank, historical_games):
        self.name = name
        self.group = group
        self.id = id
        self.points = points
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
        return f"{self.name} finished in group {self.group} with {self.points} points."



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
                    home_team = Team(team_data['name'], team_data['group'], home_team_id, 0, rank, past_matches)
                    self.teams_list.append(home_team)
                else:
                    home_team = next((obj for obj in self.teams_list if obj.id == home_team_id), None)
                
                if away_team_id not in initial_team_ids:
                    initial_team_ids.append(away_team_id)
                    team_data = next((item for item in self.teams if item["id"] == away_team_id), None)
                    past_matches = self.historical_matches[self.historical_matches["Team"] == team_data["name"]]
                    rank_row = self.ranks[self.ranks["team_name"] == team_data["name"]]["rank"]
                    rank = rank_row.values[0]
                    away_team = Team(team_data['name'], team_data['group'], away_team_id, 0, rank, past_matches)
                    self.teams_list.append(away_team)
                else:
                    away_team = next((obj for obj in self.teams_list if obj.id == away_team_id), None)

                match = Match(home_team, away_team)
                homeGoals, awayGoals = match.calc_score()
                game["homeScore"] = homeGoals
                game["awayScore"] = awayGoals

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

                


world_cup = Bracket(team_data, games_data, historical_matches_data, rank_data)

post_gs_teams, post_gs_games = world_cup.group_play()