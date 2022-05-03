import gspread
import gspread_dataframe
from pandas import DataFrame


def upload_to_google_sheet(
    data: DataFrame,
    credentials_json_path: str,
    workbook: str,
    sheet_index: int = 0,
    row: int = 1,
    col: int = 1,
    append: bool = False,
    head: bool = False,
    flush_range: str = None
):
    """
    Uploads DataFrame to Google Sheet.

    Connects to the specified sheet with proper credentials and uploads
    the passed pandas DataFrame, anchoring the top left corner to
    (row, col). Uses gspread.

    Parameters
    ----------
    data : DataFrame
        A pandas DataFrame to be uploaded. Refer to
        gspread_dataframe.set_with_dataframe

    credentials_json_path : str
        The path to a `json` file containing the information about the
        bot account that the workbook should be shared with.
        Refer to gspread's Authentication -> For Bots for more info.

    workbook : str
        The name of the Google Sheets workbook

    sheet_index : int
        Indexed from `0`, default to `0`. The index of the sheet in the
        workbook to be accessed.
        Ex: the sheet as the far left tab in the workbook is index 0, to
        the right of it is index 1...

    row : int
        Indexed from `1`, default to `1`. Row index for where to insert
        DataFrame, anchored in the top left.

    col : int
        Indexed from `1`, default to `1`. Column index for where to
        insert DataFrame, anchored in the top left.

    append : bool
        Default to `False`. If `True`, will overwrite `row` to be first
        empty row after last value in column defined by `col`

    head : bool
        Default to `False`, If `True`, will include the DataFrame
        column names as a header row.
    
    flush_range : str
        Optional argument. Google Sheets range format ("A1:C5", "D:L").
        Only supports up through column Z. Remove all values in the
        specified range before uploading DataFrame.
    """
    # Creates sheet to use Google API
    gc = gspread.service_account(filename=credentials_json_path)
    sheet = gc.open(workbook).get_worksheet(sheet_index)

    # Clears all values from flush_range if specified
    if flush_range is not None:
        col_num, row_num = range_to_colrows_count(flush_range, sheet.row_count)
        flush_dict = {
            "range": flush_range,
            "values": [[""]*col_num]*row_num
        }
        sheet.batch_update([flush_dict])

    if append is True:
        row = len(sheet.col_values(col)) + 1


    gspread_dataframe.set_with_dataframe(
        worksheet=sheet,
        dataframe=data,
        col=col,
        row=row,
        include_column_header=head
    )


def range_to_colrows_count(range: str, sheet_length: int = 1000) -> tuple:
    """
    Returns tuple (number of columns, number of rows) in the passed
    Google Sheets range.

    Parameters
    ----------
    range : str
        Google Sheets range format ("A1:C5", "D:L"). Only supports up
        through column Z.
    
    sheet_length : int
        Default to 1000. Total number of rows in the sheet (including 
        empty). Necessary in the case a last row isn't specified so as
        not to add extra rows to sheet.

    Examples
    ----------
    >>> range_to_colrows_count("A3:D10")
    (4, 8)

    >>> range_to_colrows_count("A:Z")
    (26, 1000)

    >>> range_to_colrows_count("D5:E", sheet_length=500)
    (2, 496)

    >>> range_to_colrows_count("A:F12")
    (6, 12)
    """
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