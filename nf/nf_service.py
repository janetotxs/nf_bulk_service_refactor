from utils.env_loader import get_env_variable
from utils.logger import setup_logger, log_traceback, finalize_log_upload
from utils.google_sheet import GSheetClient
from utils.web_driver import WebDriver
from nf.main_services import bulk_service as bs
from nf.main_services import step_and_flow_construct_service as sf

from utils.logger2 import logger
from nf.nf_constants import NfConstants
import datetime
import time
from nf.main_services.bulk_service import BulkServices
from nf.main_services.step_and_flow_construct_service import StepAndFlowConstructService

# Call Constants
nf = NfConstants()

# logger = setup_logger(service_name="NF", gs_client=gs)

start_time_info = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
start_time = time.time()
dict_worksheets = {
    "bulkService": nf.WORKSHEET_TAB_BULK_SERVICES,
    "paramMatrix": nf.WORKSHEET_TAB_BULK_SERVICES_TAB_PARAM_MATRIX,
    "messages": nf.WORKSHEET_TAB_BULK_SERVICES_TAB_MESSAGES,
}


class NFService:
    def __init__(self):
        self.wd = WebDriver()
        self.gs = GSheetClient()
        self.worksheets = self.gs.create_worksheets(dict_worksheets)
        self.bs = BulkServices(self.worksheets, self.wd, self.gs)
        self.sf = StepAndFlowConstructService(self.worksheets, self.wd, self.gs)

    # Login Sequence Function.
    def login_sequence(self):
        try:
            # Redirect to NF Login Page
            url_param = get_env_variable("WEBTOOL_LOGIN_FULL_URL")
            print(url_param)
            self.wd.redirect_to_page(url_param)
            self.wd.wait_until_element("id", nf.NF_LOGIN_BUTTON, "clickable")

            # Get Credential (from 'Creds' sheet tab) and assign data value to global variable 'creds_data' as array
            logger.info("Account Authorized!, Logging into NF Webtool..")
            try:
                creds_data = self.gs.get_raw_values(nf.WORKSHEET_TAB_CREDENTIAL)
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
            self.wd.perform_action("name", "uname", "sendkeys", username)
            self.wd.perform_action("name", "passwd", "sendkeys", password)
            self.wd.perform_action("id", nf.NF_LOGIN_BUTTON, "click")
            self.wd.wait_until_element("id", "content", "visible")
            logger.info("Login Successful!")

        except Exception as e:
            logger.info(f"\nSomething went wrong in the Login Sequence.\nERROR: {e}")
            self.wd.stop_process()

    # Process Sequence Function
    def process_sequence(self):

        # Start Bulk Services Creation Per Row. After creation done, return all successfully created bulk services ROWS as an array to 'bs_success_rows' array variable
        bs_success_rows = self.bs.nf_start_bulk_services()

        # Start defining Steps, using rows successfully created from Bulk Services.
        self.sf.start_step_and_flow_construct(bs_success_rows)

    # Clean Up Sequence Function
    def cleanup_sequence(self):
        logger.info("RPA Bot Process Done. Terminating Bot")
        duration_seconds = time.time() - start_time
        logger.info(
            f"\nTimestamp Report:"
            f"\nRPA Start Time: {start_time_info}"
            f"\nRPA End Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            f"\n--- Bot Duration: {str(datetime.timedelta(seconds=int(duration_seconds)))} ---"
        )
        self.wd.stop_process()

    # Function to check failed services
    def fallback_sequence(self):
        from nf.fallback_services.fallback_controller import FallbackController

        fs = FallbackController(self.wd, self.gs, self.worksheets)
        fs.start_nf_fallback_service()

    # Function to call NF sequence
    def run_sequence(self, fail_check=False):

        self.login_sequence()

        if fail_check:
            self.fallback_sequence()
        else:
            self.process_sequence()

        self.cleanup_sequence()
