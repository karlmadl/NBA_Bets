import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe


def upload_to_google_sheet(data, workbook, sheet_index, credentials_json_path):
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive.file",
             "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_json_path, scope)
    client = gspread.authorize(credentials)
    sheet1 = client.open(workbook).get_worksheet(sheet_index)

    height = len(sheet1.col_values(1)) + 1

    if height > 1: 
        Need_Header = False
    else: 
        Need_Header = True
    set_with_dataframe(sheet1, data, row=height, include_column_header=Need_Header)