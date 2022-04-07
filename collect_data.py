from turtle import home
from pysbr import * 
from datetime import datetime
import numpy as np



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