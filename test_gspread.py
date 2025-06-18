import re
import gspread
import datetime
import time
from dotenv import load_dotenv
import uuid
import os
from nf.nf_constants import NfConstants
from utils.env_loader import get_env_variable

# logger = setup_logger(service_name=f"NF {__name__}")

# Call Constants
nf = NfConstants()


load_dotenv()

# To Authorize Service Account Access to spreadsheet
gc = gspread.service_account(filename="secret_key.json")

sh = gc.open_by_key(os.getenv("GSHEET_ID"))

worksheet = sh.worksheet("Messages")


# Function to Update a specific row via row and column coordinates
def update_row(row, column, worksheet, value):
    try:
        print(f"{worksheet}: Updating Cell...")
        # Update cell using 'value'
        worksheet.update_cell(row, column, value)

    except Exception as e:
        print(f"Unexpected error has occurred while updating cell. ERROR: {e}")


rows = [2, 3]

for row in rows:
    update_row(row, 13, worksheet, 1192)
