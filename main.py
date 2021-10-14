from pysbr import * 
from datetime import datetime, date, timedelta
import pandas as pd
from functools import reduce


def swap_pairs(ls):
    swapped_pairs = [None]*len(ls)
    swapped_pairs[::2] = ls[1::2]
    swapped_pairs[1::2] = ls[::2]

    return swapped_pairs


BOOK = 'Bovada'
DATE = str(date.today() - timedelta(days=1))

dt = datetime.strptime(DATE, '%Y-%m-%d')
nba = NBA()
sb = Sportsbook() 

e = EventsByDate(nba.league_id, dt)

moneylines = OpeningLines(e.ids(), nba.market_id('ml'), sb.id(BOOK)).dataframe(e)
pointspreads = OpeningLines(e.ids(), nba.market_id('ps'), sb.id(BOOK)).dataframe(e)
totals = OpeningLines(e.ids(), nba.market_id('total'), sb.id(BOOK)).dataframe(e)

pointspreads.rename(columns={'spread / total': 'spread'}, inplace=True)
moneylines.rename(columns={'american odds': 'moneyline'}, inplace=True)
totals.rename(columns={'spread / total': 'total'}, inplace=True)

corrections = {
    "L.A. Clippers Clippers": "L.A. Clippers",
    "L.A. Lakers Lakers": "L.A. Lakers"
}

names = moneylines['participant full name'].tolist()
for index, name in enumerate(names):
    if name in corrections:
        names[index] = corrections[name]

events = moneylines['event'].tolist()
home_teams = [events[i].split(" ")[-1] for i in range(len(events))]





pregame_info = pd.DataFrame(data={
    'participant full name': names,
    'date': [DATE]*len(names),
    'opponent': swap_pairs(names),
    'home': [home_teams[i] == names[i].split(" ")[1] for i in range(len(names))],
    })


pointspreads_to_merge = pointspreads.loc[:, ['participant full name', 'spread']]
moneylines_to_merge = moneylines.loc[:, ['participant full name', 'moneyline']]
totals_to_merge = totals.loc[:, ['participant full name', 'total']]


scores = moneylines['participant score'].tolist()
postgame_info = pd.DataFrame(data={
    'participant full name': names,
    'points scored': scores,
    'points allowed': swap_pairs(scores),
    'total points scored': [scores[i] + swap_pairs(scores)[i] for i in range(len(names))],
    'lost by': [swap_pairs(scores)[i] - scores[i] for i in range(len(scores))]
})


results = pd.DataFrame(data={
    'participant full name': names,
    'spread result': ["win" if postgame_info['lost by'][i] < pointspreads_to_merge['spread'][i] else "loss" if postgame_info['lost by'][i] > pointspreads_to_merge['spread'][i] else "push" for i in range(len(names))],
    'moneyline result': ["win" if postgame_info["points allowed"][i] < postgame_info['points scored'][i] else 'loss' for i in range(len(names))],
    'total result': ["win" if postgame_info['total points scored'][i] > totals_to_merge['total'][i] else "loss" if postgame_info['total points scored'][i] < totals_to_merge['total'][i] else "push" for i in range(len(names))]
})



wrong_name_dfs = [pointspreads_to_merge, moneylines_to_merge, totals_to_merge]

for df in wrong_name_dfs:
    df['participant full name'] = names

dfs_to_merge = [pregame_info, pointspreads_to_merge, moneylines_to_merge, totals_to_merge, postgame_info, results]

final_df = reduce(lambda left,right: pd.merge(left,right,on=['participant full name'], how='outer'), dfs_to_merge)






import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(credentials)
sheet1 = client.open("NBA Bets 2021-22").get_worksheet(1)

height = len(sheet1.col_values(1)) + 1

if height > 1: 
    A = False
else: 
    A = True

set_with_dataframe(sheet1, final_df, row=height, include_column_header=A)

print('done')