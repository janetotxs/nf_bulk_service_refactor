from selenium.webdriver.common.by import By
from utils.env_loader import get_env_variable
from utils.logger2 import logger
from nf import bulk_service as bs
from nf.nf_constants import NfConstants

# Call Constants
nf = NfConstants()


# Start Service Keyword
# def nf_start_service_keyword(
#     bs_service_id, bs_row_data, webdriver, gsheet, double_extend_value=None
# ):

#     logger.info("STARTING KEYWORD SERVICE")
#     global wd
#     global gs

#     wd = webdriver
#     gs = gsheet

#     # Call create_keyword to create new keyword
#     create_keyword(bs_service_id, bs_row_data, double_extend_value)


def create_keyword(bs_service_id, bs_row_data, wd, double_extend_value=None):
    try:
        logger.info("Creating Service Keyword...")
        # Declare Keyword Operation Option if Provision, Deprovision, Status or Extend
        provision_keyword_value = bs_row_data[nf.BS_INDEX_PROVISION_KEYWORD]
        deprovision_keyword_value = bs_row_data[nf.BS_INDEX_DEPROVISION_KEYWORD]
        status_keyword_value = bs_row_data[nf.BS_INDEX_STATUS_KEYWORD]
        extend_keyword_value = bs_row_data[nf.BS_INDEX_EXTEND_KEYWORD]

        # For Extend Flow only
        if extend_keyword_value and double_extend_value == "extend":
            keyword_value = extend_keyword_value
            selected_keyword_operation = nf.KEYWORD_OPERATION_EXTEND
            operation_string = "Extend"

        # For Declaring Status Keyword and Operation
        elif status_keyword_value:
            keyword_value = status_keyword_value
            selected_keyword_operation = (
                "foo"  # Mamsh declare mo na lng sa nf_constants dapat naka xpath
            )
            operation_string = "Status"

        # For Declaring Deprovision Keyword Declaration
        elif deprovision_keyword_value:
            keyword_value = deprovision_keyword_value
            selected_keyword_operation = (
                "foo"  # Mamsh declare mo na lng sa nf_constants dapat naka xpath
            )
            operation_string = "Deprovision"

        # For Declaring Provision Keyword Declaration
        elif provision_keyword_value:
            keyword_value = provision_keyword_value
            selected_keyword_operation = (
                "foo"  # Mamsh declare mo na lng sa nf_constants dapat naka xpath
            )
            operation_string = "Provision"

        logger.info(
            f"Keyword Operation: {operation_string} Keyword Value: {keyword_value}"
        )

        # Redirect to Keyword Add Page using bulk service id
        wd.get(
            f"{get_env_variable('WEBTOOL_BASE_URL')}nf/index.php?mod=service_keywords&op=add&details_id={bs_service_id}"
        )
        wd.wait_until_element("xpath", nf.KEYWORD_OPERATION, "visible")

        # Section to fill up the fields
        # Dropdown Operation Field
        wd.perform_action("xpath", selected_keyword_operation, "click")

        # Input Regex Field
        wd.perform_action("name", nf.KEYWORD_REGEX_INPUT, "sendkeys", keyword_value)

        # Click Add Button
        wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")

        logger.info("Service Keyword Successfully Created!")

    except Exception as e:
        logger.info(f"An error has occurred while creating keyword\nERROR:{e}")
        wd.stop_process()
