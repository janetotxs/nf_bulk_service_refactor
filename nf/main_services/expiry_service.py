from utils.env_loader import get_env_variable
from utils.logger2 import logger
from nf.nf_constants import NfConstants
from selenium.common.exceptions import TimeoutException
from utils.exceptions import ExpiryServiceError

# Call Constants
nf = NfConstants()


class ExpiryService:
    def __init__(self, webdriver, gsheet):
        self.wd = webdriver
        self.gs = gsheet

    # Function to define the Service Expiry of Bulk Services
    def create_service_expiry(self, bs_row_data, service_id):
        try:
            logger.info("STARTING EXPIRY SERVICE PROCESS")
            # Declare ParamMatrix Worksheet
            param_worksheet = self.gs.create_worksheet(
                nf.WORKSHEET_TAB_BULK_SERVICES_TAB_PARAM_MATRIX
            )

            # Declare Default Duration in days
            default_duration_in_days_value = bs_row_data[
                nf.NF_INDEX_DEFAULT_DURATION_IN_DAYS
            ].lower()
            logger.info("Redirecting to Add Service Expiry Page")
            # self.wd.driver.get(
            #     f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=service_expiries&op=add&details_id={service_id}"
            # )
            url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=service_expiries&op=add&details_id={service_id}"
            self.wd.redirect_to_page(url, nf.NF_ADD_BTN_INPUT)
            self.wd.wait_until_element(
                "xpath", nf.NF_ADD_BTN_INPUT, "clickable", timeout=60
            )

            # Section to Input Default Values
            # If Default Duration in Days value is No Expiry, choose radio button no expiry, else, multiple by 24
            logger.info("Filling up service expiry fields...")

            logger.info(f"Input Expiry: {int(default_duration_in_days_value) * 24}")
            if "no" in default_duration_in_days_value:
                self.wd.perform_action("id", "et_2", "click")
            else:
                # Input Expiry
                self.wd.perform_action(
                    "id",
                    "expiry",
                    "sendkeys",
                    int(default_duration_in_days_value) * 24,
                )

                logger.info("Submitting Service Expiry with Default Values...")
                # Click Add Button
                self.wd.submit_form_and_wait_for_success(
                    "xpath", nf.NF_ADD_BTN_INPUT, nf.CONTAINS_SUCCESS_MESSAGE, skip=True
                )

            logger.info("Service Expiry Successfully Created With Default Fields")

            # Section to Input Param Matrix Values
            param_matrix_rows = self.gs.get_rows_by_name(
                param_worksheet, bs_row_data[nf.NF_INDEX_NAME]
            )

            if len(param_matrix_rows) != 0:
                for row in param_matrix_rows:
                    param_matrix_data = param_worksheet.row_values(row)
                    logger.info(
                        "Found ParamMatrix inputs for service expiry, filling up Param fields..."
                    )
                    self.wd.redirect_to_page(url)
                    self.wd.wait_until_element(
                        "xpath", nf.NF_ADD_BTN_INPUT, "clickable", timeout=60
                    )
                    logger.info(
                        f"Input Param Field: {param_matrix_data[nf.INDEX_PARAM_MATRIX_PARAM]}"
                    )
                    # Clear Input Param Field
                    self.wd.perform_action("name", nf.SERVICE_PARAM_INPUT, "clear")

                    # Input Param Field
                    self.wd.perform_action(
                        "name",
                        nf.SERVICE_PARAM_INPUT,
                        "sendkeys",
                        param_matrix_data[nf.INDEX_PARAM_MATRIX_PARAM],
                    )

                    logger.info(
                        f"Input Expiry: {int(param_matrix_data[nf.INDEX_PARAM_MATRIX_DURATION]) * 24}"
                    )
                    # Input Expiry
                    self.wd.perform_action(
                        "id",
                        "expiry",
                        "sendkeys",
                        int(param_matrix_data[nf.INDEX_PARAM_MATRIX_DURATION]) * 24,
                    )
                    # Handle after submitting form.. If taking time to load and doesn't need to get the element success message...
                    logger.info("Submitting Service Expiry with Param Values...")
                    self.wd.submit_form_and_wait_for_success(
                        "xpath",
                        nf.NF_ADD_BTN_INPUT,
                        nf.CONTAINS_SUCCESS_MESSAGE,
                        skip=True,
                    )
                    # self._click_add_and_wait()

                    logger.info("Service Expiry Successfully Created With Param Fields")

            else:
                logger.info("No ParamMatrix Found for this Service name.")
        except ExpiryServiceError:
            raise

    def _click_add_and_wait(self):
        try:
            logger.info("Clicking Add button...")
            self.wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
            self.wd.wait_until_element("xpath", nf.CONTAINS_SUCCESS_MESSAGE, "visible")
            logger.info("Service Expiry successfully created.")
        except TimeoutException:
            logger.warning(
                "TimeoutException occurred after clicking Add. Refreshing page..."
            )
            self.wd.driver.refresh()
            raise

        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            self.wd.driver.refresh()
            raise
