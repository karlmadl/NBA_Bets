from datetime import date, timedelta
import pandas as pd
import collect_data
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe


# returns a copy of the list argument with consecutive pairs 
# of elements swapped
def swap_pairs(ls):
    swapped_pairs = [None]*len(ls)
    swapped_pairs[::2] = ls[1::2]
    swapped_pairs[1::2] = ls[::2]

    return swapped_pairs





"""
Section One: Getting Data
"""


# get previous day's date, data collection is done
# one time the next morning to ensure all games are complete

DATE = str(date.today() - timedelta(days=1))



# specify which sportsbook is to be used, list of possibilities 
# can be found in pySBR docs 

BOOK = "Bovada"



# object that retrieves betting and game data

bet_data = collect_data.BettingData(date=DATE, book=BOOK)





"""
Section Two: Creating DataFrame with Data
"""


# create dataframe to upload using bet_data

df = pd.DataFrame(data={
    "team": bet_data.participants, 
    "date": [DATE]*len(bet_data.participants),
    "opponent": swap_pairs(bet_data.participants),

    # admittedly a funky line, uses the way teams are
    # listed in events to evaulate True or False
    "home": [bet_data.home_teams[i] == bet_data.participants[i].split(" ")[1] for i in range(len(bet_data.participants))],
    
    "spread": bet_data.pointspreads,
    "moneyline": bet_data.moneylines,
    "total": bet_data.totals,
    "points scored": bet_data.scores,
    "points allowed": swap_pairs(bet_data.scores)
    })



# create more columns in dataframe based on initial ones

df["total points scored"] = df["points scored"] + df["points allowed"]

df["lost by"] = df["points allowed"] - df["points scored"]

df["spread win"] = df["lost by"] < df["spread"]

df["moneyline win"] = df["lost by"] < 0

df["total over"] = df["total points scored"] > df["total"]



# Issue with Portland Trail Blazers naming on SBR leads to bug 
# where all home games are classified as False in 'home' column

if len(df[df["home"] == True]) != len(df[df["home"] == False]):
    df.loc[df["participant full name"] == "Portland Trail Blazers", ["home"]] = True





"""
Section Three: Uploading DataFrame
"""


# connect to Google Sheet

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

credentials = ServiceAccountCredentials.from_json_keyfile_name("C:/Users/kimba/VSCode Projects/NBA_Bets/credentials.json", scope)

client = gspread.authorize(credentials)

sheet1 = client.open("NBA Bets 2021-22").get_worksheet(0)



# find position to input dataframe

height = len(sheet1.col_values(1)) + 1



# Check if sheet is empty, add header if needed

if height > 1: 
    Need_Header = False
else: 
    Need_Header = True



# upload dataframe to sheet

set_with_dataframe(sheet1, df, row=height, include_column_header=Need_Header)


print("done")