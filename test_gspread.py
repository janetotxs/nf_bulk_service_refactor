import re
import gspread
import datetime
import time
from dotenv import load_dotenv
import uuid
import os

load_dotenv()

# To Authorize Service Account Access to spreadsheet
gc = gspread.service_account(filename="secret_key.json")

sh = gc.open_by_key(os.getenv("GSHEET_ID"))

worksheet = sh.worksheet("BulkService-V2")

records = worksheet.get_all_records()
if records[0]["Provision Keyword"]:
    print("YES")
print(records[0])
