import re
import pandas as pd

pd.set_option('display.max_columns', None)

data = """Date	Time	Comp	Round	Day	Venue	Result	GF	GA	Opponent	Poss	Attendance	Captain	Formation	Opp Formation	Referee	Match Report	Notes
2025-09-04	18:30 (16:30)	WCQ	Third round	Thu	Away	D	0	0	sr Suriname			Aníbal Godoy	4-2-3-1	5-4-1	Kwinsi Williams	Match Report	
2025-09-08	20:30	WCQ	Third round	Mon	Home	D	1	1	gt Guatemala			Aníbal Godoy	4-2-3-1	4-4-2	Said Martínez	Match Report	
2025-10-10	19:00 (20:00)	WCQ	Third round	Fri	Away	W	1	0	sv El Salvador			Erick Davis	5-4-1	5-3-2	Drew Fischer	Match Report	
2025-10-14	20:00	WCQ	Third round	Tue	Home	D	1	1	sr Suriname			Erick Davis	5-4-1	3-4-3	Selvin Brown	Match Report	
2025-11-13	20:00	WCQ	Third round	Thu	Away	W	3	2	gt Guatemala			Aníbal Godoy	5-4-1	4-3-3	César Arturo Ramos	Match Report	
2025-11-18	20:00 (19:00)	WCQ	Third round	Tue	Home	W	3	0	sv El Salvador			Aníbal Godoy	3-4-3	4-3-3	Said Martínez	Match Report	
2026-03-27	19:00 (12:00)	Friendlies (M)	Friendlies (M)	Fri	Away	D	1	1	za South Africa			Erick Davis	5-4-1	4-2-3-1	Thabang Ketshabile	Match Report	
2026-03-31	19:30 (12:30)	Friendlies (M)	Friendlies (M)	Tue	Away	W	2	1	za South Africa			Aníbal Godoy	3-4-3	4-2-3-1	Thabang Ketshabile	Match Report	
"""

def dfGenesis(dataString: str, teamName: str):
    # only splits on a tab or newline
    split_data = re.split(r'[\t\n]', dataString)
    initial_list = []
    new_list = []
    for i in range(len(split_data)):
        if (i+1)%18==0:
            new_list.append(initial_list)
            initial_list = []
        else:
            initial_list.append(split_data[i])

    columns = new_list.pop(0)
    df = pd.DataFrame(new_list, columns=columns)
    df = df.drop(columns=["Time", "Comp", "Round", "Day", "Venue", "Poss", "Attendance", "Captain", "Referee", "Match Report"])

    def getCountryName(x):
        vals = x.split()[1:]
        return " ".join(vals)
    df["Opponent"] = df["Opponent"].apply(lambda x: getCountryName(x))
    df.insert(4, "Team", [teamName for _ in range(len(df))])

    return df


new_df = dfGenesis(data, "Panama")

new_df.to_csv('team_schedules.csv', mode='a', index=False, header=False)