from datetime import timedelta, date
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
                       credentials_json_path="")

print("done")