from pysbr import * 
from datetime import datetime, date, timedelta
import pandas as pd
from functools import reduce
BOOK = 'Bovada'

CURRENT_DATE = '2021-03-11' # str(date.today())

dt = datetime.strptime(CURRENT_DATE, '%Y-%m-%d')

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

tos['participant full name'] = mls['participant full name'].tolist()
data_frames = [pss, mls, tos]

df_merged = reduce(lambda left,right: pd.merge(left,right,on=['participant full name'], how='outer'), data_frames)

corrections = {
    "L.A. Clippers Clippers": "L.A. Clippers",
    "L.A. Lakers Lakers": "L.A. Lakers"
}

names = df_merged['participant full name'].tolist()
for index, name in enumerate(names):
    if name in corrections:
        names[index] = corrections[name]

df_merged['participant full name'] = names

df_merged['home'] = [i % 2 == 0 for i in range(len(names))]

opponents = [None]*len(names)
opponents[::2] = names[1::2]
opponents[1::2] = names[::2]

df_merged['opponent'] = opponents

date_col = [CURRENT_DATE]*len(names)

df_merged['date'] = date_col

scores = ml['participant score'].tolist()

df_merged['points scored'] = scores
opp_scores = [None]*len(names)
opp_scores[::2] = scores[1::2]
opp_scores[1::2] = scores[::2]

df_merged['points allowed'] = opp_scores

df_merged['total points scored'] = [scores[i] + opp_scores[i] for i in range(len(names))]

df_merged = df_merged[['participant full name', 'date', 'opponent', 'home', 'spread', 'moneyline', 'total', 'points scored', 'points allowed', 'total points scored']]

ps_result = []
for i in range(len(df_merged)):
    if df_merged['points allowed'][i] - df_merged['points scored'][i] > df_merged['spread'][i]:
        ps_result.append('loss')
    elif df_merged['points allowed'][i] - df_merged['points scored'][i] < df_merged['spread'][i]:
        ps_result.append('win')
    elif df_merged['points allowed'][i] - df_merged['points scored'][i] == df_merged['spread'][i]:
        ps_result.append('push')

ml_result = []
for i in range(len(df_merged)):
    if df_merged['points allowed'][i] > df_merged['points scored'][i]:
        ml_result.append('loss')
    elif df_merged['points allowed'][i] < df_merged['points scored'][i]:
        ml_result.append('win')

to_result = []
for i in range(len(df_merged)):
    if df_merged['total points scored'][i] < df_merged['total'][i]:
        to_result.append('loss')
    elif df_merged['total points scored'][i] > df_merged['total'][i]:
        to_result.append('win')
    elif df_merged['total points scored'][i] == df_merged['total'][i]:
        to_result.append('push')

df_merged['spread result'], df_merged['moneyline result'], df_merged['total result'] = ps_result, ml_result, to_result

print(df_merged)