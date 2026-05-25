import pandas as pd

dates_list = ["20250403", "20250710", "20250918", "20251017", "20251119", "20251222", "20260119"]

for date in dates_list:
    file_string = "/Users/nickbourgeois/Documents/python/world-cup-tournament-challenge/data/" + date + "_fifa_rankings.csv"
    df = pd.read_csv(file_string)
    df = df.iloc[:211, :]
    df.to_csv(file_string, index=False)
