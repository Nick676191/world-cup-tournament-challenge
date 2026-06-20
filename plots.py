import json
import string
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

first_file_path = "/Users/nickbourgeois/Documents/python/world-cup-tournament-challenge/data/winner_data.json"
second_file_path = "/Users/nickbourgeois/Documents/python/world-cup-tournament-challenge/data/group_positions.json"

with open(first_file_path, "r") as first_file:
    winner_results = json.load(first_file)

with open (second_file_path, "r") as second_file:
    group_positions = json.load(second_file)


# first plot of the winners of the world cup sim
countries = [cat[0] for cat in winner_results]
percentages = [per[1] for per in winner_results]

fig, ax = plt.subplots()
bars = ax.bar(countries[:10], percentages[:10])
ax.bar_label(bars, padding=2, fmt="%.3f", fontsize=7)

ax.set_title("Projected Winners of the World Cup")
ax.set_xlabel("Countries")
ax.set_ylabel("Proportion")
ax.tick_params(axis="x", rotation=45, labelsize=8)
plt.show()


# second plot of the projected winners of each group
group_letters = [letter for letter, num in zip(string.ascii_uppercase, range(12))]
def axis_assigner(num):
    if num < 4:
        row = 0
        col = num
    elif 4 <= num < 8:
        row = 1
        col = num - 4
    else:
        row = 2
        col = num - 8
    
    return (row, col)

fig, axs = plt.subplots(nrows=3, ncols=4, sharey=True, figsize=(8, 6))
for group, num in zip(group_letters, range(len(group_letters))):
    row, col = axis_assigner(num)
    countries = [cat[0] for cat in group_positions[group][0]]
    percentages = [per[1] for per in group_positions[group][0]]
    if "Bosnia and Herzegovina" in countries:
        bosnia_id = countries.index("Bosnia and Herzegovina")
        countries[bosnia_id] = "Bosnia"
    if "Korea Republic" in countries:
        korea_id = countries.index("Korea Republic")
        countries[korea_id] = "Korea"
    bars = axs[row, col].bar(countries, percentages)
    axs[row, col].bar_label(bars, padding=2, fmt="%.2f", fontsize=6)
    axs[row, col].tick_params(axis="x", rotation=45, labelsize=8)
    axs[row, col].set_title(f"Group {group}")

# ensuring that y axis is from 0 to 1
y_setter = axs[0, 0]
y_setter.set_ylim(0, 1)
y_setter.set_yticks(np.arange(0.25, 1, 0.25))

fig.subplots_adjust(hspace=1)
fig.suptitle("Projected Group Winners")
fig.supylabel("Proportion")
plt.show()

# third plot to show the second place teams
fig, axs = plt.subplots(nrows=3, ncols=4, sharey=True, figsize=(8, 6))
for group, num in zip(group_letters, range(len(group_letters))):
    row, col = axis_assigner(num)
    countries = [cat[0] for cat in group_positions[group][1]]
    percentages = [per[1] for per in group_positions[group][1]]
    if "Bosnia and Herzegovina" in countries:
        bosnia_id = countries.index("Bosnia and Herzegovina")
        countries[bosnia_id] = "Bosnia"
    if "Korea Republic" in countries:
        korea_id = countries.index("Korea Republic")
        countries[korea_id] = "Korea"
    bars = axs[row, col].bar(countries, percentages)
    axs[row, col].bar_label(bars, padding=2, fmt="%.2f", fontsize=6)
    axs[row, col].tick_params(axis="x", rotation=45, labelsize=8)
    axs[row, col].set_title(f"Group {group}")

# ensuring that y axis is from 0 to 1
y_setter = axs[0, 0]
y_setter.set_ylim(0, 1)
y_setter.set_yticks(np.arange(0.25, 1, 0.25))

fig.subplots_adjust(hspace=1)
fig.suptitle("Projected Second Place Team per Group")
fig.supylabel("Proportion")
plt.show()