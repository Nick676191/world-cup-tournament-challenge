import pandas as pd
import datetime as dt

dates = ["20250403", "20250710", "20250918", "20251017", "20251119", "20251222", "20260119"]
datetime_list = pd.to_datetime(dates)
df_str_one = "/Users/nickbourgeois/Documents/python/world-cup-tournament-challenge/data/"
df_str_two = "_fifa_rankings.csv"
dates_dfs = {date: pd.read_csv(df_str_one + date + df_str_two) for date in dates}


team_schedules = pd.read_csv(r"/Users/nickbourgeois/Documents/python/world-cup-tournament-challenge/data/team_schedules.csv")

rank_str = "/Users/nickbourgeois/Documents/python/world-cup-tournament-challenge/data/" + str(dates[0]) + "_fifa_rankings.csv"
ranked_df = pd.read_csv(rank_str)

# changing date columns to datetimes
team_schedules["Date"] = pd.to_datetime(team_schedules["Date"])
# team name preprocessing
team_schedules['Opponent'] = team_schedules['Opponent'].replace(
    {'United States': 'USA', 
     'N. Macedonia': 'North Macedonia',
     'UAE': 'United Arab Emirates',
     'Trin & Tobago': 'Trinidad and Tobago',
     'Gambia': 'The Gambia',
     'Rep. of Ireland': 'Republic of Ireland',
     'Bosnia-Herzegovina': 'Bosnia and Herzegovina',
     'Equ. Guinea': 'Equatorial Guinea',
     'Cape Verde': 'Cabo Verde',
     'St. Lucia': 'St Lucia',
     'São Tomé': 'São Tomé and Príncipe',
     'Dominican Rep.': 'Dominican Republic'
     })
# remove 'CAR' and 'Guadeloupe' as I can't find any ranks for these teams and they make up 0.5% of the rows of the data
team_schedules = team_schedules[team_schedules["Opponent"] != "CAR"].reset_index(drop=True)
team_schedules = team_schedules[team_schedules["Opponent"] != "Guadeloupe"].reset_index(drop=True)

# removing any parentheses from goals columns
def only_goals(x):
    return x[0]

team_schedules["GF"] = team_schedules["GF"].apply(lambda x: only_goals(x))
team_schedules["GA"] = team_schedules["GA"].apply(lambda x: only_goals(x))

def findRank(df_dict, team_df, date_num, keys, index):
    rank_df = df_dict[keys[date_num]]
    matching_row = rank_df[rank_df["team_name"] == team_df["Opponent"][index]]
    opp_rank = matching_row["rank"]
    # if len(opp_rank) == 0:
    #     return 999
    # if len(opp_rank) > 1:
    #     return 9999

    return opp_rank.values[0]

ranks = []
dict_keys = list(dates_dfs.keys())
for i in range(len(team_schedules)):
    if team_schedules["Date"][i] < datetime_list[0]:
        val = findRank(dates_dfs, team_schedules, 0, dict_keys, i)
        ranks.append(val)
    elif datetime_list[0] <= team_schedules["Date"][i] < datetime_list[1]:
        val = findRank(dates_dfs, team_schedules, 0, dict_keys, i)
        ranks.append(val)
    elif datetime_list[1] <= team_schedules["Date"][i] < datetime_list[2]:
        val = findRank(dates_dfs, team_schedules, 1, dict_keys, i)
        ranks.append(val)
    elif datetime_list[2] <= team_schedules["Date"][i] < datetime_list[3]:
        val = findRank(dates_dfs, team_schedules, 2, dict_keys, i)
        ranks.append(val)
    elif datetime_list[3] <= team_schedules["Date"][i] < datetime_list[4]:
        val = findRank(dates_dfs, team_schedules, 3, dict_keys, i)
        ranks.append(val)
    elif datetime_list[4] <= team_schedules["Date"][i] < datetime_list[5]:
        val = findRank(dates_dfs, team_schedules, 4, dict_keys, i)
        ranks.append(val)
    elif datetime_list[5] <= team_schedules["Date"][i] < datetime_list[6]:
        val = findRank(dates_dfs, team_schedules, 5, dict_keys, i)
        ranks.append(val)
    else:
        val = findRank(dates_dfs, team_schedules, 6, dict_keys, i)
        ranks.append(val)

team_schedules["Opp Rank"] = ranks
team_schedules = team_schedules.astype({"GF": "int", "GA": "int"})
team_schedules.to_csv("ranked_team_schedules.csv", index=False)

# zero_ranks = team_schedules[team_schedules["Opp Rank"] == 999]["Opponent"]
# mult_ranks = team_schedules[team_schedules["Opp Rank"] == 9999]["Opponent"]
# print(f"These {len(set(zero_ranks))} teams had no teams show up in their search:\n{set(zero_ranks)}\nThey make up {round((len(zero_ranks)/len(team_schedules))*100, 2)}% of the rows")
# print()
# print(f"These {len(set(mult_ranks))} teams had multiple teams show up in their search:\n{set(mult_ranks)}\nThey make up {round((len(mult_ranks)/len(team_schedules))*100, 2)}% of the rows")