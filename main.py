from datetime import timedelta, date
from distutils.command.upload import upload
import pandas as pd
import collect_data
from upload_to_sheet import upload_to_google_sheet


DATE = str(date.today() - timedelta(days=1))
BOOK = "Bovada"

bet_data = collect_data.BettingData(date=DATE, book=BOOK)

bet_data_df = pd.DataFrame(data=vars(bet_data))

upload_to_google_sheet(data=bet_data_df,
                       workbook="NBA Bets 2021-22",
                       sheet_index=0,
                       credentials_json_path=r"C:\Users\kimba\VSCode Projects\NBA_Bets\credentials.json")

props_data = collect_data.PlayerProps(last_n_games=10).get_data()

upload_to_google_sheet(data=props_data,
                       workbook="NBA Bets 2021-22",
                       sheet_index=1,
                       credentials_json_path=r"C:\Users\kimba\VSCode Projects\NBA_Bets\credentials.json",
                       row=9,
                       col=2)

print("done")