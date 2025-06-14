import gspread
import logging
import datetime
from google.oauth2.service_account import Credentials
from typing import List, Dict, Any
from utils.env_loader import get_env_variable
from nf.nf_constants import NfConstants

logger = logging.getLogger(__name__)

# Call Constants
nf = NfConstants()


class GSheetClient:

    def __init__(self, service_account_file: str = None, scopes: List[str] = None):

        # To Authorize Service Account Access to spreadsheet via gsheet id
        if scopes is None:
            scopes = ["https://www.googleapis.com/auth/spreadsheets"]

        if not service_account_file:
            service_account_file = get_env_variable("GOOGLE_SERVICE_ACCOUNT")

        credentials = Credentials.from_service_account_file(
            service_account_file, scopes=scopes
        )
        client = gspread.authorize(credentials)
        self.spreadsheet = client.open_by_key(get_env_variable("GSHEET_ID"))
        print("Authorized scopes:", credentials.scopes)

    # Get Google Worksheet Data using spreadsheet ID
    def get_sheet_data(self, worksheet_name: str) -> List[Dict[str, Any]]:
        worksheet = self.spreadsheet.worksheet(worksheet_name)
        return worksheet.get_all_records()

    def get_raw_values(self, worksheet_name: str) -> List[List[Any]]:
        worksheet = self.spreadsheet.worksheet(worksheet_name)
        return worksheet.get_all_values()

    def create_worksheet(self, worksheet_name: str) -> List[List[Any]]:
        worksheet = self.spreadsheet.worksheet(worksheet_name)
        return worksheet

    # Get row data based on current date.
    def get_pending_rows(self, worksheet, column_date, column_rpa_remarks):
        logger.info("Fetching rows to work on for today...")
        try:
            current_date_cells = worksheet.findall(
                datetime.datetime.now().strftime("%Y-%m-%d"), in_column=column_date
            )

            # Check rpa remark column if there's a text that does not contain 'Successful' keyword to determine the pending entries, if true, append row value to an array variable.
            result = []
            for data in current_date_cells:
                print(data.row)
                data_value = worksheet.cell(data.row, column_rpa_remarks).value
                # print(str(data.row) + " = " + data_value)
                if data_value:
                    value = data_value.lower()
                else:
                    value = ""
                print(data_value)
                if not "success" in value or not value:
                    result.append(data.row)
                    logger.info(f"Pending Row Added: {data.row}")
            print(result)
            return result

        except Exception as e:
            logger.info(f"An error has occurred while fetching rows..\nERROR:{e}")

    # Function to Update a specific row via row and column coordinates
    def update_row(self, row, column, worksheet, value):
        try:
            logger.info(f"{worksheet}: Updating Cell...")
            # Update cell using 'value'
            worksheet.update_cell(row, column, value)

        except Exception as e:
            logger.info(
                f"Unexpected error has occurred while updating cell. ERROR: {e}"
            )

    # Function to update RPA remarks for error message based on exception
    def update_rpa_remarks_error(self, row, error_msg, worksheet):
        try:
            # Update remarks failed process
            error_message = f"Failed | {error_msg}"
            worksheet.update_cell(row, worksheet.col_count, error_message)

        except Exception as e:
            logger.info(
                f"Unexpected error has occurred when updating RPA remarks error 'update_rpa_remarks_error'. ERROR: {e}"
            )

    # Get row data for ParamMatrix worksheet
    def get_rows_by_name(self, worksheet, name_to_find):
        try:
            logger.info(f"Fetching Rows that matches: '{name_to_find}'")

            # find all cells that matches the name_to_find value
            current_cells = worksheet.findall(name_to_find)

            result = []
            if len(current_cells) != 0:
                for cell in current_cells:
                    logger.info(f"Row Fetched: {cell.row}")
                    result.append(cell.row)
            else:
                logger.info(
                    f"The bot was unable to find a service name that matches: '{name_to_find}'"
                )
                return []

            logger.info(f"Rows Successfully Fetched: {result}")
            return result

        except Exception as e:
            logger.info(
                f"An error has occurred on function 'get_rows_by_name'\nERROR:{e}"
            )
