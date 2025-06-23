from utils.env_loader import get_env_variable
from utils.logger2 import logger
from nf.nf_constants import NfConstants
from selenium.common.exceptions import TimeoutException

# Call Constants
nf = NfConstants()


class ExpiryService:
    def __init__(self, webdriver, gsheet):
        self.wd = webdriver
        self.gs = gsheet

    # Function to define the Service Expiry of Bulk Services
    def create_service_expiry(self, bs_row_data, service_id):
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
        self.wd.driver.get(
            f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=service_expiries&op=add&details_id={service_id}"
        )
        self.wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "visible")

        # Section to Input Default Values
        # If Default Duration in Days value is No Expiry, choose radio button no expiry, else, multiple by 24
        logger.info("Site Reached!")
        if "no" in default_duration_in_days_value:
            self.wd.perform_action("id", "et_2", "click")
        else:
            # Input Expiry Field
            self.wd.perform_action(
                "id",
                "expiry",
                "sendkeys",
                int(default_duration_in_days_value) * 24,
            )

            logger.info("Creating Service Expiry with Default Values...")
            # Click Add Button
            self._click_add_and_wait()

        logger.info("Service Expiry Successfully Created With Default Values")

        # Section to Input Param Matrix Values
        param_matrix_rows = self.gs.get_rows_by_name(
            param_worksheet, bs_row_data[nf.NF_INDEX_NAME]
        )

        if len(param_matrix_rows) != 0:
            for row in param_matrix_rows:
                param_matrix_data = param_worksheet.row_values(row)
                logger.info(
                    "Found Param inputs for Service Expiry, filling up Param fields..."
                )
                # Clear Input Param Field
                self.wd.perform_action("name", nf.SERVICE_PARAM_INPUT, "clear")

                # Input Param Field
                self.wd.perform_action(
                    "name",
                    nf.SERVICE_PARAM_INPUT,
                    "sendkeys",
                    param_matrix_data[nf.INDEX_PARAM_MATRIX_AMOUNT],
                )

                # Input Expiry
                self.wd.perform_action(
                    "id",
                    "expiry",
                    "sendkeys",
                    int(param_matrix_data[nf.INDEX_PARAM_MATRIX_DURATION]) * 24,
                )
                # Handle after submitting form.. If taking time to load and doesn't need to get the element success message...
                logger.info("Creating Service Expiry with Param Values...")
                self._click_add_and_wait()

                logger.info("Service Expiry Successfully Created With Param Values")

        else:
            logger.info("No Param Matrix Found for this Service name.")

    def _click_add_and_wait(self, wd):
        try:
            logger.info("Clicking Add button...")
            self.wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
            self.wd.wait_until_element("xpath", nf.NF_SUCCESS_MESSAGE, "visible")
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
