from utils.env_loader import get_env_variable
from utils.helpers import stop_process
from utils.logger import setup_logger
from utils.google_sheet import GSheetClient
from utils.web_driver import WebDriver
from nf.nf_constants import NfConstants

logger = setup_logger(service_name="NF")

#Calls NF Constants
nf = NfConstants()

def process_sequence_nf():

    #login
    #Calls web driver
    wd = WebDriver()
    url_param = get_env_variable("WEBTOOL_LOGIN_FULL_URL")
    wd.redirect_nf_login_page(url_param) 
    login_sequence(wd)

    #call proccess
    #nf_start_bulk_services()

    stop_process(logger=logger)

# Login Sequence Function.
def login_sequence(wd):
    try:

        gs = GSheetClient()
        gsheet = nf.GSHEET_ID
        sheet_tab = nf.WORKSHEET_TAB_CREDENTIAL

        # Get Credential (from 'Creds' sheet tab) and assign data value to global variable 'creds_data' as array
        logger.info("Account Authorized!, Logging into NF Webtool..")
        try:
            creds_data = gs.get_raw_values(gsheet, sheet_tab)
        except Exception as e:
             logger.error(f"Something went wrong fetching sheet data: {e}")
             raise
        
        # Skip the header (row 0), loop through each row of credentials
        for index, row in enumerate(creds_data[1:], start=2):  # Starting from row 2 (index 1)
            if len(row) < 2:
                logger.warning(f"Skipping row {index}: not enough columns for username/password.")
                continue
            username, password = row[0], row[1]
       
    
        # Input username and password then click Submit button
        wd.find("name", "uname", "sendkeys", username)
        wd.find("name", "passwd", "sendkeys", password)
        wd.find("id", nf.NF_LOGIN_BUTTON, "click")

    except Exception as e:
        logger.info(f"\nSomething went wrong in the Login Sequence.\nERROR: {e}")
        stop_process(logger=logger)




