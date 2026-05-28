import pandas as pd
import datetime as dt

dates = ["20250403", "20250710", "20250918", "20251017", "20251119", "20251222", "20260119"]
datetime_list = pd.to_datetime(dates)
df_str_one = "/Users/nickbourgeois/Documents/python/world-cup-tournament-challenge/data/"
df_str_two = "_fifa_rankings.csv"
dates_dfs = {date: pd.read_csv(df_str_one + date + df_str_two) for date in dates}


team_schedules = pd.read_csv(r"/Users/nickbourgeois/Documents/python/world-cup-tournament-challenge/data/team_schedules.csv")
# team_schedules = team_schedules.head()

rank_str = "/Users/nickbourgeois/Documents/python/world-cup-tournament-challenge/data/" + str(dates[0]) + "_fifa_rankings.csv"
ranked_df = pd.read_csv(rank_str)

# changing date columns to datetimes
team_schedules["Date"] = pd.to_datetime(team_schedules["Date"])
# tester_df["Date"] = pd.to_datetime(tester_df["Date"])
# print(tester_df)

def findRank(df_dict, team_df, date_num, keys, index):
    rank_df = df_dict[keys[date_num]]
    matching_row = rank_df[rank_df["team_name"].str.contains(team_df["Opponent"][index], case=False, na=False)]
    opp_rank = matching_row["rank"]
    if len(opp_rank) != 1:
        return 999

    return opp_rank.values[0]

ranks = []
dict_keys = list(dates_dfs.keys())
for i in range(len(team_schedules)):
    if team_schedules["Date"][i] <= datetime_list[0]:
        val = findRank(dates_dfs, team_schedules, 0, dict_keys, i)
        ranks.append(val)
    elif datetime_list[0] < team_schedules["Date"][i] <= datetime_list[1]:
        val = findRank(dates_dfs, team_schedules, 1, dict_keys, i)
        ranks.append(val)
    elif datetime_list[1] < team_schedules["Date"][i] <= datetime_list[2]:
        val = findRank(dates_dfs, team_schedules, 2, dict_keys, i)
        ranks.append(val)
    elif datetime_list[2] < team_schedules["Date"][i] <= datetime_list[3]:
        val = findRank(dates_dfs, team_schedules, 3, dict_keys, i)
        ranks.append(val)
    elif datetime_list[3] < team_schedules["Date"][i] <= datetime_list[4]:
        val = findRank(dates_dfs, team_schedules, 4, dict_keys, i)
        ranks.append(val)
    elif datetime_list[4] < team_schedules["Date"][i] <= datetime_list[5]:
        val = findRank(dates_dfs, team_schedules, 5, dict_keys, i)
        ranks.append(val)
    else:
        val = findRank(dates_dfs, team_schedules, 6, dict_keys, i)
        ranks.append(val)

team_schedules["Opp Rank"] = ranks
print(team_schedules)

bad_ranks = team_schedules[team_schedules["Opp Rank"] == 999]
print(f"These {len(set(bad_ranks["Opponent"]))} countries have been given an unknown rank value:\n{set(bad_ranks["Opponent"])}\nThey are in {len(bad_ranks)} rows of {len(team_schedules)}")