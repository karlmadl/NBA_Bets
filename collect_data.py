from pysbr import * 
from datetime import datetime



def correct_names(arr):

    corrections = {
        "L.A. Clippers Clippers": "L.A. Clippers",
        "L.A. Lakers Lakers": "L.A. Lakers"
    }

    for index, team in enumerate(arr):
        if team in corrections:
            arr[index] = corrections[team]

    return arr



class BettingData:
    """
    Object that uses pySBR connection to grab NBA betting data from SBR's site.
    Attributes contain lists of information to be used as columns in pandas DataFrame.

    Parameters
    ----------
    date : string. Necessary to include year, month, and day. This determines date of game data
    to be gathered. If no games were played on the given date, a Key Error is thrown.

    book : string. Determines which sportsbook is queried (eg. 'Bovada'). Refer to pySBR documentation for a list
    of possible values. Invalid sportsbook name will throw a Value Error from pySBR.
    """

    def __init__(self, date: str, book: str):

        self.date = datetime.strptime(date, r'%Y-%m-%d')
        nba, sb = NBA(), Sportsbook()

        e = EventsByDate(nba.league_id, self.date)

        pointspreads = OpeningLines(e.ids(), nba.market_id('ps'), sb.id(book)).dataframe(e)
        
        
        self.pointspreads = pointspreads['spread / total'].tolist()
        
        self.moneylines = OpeningLines(e.ids(), nba.market_id('ml'), sb.id(book)).dataframe(e)['american odds'].tolist()

        self.totals = OpeningLines(e.ids(), nba.market_id('total'), sb.id(book)).dataframe(e)['spread / total'].tolist()

        self.participants = correct_names(pointspreads['participant full name'].tolist())

        self.events = pointspreads['event'].tolist()

        self.scores = pointspreads['participant score'].tolist()

        self.home_teams = [self.events[i].split(" ")[-1] for i in range(len(self.events))]     