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

moneylines = OpeningLines(e.ids(), nba.market_id('ml'), sb.id(BOOK))
pointspreads = OpeningLines(e.ids(), nba.market_id('ps'), sb.id(BOOK))
totals = OpeningLines(e.ids(), nba.market_id('total'), sb.id(BOOK))

ps = pointspreads.dataframe(e).rename(columns={'spread / total': 'spread'})
ml = moneylines.dataframe(e).rename(columns={'american odds': 'moneyline'})
to = totals.dataframe(e).rename(columns={'spread / total': 'total'})

pss = ps.loc[:, ['participant full name', 'spread']]
mls = ml.loc[:, ['participant full name', 'moneyline']]
tos = to.loc[:, ['participant full name', 'total']]


corrections = {
    "L.A. Clippers Clippers": "L.A. Clippers",
    "L.A. Lakers Lakers": "L.A. Lakers"
}

names = mls['participant full name'].tolist()
for index, name in enumerate(names):
    if name in corrections:
        names[index] = corrections[name]

data_frames = [pss, mls, tos]

for df in data_frames:
    df['participant full name'] = names

opponents = swap_pairs(names)

pregame_info = pd.DataFrame(data={
    'participant full name': names,
    'date': [DATE]*len(names),
    'opponent': opponents,
    'home': [i % 2 == 0 for i in range(len(names))],
    })


scores = ml['participant score'].tolist()

postgame_info = pd.DataFrame(data={
    'participant full name': names,
    'points scored': scores,
    'points allowed': swap_pairs(scores),
    'total points scored': [scores[i] + swap_pairs(scores)[i] for i in range(len(names))],
    'lost by': [swap_pairs(scores)[i] - scores[i] for i in range(len(scores))]
})


dfs_to_merge = [pregame_info, pss, mls, tos, postgame_info]

df_merged = reduce(lambda left,right: pd.merge(left,right,on=['participant full name'], how='outer'), dfs_to_merge)

results_df = pd.DataFrame(data={
    'participant full name': names,
    'spread result': ["win" if df_merged['lost by'][i] < df_merged['spread'][i] else "loss" if df_merged['lost by'][i] > df_merged['spread'][i] else "push" for i in range(len(names))],
    'moneyline result': ["win" if df_merged["points allowed"][i] < df_merged['points scored'][i] else 'loss' for i in range(len(names))],
    'total result': ["win" if df_merged['total points scored'][i] > df_merged['total'][i] else "loss" if df_merged['total points scored'][i] < df_merged['total'][i] else "push" for i in range(len(names))]
})

final_df = pd.merge(df_merged, results_df, on='participant full name')





import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    "../credentials.json", scope)
client = gspread.authorize(credentials)
sheet1 = client.open("NBA Bets").get_worksheet(3)

height = len(sheet1.col_values(1)) + 1

if height > 1: 
    A = False
else: 
    A = True

set_with_dataframe(sheet1, final_df, row=height, include_column_header=A)

print('done')