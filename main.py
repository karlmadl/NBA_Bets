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
CURRENT_DATE = '2021-03-11' # yesterday = str(date.today() - timedelta(days=1))

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
    'date': [CURRENT_DATE]*len(names),
    'opponent': opponents,
    'home': [i % 2 == 0 for i in range(len(names))],
    })


scores = ml['participant score'].tolist()

postgame_info = pd.DataFrame(data={
    'participant full name': names,
    'points scored': scores,
    'points allowed': swap_pairs(scores),
    'total points scored': [scores[i] + swap_pairs(scores)[i] for i in range(len(names))]
})


dfs_to_merge = [pregame_info, pss, mls, tos, postgame_info]

df_merged = reduce(lambda left,right: pd.merge(left,right,on=['participant full name'], how='outer'), dfs_to_merge)

print(df_merged)



# ps_result, ml_result, to_result = [], [], []
# for i in range(len(df_merged)):
#     if df_merged['points allowed'][i] - df_merged['points scored'][i] > df_merged['spread'][i]:
#         ps_result.append('loss')
#     elif df_merged['points allowed'][i] - df_merged['points scored'][i] < df_merged['spread'][i]:
#         ps_result.append('win')
#     elif df_merged['points allowed'][i] - df_merged['points scored'][i] == df_merged['spread'][i]:
#         ps_result.append('push')

#     if df_merged['points allowed'][i] > df_merged['points scored'][i]:
#         ml_result.append('loss')
#     elif df_merged['points allowed'][i] < df_merged['points scored'][i]:
#         ml_result.append('win')

#     if df_merged['total points scored'][i] < df_merged['total'][i]:
#         to_result.append('loss')
#     elif df_merged['total points scored'][i] > df_merged['total'][i]:
#         to_result.append('win')
#     elif df_merged['total points scored'][i] == df_merged['total'][i]:
#         to_result.append('push')

# df_merged['spread result'], df_merged['moneyline result'], df_merged['total result'] = ps_result, ml_result, to_result

# print(df_merged)