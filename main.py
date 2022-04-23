from datetime import timedelta, date
from distutils.command.upload import upload
import pandas as pd
import collect_data
from upload_to_sheet import upload_to_google_sheet


DATE = str(date.today() - timedelta(days=1))
BOOK = "Bovada"

bet_data = collect_data.TeamBettingData(date=DATE, book=BOOK)

bet_data_df = pd.DataFrame(data=vars(bet_data))
upload_to_google_sheet(data=bet_data_df,
                       workbook="NBA Bets 2021-22",
                       sheet_index=0,
                       credentials_json_path="C:/Users/kimba/VSCode Projects/NBA_Bets/credentials.json")


props_data = collect_data.PlayerProps(LastNGames="10", SeasonType="Playoffs").get_data()
upload_to_google_sheet(data=props_data,
                       workbook="NBA Bets 2021-22",
                       sheet_index=1,
                       credentials_json_path="credentials.json",
                       row=10,
                       col=2,
                       flush_range="B10:H")

print("done")