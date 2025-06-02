import gspread
import logging

from google.oauth2.service_account import Credentials
from typing import List, Dict, Any
from utils.env_loader import get_env_variable

logger = logging.getLogger(__name__)

class GSheetClient:
    
    def __init__(self, service_account_file: str = None, scopes: List[str] = None):

        # To Authorize Service Account Access to spreadsheet via gsheet id
        if scopes is None:
            scopes = ['https://www.googleapis.com/auth/spreadsheets']

        if not service_account_file:
            service_account_file = get_env_variable("GOOGLE_SERVICE_ACCOUNT")

        credentials = Credentials.from_service_account_file(service_account_file, scopes=scopes)
        self.client = gspread.authorize(credentials)

        print("Authorized scopes:", credentials.scopes)

  
    # Get Google Worksheet Data using spreadsheet ID
    def get_sheet_data(self, spreadsheet_id: str, worksheet_name: str) -> List[Dict[str, Any]]:
        spreadsheet = self.client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(worksheet_name)
        return worksheet.get_all_records()

    def get_raw_values(self, spreadsheet_id: str, worksheet_name: str) -> List[List[Any]]:
        spreadsheet = self.client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(worksheet_name)
        return worksheet.get_all_values()
