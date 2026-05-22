import numpy as np
from scraper import scrapy

# grabbing the world cup teams and games from the scraper object
team_url = "https://play.fifa.com/json/bracket_predictor/squads.json"
team_data = scrapy(team_url).findData()

games_url = "https://play.fifa.com/json/bracket_predictor/rounds.json"
games_data = scrapy(games_url).findData()

class Team(object):
    def __init__(self, def_stats, off_stats, name, group, id, points):
        self.def_stats = def_stats
        self.off_stats = off_stats
        self.name = name
        self.group = group
        self.id = id
        self.points = points
    
    def __str__(self):
        return f"{self.name} finished in group {self.group} with {self.points} points."



class Match(object):
    def __init__(self, team_one, team_two):
        self.team_one = team_one
        self.team_two = team_two
        
    def calc_score(self):
        self.team_one_goals = self.team_one.off_stats - self.team_two.def_stats
        self.team_two_goals = self.team_two.off_stats - self.team_one.def_stats

        return (self.team_one_goals, self.team_two_goals)



class Bracket(object):
    def __init__(self, teams, games):
        self.teams = teams
        self.games = games
    
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
                    home_team = Team(np.random.rand(), np.random.rand()*3, team_data['abbr'], team_data['group'], home_team_id, 0)
                    self.teams_list.append(home_team)
                else:
                    home_team = next((obj for obj in self.teams_list if obj.id == home_team_id), None)
                
                if away_team_id not in initial_team_ids:
                    initial_team_ids.append(away_team_id)
                    team_data = next((item for item in self.teams if item["id"] == away_team_id), None)
                    away_team = Team(np.random.rand(), np.random.rand()*3, team_data['abbr'], team_data['group'], away_team_id, 0)
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
        
        return self.teams_list, self.games

                


world_cup = Bracket(team_data, games_data)

post_gs_teams, post_gs_games = world_cup.group_play()
print(post_gs_teams[0])
print()
print()
print(post_gs_games)






# mexico = Team(1, 2, team_data[0]['abbr'], team_data[0]['group'], team_data[0]['id'], 0)
# korea = Team(0, 2, team_data[1]['abbr'], team_data[1]['group'], team_data[1]['id'], 0)

# gameOne = Match(mexico, korea)

# mexicoGoals, koreaGoals = gameOne.calc_score()

# print(mexicoGoals, koreaGoals)

# print(games_data[0]['tournaments'][0])