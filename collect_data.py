from turtle import home
from typing import Iterable, Type
from pysbr import * 
from datetime import datetime
import numpy as np
import requests
import pandas as pd


# -----------------------------------------------------------------------
# TeamBettingData class


def correct_names(arr):

    corrections = {
        "L.A. Clippers Clippers": "L.A. Clippers",
        "L.A. Lakers Lakers": "L.A. Lakers"
    }

    for index, team in enumerate(arr):
        if team in corrections:
            arr[index] = corrections[team]

    return arr


def swap_consec_pairs(arr: list):
    """
    Returns a copy of the passed list with all consecutive pairs
    interchanged.

    If the list has an odd length, the last element will remain in place.
    Other iterables can be passed (str, tuple, numpy array) but a list
    will be returned.

    Parameters
    ----------
    arr : list

    Examples
    ----------
    >>> my_list = ["A", "B", "C", "D"]
    >>> swap_consec_pairs(my_list)
    ["B", "A", "D", "C"]
    ----------
    >>> my_list = [1, 2, 3, 4, 5]
    >>> swap_consec_pairs(my_list)
    [2, 1, 4, 3, 5]
    """
    swapped = [None]*len(arr)

    if len(arr) % 2 == 0:
        swapped[::2] = arr[1::2]
        swapped[1::2] = arr[::2]
    elif len(arr) % 2 == 1:
        swapped[:len(arr)-1:2] = arr[1::2]
        swapped[1::2] = arr[:len(arr)-1:2]
        swapped[-1] = arr[-1]

    return swapped


class TeamBettingData:
    """
    Object that uses pySBR connection to grab NBA betting data from 
    SBR"s site. 
    
    Attributes contain lists of information to be used as 
    columns in pandas DataFrame.

    Parameters
    ----------
    date : str
        Necessary to include year, month, and day.  This 
        determines date of game data to be gathered.  If no games were 
        played on the given date, a Key Error is thrown.
    book : str
        Determines which sportsbook is queried (eg. "Bovada"). Refer to
        pySBR documentation for a list of possible values.  Invalid 
        sportsbook name will throw a Value Error from pySBR.
    """

    def __init__(self, date: str, book: str):
        """
        This works but admittedly, this is terrible. Need to find a 
        cleaner solution. Perhaps it'd be best to treat most of these as
        properties instead.
        """
        self.date = datetime.strptime(date, r"%Y-%m-%d")
        nba, sb = NBA(), Sportsbook()
        e = EventsByDate(nba.league_id, self.date)
        self.ps_df = OpeningLines(e.ids(), nba.market_id("ps"), sb.id(book)).dataframe(e)
        self.ml_df = OpeningLines(e.ids(), nba.market_id("ml"), sb.id(book)).dataframe(e)
        self.tot_df = OpeningLines(e.ids(), nba.market_id("total"), sb.id(book)).dataframe(e)
        events = self.ps_df["event"].tolist()
        self.home_teams = [events[i].split(" ")[-1] for i in range(len(events))]

    @property
    def participants(self):
        return correct_names(self.ps_df["participant full name"].tolist())

    @property
    def opponents(self):
        return swap_consec_pairs(self.participants)

    @property
    def home(self):
        return [self.home_teams[i] in self.participants[i] for i in range(len(self.home_teams))]

    @property
    def pointspreads(self):
        return self.ps_df["spread / total"].tolist()

    @property
    def moneylines(self):
        return self.ml_df["american odds"].tolist()

    @property
    def totals(self):
        return self.tot_df["spread / total"].tolist()

    @property
    def scores(self):
        return self.ps_df["participant score"].tolist()

    @property
    def points_allowed(self):
        return swap_consec_pairs(self.scores)

    @property
    def total_points_scored(self):
        return (np.array(self.scores) + np.array(self.points_allowed)).tolist()

    @property
    def lost_by(self):
        return (np.array(self.points_allowed) - np.array(self.scores)).tolist()

    @property
    def pointspread_win(self):
        return (np.array(self.points_allowed) - np.array(self.scores)
                < np.array(self.pointspreads)).tolist()

    @property
    def moneyline_win(self):
        return (np.array(self.scores) > np.array(self.points_allowed)).tolist()

    @property
    def total_over(self):
        return (np.array(self.total_points_scored) > np.array(self.totals)).tolist()

    def properties(self) -> dict:
        props = {
            "participants": self.participants,
            "date": self.date,
            "opponents": self.opponents,
            "home": self.home,
            "pointspreads": self.pointspreads,
            "moneylines": self.moneylines,
            "totals": self.totals,
            "scores": self.scores,
            "points_allowed": self.points_allowed,
            "total_points_scored": self.total_points_scored,
            "lost_by": self.lost_by,
            "pointspread_win": self.pointspread_win,
            "moneyline_win": self.moneyline_win,
            "total_over": self.total_over
        }
        return props


# -----------------------------------------------------------------------
# PlayerProps class


url_dict = {
    "College": "",
    "Conference": "",
    "Country": "",
    "DateFrom": "",
    "DateTo": "",
    "Division": "",
    "DraftPick": "",
    "DraftYear": "",
    "GameScope": "",
    "GameSegment": "",
    "Height": "",
    "LastNGames": "",
    "LeagueID": "00",
    "Location": "",
    "MeasureType": "Base",
    "Month": "0",
    "OpponentTeamID": "0",
    "Outcome": "",
    "PORound": "0",
    "PaceAdjust": "N",
    "PerMode": "PerGame",
    "Period": "0",
    "PlayerExperience": "",
    "PlayerPosition": "",
    "PlusMinus": "N",
    "Rank": "N",
    "Season": "2021-22",
    "SeasonSegment": "",
    "SeasonType": "Regular+Season",
    "ShotClockRange": "",
    "StarterBench": "",
    "TeamID": "0",
    "TwoWay": "0",
    "VsConference": "",
    "VsDivision": "",
    "Weight": ""
    }


class PlayerProps:

    def __init__(self, **kwargs):

        for key in kwargs:
            if key in url_dict:
                url_dict[key] = kwargs[key]
            else:
                print(f"{key} is not an option, it has been ignored.")

        url_start = 'https://stats.nba.com/stats/leaguedashplayerstats?'
        self.url = url_start + "&".join([key + "=" + url_dict[key] for key in url_dict])

        self.headers  = {
            "Connection": "keep-alive",
            "Accept": "application/json, text/plain, */*",
            "x-nba-stats-token": "true",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
            "x-nba-stats-origin": "stats",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Referer": "https://stats.nba.com/",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
        }
    

    def get_data(self):
        response = requests.get(self.url, headers=self.headers).json()
        stats = response["resultSets"][0]["rowSet"]
        col_names = response["resultSets"][0]["headers"]
        df = pd.DataFrame(stats, columns=col_names)
        reordered_df = df.loc[:, ["PLAYER_NAME", "PTS", "FG3M", "REB", "AST", "STL", "BLK"]]

        return reordered_df
        