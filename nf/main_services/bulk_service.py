from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from utils.env_loader import get_env_variable
from utils.helpers import get_after_word
from utils.logger2 import logger
from nf.main_services.expiry_service import ExpiryService
from nf.nf_constants import NfConstants
from utils.exceptions import (
    BulkServiceError,
    WalletError,
    GSheetUpdateError,
    ExpiryServiceError,
)
import time

# Constants
nf = NfConstants()


class BulkServices:
    def __init__(self, worksheets, webdriver, gsheet):
        self.wd = webdriver
        self.gs = gsheet
        self.worksheets = worksheets
        self.list_service_id = []
        self.es = ExpiryService(self.wd, self.gs)

    # Function to create bulk service
    def create_bulk_service(self, row_data):

        # Redirect to Add Page of Bulk Service
        url = get_env_variable("WEBTOOL_BULK_SERVICES_ADD_FULL_URL")
        self.wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)
        self.wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "visible", timeout=60)

        logger.info(f"Creating bulk service for {row_data[nf.NF_INDEX_NAME]}")
        try:
            logger.info(f"Input Name: {row_data[nf.NF_INDEX_NAME]}")
            self.wd.perform_action(
                "xpath", nf.NF_INPUT_NAME, "sendkeys", row_data[nf.NF_INDEX_NAME]
            )

            logger.info(f"RadioBtn Service Class: Bulk Service")
            self.wd.perform_action(
                "xpath", nf.NF_BS_SERVICE_CLASS_BULK_SERVICE, "click"
            )
            # This verify the input value for wallet if existing, if not, will create new data service
            self.handle_group_status_inquiry(
                row_data[nf.NF_INDEX_GROUP_STATUS_INQUIRY],
                row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT],
                row_data[nf.NF_INDEX_WALLET_TYPE],
                row_data[nf.NF_INDEX_WALLET],
            )

            logger.info(f"Dropdwn Status: ACTIVE")
            self.handle_nf_bs_status("active")

            logger.info(f"Input Thread Count: {row_data[nf.NF_INDEX_THREAD_COUNT]}")
            self.wd.perform_action(
                "name",
                nf.NF_BS_THREAD_COUNT_INPUT_NAME,
                "sendkeys",
                row_data[nf.NF_INDEX_THREAD_COUNT],
            )
            logger.info("Dropdwn Bulk Service Type: Wallet-Based")
            self.handle_nf_bs_type("Wallet-Based")

            logger.info(f"Checkbox Brands: {row_data[nf.NF_INDEX_BRAND]}")
            self.handle_nf_bs_brands(row_data[nf.NF_INDEX_BRAND])

            logger.info("Input Timeout(sec): 60")
            self.wd.perform_action("name", nf.NF_BS_TIMEOUT_SEC, "sendkeys", 60)

            logger.info("Input Status Charged Amount: 0")
            self.wd.perform_action(
                "name", nf.NF_BS_STATUS_CHARGED_AMOUNT, "sendkeys", 0
            )
            logger.info("Input Balance Charged Amount: 0")
            self.wd.perform_action(
                "name", nf.NF_BS_BALANCE_CHARGED_AMOUNT, "sendkeys", 0
            )

            logger.info(f"Input SMP Name: {row_data[nf.NF_INDEX_SMP_NAME]}")
            self.wd.perform_action(
                "name", nf.NF_BS_SMP_NAME, "sendkeys", row_data[nf.NF_INDEX_SMP_NAME]
            )

            logger.info("Input Access Code: 8080")
            self.wd.perform_action(
                "name", nf.NF_BS_DEFAULT_ACCESS_CODE, "sendkeys", 8080
            )

            logger.info("Input Queue Limit: 1000")
            self.wd.perform_action("name", nf.NF_BS_QUEUE_LIMIT, "sendkeys", 1000)

            logger.info(
                f"RadioBtn Deprov on empty: {row_data[nf.NF_INDEX_DEPROV_ON_EMPTY]}"
            )
            self.handle_bs_deprov_on_empty(row_data[nf.NF_INDEX_DEPROV_ON_EMPTY])

            logger.info("RadioBtn Pre-Expiry Notif: No")
            self.handle_bs_preexpiry_notifs("no")

            logger.info(
                f"RadioBtn Subscription Less: {row_data[nf.NF_INDEX_SUBSCRIPTION_LESS]}"
            )
            self.handle_bs_subscription_less(row_data[nf.NF_INDEX_SUBSCRIPTION_LESS])

            logger.info(f"RadioBtn Max Recurrence: No Recurrence")
            self.wd.perform_action("id", nf.NF_BS_MAX_RECURRENCE, "click")

            logger.info(
                f"Input Max Daily Extensions: {row_data[nf.NF_INDEX_MAX_DAILY_EXT]}"
            )
            self.wd.perform_action("name", nf.NF_BS_MAX_DAILY_EXTENSION, "clear")
            self.wd.perform_action(
                "name",
                nf.NF_BS_MAX_DAILY_EXTENSION,
                "sendkeys",
                row_data[nf.NF_INDEX_MAX_DAILY_EXT],
            )

            logger.info(
                f"Input Max Total Extensions: {row_data[nf.NF_INDEX_MAX_TOTAL_EXT]}"
            )
            self.wd.perform_action("name", nf.NF_BS_MAX_TOTAL_EXTENSION, "clear")
            self.wd.perform_action(
                "name",
                nf.NF_BS_MAX_TOTAL_EXTENSION,
                "sendkeys",
                row_data[nf.NF_INDEX_MAX_TOTAL_EXT],
            )

            logger.info(f"Input Promo Name: {row_data[nf.NF_INDEX_PROMO_NAME]}")
            self.wd.perform_action(
                "name",
                nf.NF_BS_PROMO_NAME,
                "sendkeys",
                row_data[nf.NF_INDEX_PROMO_NAME],
            )

            logger.info("All input fields are done!")

            # Section to get success message after clicking submit button
            success_msg = self.wd.submit_form_and_wait_for_success(
                "xpath", nf.NF_ADD_BTN_INPUT, nf.SUCCESS_MESSAGE
            )

            # Section to get the service id in Success Message
            word_service_id = get_after_word(success_msg, "Service with id:")
            service_id = word_service_id.replace(".", "")
            logger.info(f"Bulk Service Id Retrieved: {service_id}")

            # Call function to Start Service Expiry Service
            self.es.create_service_expiry(row_data, service_id)

            return service_id

        except BulkServiceError:
            logger.error(f"Failed to create bulk service")
            raise
        except ExpiryServiceError:
            logger.error(f"Failed to create service expiry service")
            raise

    def handle_group_status_inquiry(
        self, group_status_value, sf_construct_value, wallet_type_value, wallet_value
    ):
        if sf_construct_value.lower() == "prepaid ctl with unli sms and unli voice":
            return

        if group_status_value.lower() == "yes":
            self.wd.perform_action("id", nf.NF_BS_GROUP_STATUS_INQUIRY, "click")

        self.handle_nf_bs_wallet_type(wallet_type_value)

        wallet_status = self.check_wallet(wallet_value)
        self.process_wallet(wallet_status)

    # Handle Radio Button Wallet Type.
    def handle_nf_bs_wallet_type(self, wallet_type_value):
        logger.info(f"RadioBtn Wallet Type: {wallet_type_value}")
        element_map = {
            "sms/voice": nf.BS_WALLET_TYPE_SMSVOICE,
            "data": nf.BS_WALLET_TYPE_DATA,
            "sps": nf.BS_WALLET_TYPE_SPS,
        }
        element = element_map.get(wallet_type_value.lower(), nf.BS_WALLET_TYPE_CPS)
        self.wd.perform_action("xpath", element, "click")

    # Function to check if wallet value exist return boolean True, if not, return False
    def check_wallet(self, wallet_value):
        try:
            logger.info(f"Dropdwn Name: {wallet_value}")
            self.wd.driver.find_element(
                By.XPATH, f"//option[contains(text(),'{wallet_value.strip()}')]"
            ).click()
            return [True, wallet_value]
        except NoSuchElementException:
            return [False, wallet_value]

    def process_wallet(self, wallet_array):
        exists, value = wallet_array
        if exists:
            self.wd.perform_action(
                "xpath", f"//option[contains(text(),'{value}')]", "click"
            )
        else:
            self.create_nf_ds_new_wallet(value)

    def create_nf_ds_new_wallet(self, wallet_name):
        try:
            logger.info(f"Creating new wallet: {wallet_name}")
            self.wd.driver.get(get_env_variable("WEBTOOL_DATA_SERVICES_ADD_FULL_URL"))
            self.wd.wait_until_element(
                "name", nf.NF_DATA_SERVICES_INPUT_NAME, "visible"
            )
            self.wd.perform_action(
                "name", nf.NF_DATA_SERVICES_INPUT_NAME, "sendkeys", wallet_name
            )
            self.wd.perform_action(
                "xpath", nf.NF_DATA_SERVICE_TYPE_WALLET_BASED, "click"
            )
            time.sleep(3)
            self.wd.driver.get(get_env_variable("WEBTOOL_BULK_SERVICES_ADD_FULL_URL"))
            self.wd.wait_until_element("xpath", nf.NF_INPUT_NAME, "visible")
        except Exception as e:
            raise WalletError(f"Failed to create wallet {wallet_name}: {e}")

    # +============================

    # Handle Bulk Service Status Dropdown
    def handle_nf_bs_status(self, nf_status_value):
        element_map = {
            "inactive": nf.BS_STATUS_INACTIVE,
            "no prov": nf.BS_STATUS_NOPROV,
        }

        element = element_map.get(nf_status_value, nf.BS_STATUS_ACTIVE)
        self.wd.perform_action("xpath", element, "click")

    # Handle Bulk Service Type Dropdown
    def handle_nf_bs_type(self, nf_type_value):
        element = None

        if nf_type_value == "Time-Based":
            element = nf.NF_BS_TYPE_TIME_BASED
        else:
            element = nf.NF_BS_TYPE_WALLET_BASED

        self.wd.perform_action("xpath", element, "click")

    # Handle Bulk Service Brands Multiple Checkbox
    def handle_nf_bs_brands(self, brands_value):
        match brands_value.lower():
            case "ghp":
                element = nf.NF_BS_BRAND_GHP
            case "tm":
                element = nf.NF_BS_BRAND_TM
            case "postpaid":
                element = nf.NF_BS_BRAND_POSTPAID
            case "pw":
                element = nf.NF_BS_BRAND_PW

        self.wd.perform_action("id", element, "click")

    # Handle Bulk Service Deprov on empty Radio Button
    def handle_bs_deprov_on_empty(self, deprov_value):
        element = None
        if deprov_value.lower() == "yes":
            element = nf.NF_BS_DEPROV_ON_EMPTY_YES
        else:
            element = nf.NF_BS_DEPROV_ON_EMPTY_NO

        self.wd.perform_action("xpath", element, "click")

    # Handle Bulk Service Pre expiry notif Radio Button
    def handle_bs_preexpiry_notifs(self, preexpiry_value):
        element = None
        if preexpiry_value.lower() == "yes":
            element = nf.NF_BS_CANCEL_PRE_EXPIRY_YES
        else:
            element = nf.NF_BS_CANCEL_PRE_EXPIRY_NO

        self.wd.perform_action("xpath", element, "click")

    # Handle Bulk Service Subscriptonless Radio Button
    def handle_bs_subscription_less(self, subscription_value):
        element = None
        if subscription_value.lower() == "yes":
            element = nf.NF_BS_SUBSCRIPTION_LESS
        else:
            element = nf.NF_BS_NOTSUBSCRIPTION_LESS

        self.wd.perform_action("id", element, "click")

    # Handle Bulk Service Community Pool Radio Button
    def handle_bs_community_pool(self, community_pool_value):
        element = None
        if community_pool_value.lower() == "yes":
            element = nf.NF_BS_COMM_POOL_YES
        else:
            element = nf.NF_BS_COMM_POOL_NO

        self.wd.perform_action("xpath", element, "click")

    def nf_assign_bulk_service_flow(self, double_extend_value, bs_service_id, flow_id):
        try:
            # Assign flow and api flow depends if there's a double/extend/none flow
            logger.info(
                f"Assigning {double_extend_value.upper()} Flow and {double_extend_value.upper()} API Flow in Bulk Services For: {bs_service_id}"
            )
            flow_name = (
                "double_flow"
                if double_extend_value == "double"
                else (
                    "extend_flow" if double_extend_value == "extend" else "default_flow"
                )
            )
            api_flow_name = (
                "api_double_flow" if double_extend_value == "double" else "api_flow"
            )

            # Redirect to Bulk Service Edit page for current service id
            self.wd.driver.get(
                f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=bulk_services&op=edit&id={bs_service_id}"
            )
            self.wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")

            # Input Default Flow Dropwdown
            self.wd.perform_action(
                "xpath",
                f"//select[@name='{flow_name}']//option[@value='{flow_id}']",
                "click",
            )
            if double_extend_value != "extend":
                # Input API Flow Dropdown
                self.wd.perform_action(
                    "xpath",
                    f"//select[@name='{api_flow_name}']//option[@value='{flow_id}']",
                    "click",
                )

            # Handle after editing form. Stop loading the page if its taking time to load and doesn't need to get the element success message...
            # Click Update button
            # self.wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")

            self.wd.submit_form_and_wait_for_success(
                "xpath", nf.NF_ADD_BTN_INPUT, nf.SUCCESS_MESSAGE
            )

        except Exception as e:
            logger.info(
                f"An error has occurred while assigning flow in Edit page of bulk service id: {bs_service_id}\nERROR: {e}"
            )
            raise

    # Orchestrator of bulk service file
    def nf_start_bulk_services(self):

        # Fetch current deployment date rows
        pending_rows = self.gs.get_pending_rows(
            self.worksheets["bulkService"],
            nf.COLUMN_BULK_SERVICE_DEPLOYMENT_DATE,
            nf.BS_INDEX_RPA_REMARKS_BASE_FLOW,
        )
        # If there's no deployment date today to work on, terminate script
        if not pending_rows:
            logger.warning("No deployment today to work on, terminating bot...")
            self.wd.stop_process()
            # return []

        # Start loop using pending rows that has been fetched
        for i, row in enumerate(pending_rows):
            try:
                # Get row data
                row_data = self.worksheets["bulkService"].row_values(row)

                # Call function create_bulk_service to start the process
                service_id = self.create_bulk_service(row_data)

                # Update Bulk Service RPA Remarks after creation
                self.gs.update_row(row, 1, self.worksheets["bulkService"], service_id)
                self.gs.update_row(
                    row,
                    self.worksheets["bulkService"].col_count,
                    self.worksheets["bulkService"],
                    "Bulk Services Created, in progress defining of steps and flows",
                )
                self.list_service_id.append(service_id)

            except BulkServiceError as e:
                logger.error(f"Row {row}: Bulk service failed: {e}")
                self.gs.update_rpa_remarks_error(
                    row, str(e), self.worksheets["bulkService"]
                )

            except ExpiryServiceError as e:
                logger.error(f"Row {row}: Service Expiry failed: {e}")
                self.gs.update_rpa_remarks_error(
                    row, str(e), self.worksheets["bulkService"]
                )

            except Exception as e:
                logger.exception(f"Unexpected error at row {row}: {e}")
                self.wd.stop_process()
                raise

        if not self.list_service_id:
            self.wd.stop_process()
            raise BulkServiceError(
                "No successful Bulk Services created, terminating bot."
            )

        # Return successful rows
        list_success_rows = [
            self.worksheets["bulkService"].find(str(service_id), in_column=1).row
            for service_id in self.list_service_id
        ]
        logger.info(f"Successful Bulk Service Rows: {list_success_rows}")
        return list_success_rows
