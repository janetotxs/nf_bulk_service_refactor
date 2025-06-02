import gspread
import logging
import datetime
from google.oauth2.service_account import Credentials
from typing import List, Dict, Any
from utils.env_loader import get_env_variable

logger = logging.getLogger(__name__)


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
            print(result)
            return result

        except Exception as e:
            logger.info(
                f"An error has occurred on function 'get_pending_rows'\nERROR:{e}"
            )

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
    def get_param_pending_rows(
        self, param_worksheet, bs_name, column_bs_name, column_service_id
    ):
        try:
            logger.info(
                "Checking if there's an input data from ParamMatrix Worksheet related to Bulk Service Name and Service ID"
            )
            print(f"bulk service name: {bs_name}")
            print(f"column bs name: {column_bs_name}")
            print(f"column service id: {column_service_id}")

            # In ParamMatrix worksheet, find current BS name on column 'Service Name'
            current_cells = param_worksheet.findall(bs_name, in_column=column_bs_name)

            # Check ParamMatrix Service ID column if there's an existing value to determine the pending entries, if true, append row value to an array variable.
            result = []
            if len(current_cells) != 0:
                for data in current_cells:
                    print(f"data row: {data.row}")
                    data_value = param_worksheet.cell(data.row, column_service_id).value
                    # print(str(data.row) + " = " + data_value)

                    # If there's no service id in service id column, continue to define.
                    if data_value:
                        logger.info(
                            f"Service ID Exist: {data_value}, proceed to next param"
                        )
                        value = data_value.lower()
                    else:
                        print("No Service ID yet")
                        value = ""

                    if not value:
                        logger.info(f"Stored pending row: {data.row}")
                        result.append(data.row)

            else:
                logger.info("No PARAM to define..")

            print(result)
            return result

        except Exception as e:
            logger.info(
                f"An error has occurred on function 'get_pending_rows'\nERROR:{e}"
            )
