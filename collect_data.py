from turtle import home
from typing import Type
from pysbr import * 
from datetime import datetime, timedelta, date
import numpy as np
import requests
import pandas as pd



def correct_names(arr):

    corrections = {
        "L.A. Clippers Clippers": "L.A. Clippers",
        "L.A. Lakers Lakers": "L.A. Lakers"
    }

    for index, team in enumerate(arr):
        if team in corrections:
            arr[index] = corrections[team]

    return arr


def swap_consec_pairs(arr):
    swapped = [None]*len(arr)
    swapped[::2], swapped[1::2] = arr[1::2], arr[::2]

    return swapped



class BettingData:
    """
    Object that uses pySBR connection to grab NBA betting data from 
    SBR's site. 
    
    Attributes contain lists of information to be used as 
    columns in pandas DataFrame.

    Parameters
    ----------
    date : str
        Necessary to include year, month, and day.  This 
        determines date of game data to be gathered.  If no games were 
        played on the given date, a Key Error is thrown.
    book : str
        Determines which sportsbook is queried (eg. 'Bovada'). Refer to
        pySBR documentation for a list of possible values.  Invalid 
        sportsbook name will throw a Value Error from pySBR.
    """

    def __init__(self, date: str, book: str):
        date = datetime.strptime(date, r'%Y-%m-%d')
        nba, sb = NBA(), Sportsbook()
        e = EventsByDate(nba.league_id, date)
        pointspreads = OpeningLines(e.ids(), nba.market_id('ps'), sb.id(book)).dataframe(e)
        events = pointspreads['event'].tolist()
        home_teams = [events[i].split(" ")[-1] for i in range(len(events))]


        self.participants = correct_names(pointspreads['participant full name'].tolist())

        self.date = date

        self.opponents = swap_consec_pairs(self.participants)

        self.home = [home_teams[i] in self.participants[i] for i in range(len(home_teams))]

        self.pointspreads = pointspreads['spread / total'].tolist()

        self.moneylines = OpeningLines(e.ids(), nba.market_id('ml'), sb.id(book)).dataframe(e)['american odds'].tolist()

        self.totals = OpeningLines(e.ids(), nba.market_id('total'), sb.id(book)).dataframe(e)['spread / total'].tolist()

        self.scores = pointspreads['participant score'].tolist()

        self.points_allowed = swap_consec_pairs(self.scores)

        self.total_points_scored = (np.array(self.scores) + np.array(self.points_allowed)).tolist()

        self.lost_by = (np.array(self.points_allowed) - np.array(self.scores)).tolist()

        self.pointspread_win = (np.array(self.points_allowed) - np.array(self.scores) < np.array(self.pointspreads)).tolist()

        self.moneyline_win = (np.array(self.scores) > np.array(self.points_allowed)).tolist()

        self.totals_over = (np.array(self.total_points_scored) > np.array(self.totals)).tolist()


class PlayerProps:

    def __init__(self, last_n_days: int = None, last_n_games: int = None):

        if last_n_days is not None and last_n_games is not None:
            raise TypeError("PlayerProps should only be passed one argument")
        elif last_n_games is not None:
            self.url = f"https://stats.nba.com/stats/leaguedashplayerstats?College=&Conference=&Country=&DateFrom=&DateTo=&Division=&DraftPick=&DraftYear=&GameScope=&GameSegment=&Height=&LastNGames={last_n_games}&LeagueID=00&Location=&MeasureType=Base&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PaceAdjust=N&PerMode=PerGame&Period=0&PlayerExperience=&PlayerPosition=&PlusMinus=N&Rank=N&Season=2021-22&SeasonSegment=&SeasonType=Regular+Season&ShotClockRange=&StarterBench=&TeamID=0&TwoWay=0&VsConference=&VsDivision=&Weight="
        elif last_n_days is not None:
            self.url = f"https://stats.nba.com/stats/leaguedashplayerstats?College=&Conference=&Country=&DateFrom={(date.today() - timedelta(days=last_n_days)).strftime(r'%m')}%2F{(date.today() - timedelta(days=last_n_days)).strftime(r'%d')}%2F{(date.today() - timedelta(days=last_n_days)).strftime(r'%Y')}&DateTo={date.today().strftime(r'%m')}%2F{date.today().strftime(r'%d')}%2F{date.today().strftime(r'%Y')}&Division=&DraftPick=&DraftYear=&GameScope=&GameSegment=&Height=&LastNGames=0&LeagueID=00&Location=&MeasureType=Base&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PaceAdjust=N&PerMode=PerGame&Period=0&PlayerExperience=&PlayerPosition=&PlusMinus=N&Rank=N&Season=2021-22&SeasonSegment=&SeasonType=Regular+Season&ShotClockRange=&StarterBench=&TeamID=0&TwoWay=0&VsConference=&VsDivision=&Weight="
        else:
            raise TypeError("PlayerProps should be passed one argument")

        self.headers  = {
            'Connection': 'keep-alive',
            'Accept': 'application/json, text/plain, */*',
            'x-nba-stats-token': 'true',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
            'x-nba-stats-origin': 'stats',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Referer': 'https://stats.nba.com/',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    

    def get_data(self):
        response = requests.get(self.url, headers=self.headers).json()
        stats = response['resultSets'][0]['rowSet']
        col_names = response['resultSets'][0]['headers']
        df = pd.DataFrame(stats, columns=col_names)
        reordered_df = df.loc[:, ["PLAYER_NAME", "PTS", "FG3M", "REB", "AST", "STL", "BLK"]]

        return reordered_df
        