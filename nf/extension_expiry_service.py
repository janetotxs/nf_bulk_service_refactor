from selenium.webdriver.common.by import By
from utils.env_loader import get_env_variable
from utils.logger2 import logger
from nf import bulk_service as bs
from nf.nf_constants import NfConstants

# Call Constants
nf = NfConstants()


def nf_start_extension_expiry_service(
    double_extend_value, bs_service_id, webdriver, gsheet
):
    logger.info("STARTING KEYWORD SERVICE")
    global wd
    global gs

    wd = webdriver
    gs = gsheet

    # Execute keyword_extend function if its in the Extend flow
    if double_extend_value == "extend":
        create_extension_expiry(bs_service_id)


def create_extension_expiry(bs_service_id):
    # Redirect to Keyword Add Page using bulk service id
    wd.get(
        f"{get_env_variable('WEBTOOL_BASE_URL')}nf/index.php?mod=service_keywords&op=add&details_id={bs_service_id}"
    )
    wd.wait_until_element("xpath", nf.KEYWORD_OPERATION, "visible")
