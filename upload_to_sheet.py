import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_dataframe import set_with_dataframe


def upload_to_google_sheet(data, workbook, sheet_index, credentials_json_path, row=None, col=1, head=False, flush_range=None):
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive.file",
             "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_json_path, scope)
    client = gspread.authorize(credentials)
    sheet1 = client.open(workbook).get_worksheet(sheet_index)

    if flush_range is not None:
        col_num, row_num = range_to_colrows(flush_range, sheet1.row_count)
        sheet1.batch_update([{"range": flush_range, "values": [[""]*col_num]*row_num}])

    if row is None:
        row = len(sheet1.col_values(col)) + 1

    set_with_dataframe(sheet1, data, col=col, row=row, include_column_header=head)


def range_to_colrows(range: str, sheet_length: int):
    ls = range.split(":")
    col_count = ord(ls[1][0]) - ord(ls[0][0]) + 1

    try:
        top_row = int(ls[0][1:])
    except:
        top_row = 1
    
    try:
        bottom_row = int(ls[1][1:])
    except:
        bottom_row = sheet_length
    row_count = bottom_row - top_row + 1

    return (col_count, row_count)