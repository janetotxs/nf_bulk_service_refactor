from selenium.webdriver.common.by import By
from utils.env_loader import get_env_variable
from utils.logger2 import logger
from nf import bulk_service as bs
from nf.nf_constants import NfConstants

# Call Constants
nf = NfConstants()


# def nf_start_extension_expiry_service(
#     double_extend_value, bs_service_id, webdriver, gsheet
# ):
#     logger.info("STARTING KEYWORD SERVICE")
#     global wd
#     global gs

#     wd = webdriver
#     gs = gsheet

#     create_extension_expiry(bs_service_id)


def create_extension_expiry(bs_service_id, bs_row_data, wd):
    try:
        # Redirect to Keyword Add Page using bulk service id
        logger.info("Creating Service Extension Expiry...")
        wd.get(
            f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=service_extension_expiries&op=add&details_id={bs_service_id}"
        )
        wd.wait_until_element(
            "name", nf.SERVICE_EXTENSION_EXPIRY_PARAM_INPUT, "visible"
        )

        # Clear Param Input
        wd.perform_action("name", nf.SERVICE_EXTENSION_EXPIRY_PARAM_INPUT, "clear")

        # Input Param Field
        wd.perform_action(
            "name",
            nf.SERVICE_EXTENSION_EXPIRY_PARAM_INPUT,
            "sendkeys",
            bs_row_data[nf.NF_INDEX_EXTEND_AMOUNT],
        )

        # Input Amount Field in hours Field
        wd.perform_action(
            "id",
            nf.SERVICE_EXTENSION_EXPIRY_EXPIRY_INPUT,
            "sendkeys",
            int(bs_row_data[nf.NF_INDEX_EXTEND_DURATION_IN_DAYS]) * 24,
        )

        # Click Add Button
        wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")

        logger.info("Service Extension Expiry Successfully Created!")

    except Exception as e:
        logger.info(f"An error has occurred while creating keyword\nERROR:{e}")
        wd.stop_process()
