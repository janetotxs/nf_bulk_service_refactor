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

worksheet = sh.worksheet("BulkService-V2")

records = worksheet.row_values(2)

value = records[nf.BS_INDEX_PROVISION_KEYWORD]
if value:
    print("EXIST!")

print(value)
