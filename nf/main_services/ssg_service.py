from utils.logger import setup_logger
from utils.logger2 import logger
from nf.nf_constants import NfConstants
from utils.env_loader import get_env_variable

# logger = setup_logger(service_name=f"NF {__name__}")

# Call Constants
nf = NfConstants()


# Function to define the created bulk service to simple service group
def define_bs_simple_service_group(bs_service_id, bs_rpa_remarks_value, wd):
    try:
        logger.info("STARTING SIMPLE SERVICE GROUP PROCESS")
        # Redirect to Simple Service Group Details Page
        logger.info("Redirecting to Simple Service Group Detail Page...")
        wd.driver.get(
            f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=simple_service_groups&op=details&id=1"
        )
        wd.wait_until_element("xpath", nf.SSG_ADD_BTN_ACCESS_CODE, "visible")
        logger.info("Simple Service Group Detail Page Successfully Reached!")

        # Select Current Bulk Service ID
        wd.perform_action(
            "xpath",
            f"//select[@name='simple_service_id']//option[@value='{bs_service_id}']",
            "click",
        )

        # Input Priority Field = Default Value 1
        wd.perform_action("name", nf.SSG_PRIORITY_INPUT, "sendkeys", 1)

        # Click Add Button
        wd.perform_action("xpath", nf.SSG_ADD_BTN_SIMPLE_SERVICES, "click")
        logger.info(
            f"Bulk Service {bs_service_id} Successfully Defined in Simple Service Group [DATA_BAL] With Priority 1"
        )

    except Exception as e:
        logger.info(
            f"An error has occurred while defining the bulk service in simple service group\nERROR: {e}"
        )
        wd.stop_process()
