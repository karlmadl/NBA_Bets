import gspread
from gspread_dataframe import set_with_dataframe
from pandas import DataFrame


def upload_to_google_sheet(data: DataFrame,
                           credentials_json_path: str,
                           workbook: str,
                           sheet_index: int = 0,
                           row: int = None,
                           col: int = 1,
                           head: bool = False,
                           flush_range: str = None):

    gc = gspread.service_account(filename=credentials_json_path)
    sheet = gc.open(workbook).get_worksheet(sheet_index)

    if flush_range is not None:
        col_num, row_num = range_to_colrows(flush_range, sheet.row_count)
        sheet.batch_update([{"range": flush_range, "values": [[""]*col_num]*row_num}])

    if row is None:
        row = len(sheet.col_values(col)) + 1

    set_with_dataframe(sheet, data, col=col, row=row, include_column_header=head)


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