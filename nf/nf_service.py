from utils.env_loader import get_env_variable
from utils.logger import setup_logger
from utils.google_sheet import GSheetClient
from utils.web_driver import WebDriver
from nf.main_services import bulk_service as bs
from nf.main_services import step_and_flow_construct_service as sf
from utils.logger2 import logger
from nf.nf_constants import NfConstants
import datetime
import time
from nf.main_services import message_service as ms

# Call Constants
nf = NfConstants()

start_time_info = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
start_time = time.time()

# logger = setup_logger(service_name="NF")


# Function to start the process for NF
def process_sequence_nf():
    # Calls web driver and gsheet
    wd = WebDriver()
    gs = GSheetClient()

    # NF Login Sequence
    login_sequence(wd, gs)

    # NF Process Sequence
    process_sequence(wd, gs)

    # NF Clean up Sequence
    cleanup_sequence(wd)


# Login Sequence Function.
def login_sequence(wd, gs):
    try:
        # Redirect to NF Login Page
        url_param = get_env_variable("WEBTOOL_LOGIN_FULL_URL")
        wd.redirect_nf_login_page(url_param)

        # Get Credential (from 'Creds' sheet tab) and assign data value to global variable 'creds_data' as array
        logger.info("Account Authorized!, Logging into NF Webtool..")
        try:
            creds_data = gs.get_raw_values(nf.WORKSHEET_TAB_CREDENTIAL)
        except Exception as e:
            logger.error(f"Something went wrong fetching sheet data: {e}")
            raise

        # Skip the header (row 0), loop through each row of credentials
        for index, row in enumerate(
            creds_data[1:], start=2
        ):  # Starting from row 2 (index 1)
            if len(row) < 2:
                logger.warning(
                    f"Skipping row {index}: not enough columns for username/password."
                )
                continue
            username, password = row[0], row[1]

        # Input username and password then click Submit button
        wd.perform_action("name", "uname", "sendkeys", username)
        wd.perform_action("name", "passwd", "sendkeys", password)
        wd.perform_action("id", nf.NF_LOGIN_BUTTON, "click")
        wd.wait_until_element("id", "content", "visible")
        logger.info("Login Successful!")

    except Exception as e:
        logger.info(f"\nSomething went wrong in the Login Sequence.\nERROR: {e}")
        wd.stop_process()


# Process Sequence Function
def process_sequence(wd, gs):

    # Create Worksheet For Bulk Service
    bulk_service_worksheet = gs.create_worksheet(nf.WORKSHEET_TAB_BULK_SERVICES_V2)

    # Start Bulk Services Creation Per Row. After creation done, return all successfully created bulk services ROWS as an array to 'bs_success_rows' array variable
    bs_success_rows = bs.nf_start_bulk_services(bulk_service_worksheet, wd, gs)

    # Start defining Steps, using rows successfully created from Bulk Services.
    sf.start_step_and_flow_construct(bulk_service_worksheet, bs_success_rows, wd, gs)

    # Start Defining Messages and Reminder Messages
    ms.create_message(wd, gs)


# Clean Up Sequence Function
def cleanup_sequence(wd):
    logger.info("RPA Bot Process Done. Terminating Bot")

    logger.info(
        f"\nTimestamp Report:"
        f"\nRPA Start Time: {start_time_info}"
        f"\nRPA End Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        f"\n--- Bot Duration: {time.time() - start_time:.2f} seconds ---"
    )
    wd.stop_process()
