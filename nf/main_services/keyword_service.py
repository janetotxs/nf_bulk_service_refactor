from selenium.webdriver.common.by import By
from utils.env_loader import get_env_variable
from utils.logger2 import logger
from nf.main_services import bulk_service as bs
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
        logger.info("STARTING EXTEND KEYWORD PROCESS")
        # Declare Keyword value and Operation
        # list_keywords = []
        provision_keyword_value = bs_row_data[nf.BS_INDEX_PROVISION_KEYWORD]
        deprovision_keyword_value = bs_row_data[nf.BS_INDEX_DEPROVISION_KEYWORD]
        status_keyword_value = bs_row_data[nf.BS_INDEX_STATUS_KEYWORD]
        extend_keyword_value = bs_row_data[nf.BS_INDEX_EXTEND_KEYWORD]
        # list_keywords.append(provision_keyword_value)
        # list_keywords.append(deprovision_keyword_value)
        # list_keywords.append(status_keyword_value)
        # list_keywords.append(extend_keyword_value)

        keyword_conditions = {
            "Provision": True if provision_keyword_value else False,
            "Deprovision": True if deprovision_keyword_value else False,
            "Status": True if status_keyword_value else False,
            "Extend": (
                True
                if extend_keyword_value and double_extend_value == "extend"
                else False
            ),
        }

        # Start Loop for each keyword that is set to True
        for keyword_key, keyword_true in keyword_conditions.items():
            if keyword_true:
                logger.info(f"Current Loop: {keyword_key}")
                # Get keyword value and operiations by calling function get_keyword_operation
                keyword_value, selected_keyword_operation = get_keyword_operation(
                    keyword_key.lower(),
                    provision_keyword_value,
                    deprovision_keyword_value,
                    status_keyword_value,
                    extend_keyword_value,
                )

                logger.info(
                    f"Keyword Operation: {keyword_key} Keyword Value: {keyword_value}"
                )

                # Redirect to Keyword Add Page using bulk service id
                wd.driver.get(
                    f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=service_keywords&op=add&details_id={bs_service_id}"
                )
                wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "visible")
                logger.info("Site Reached!")

                # Section to fill up the fields
                # Dropdown Operation Field
                wd.perform_action("xpath", selected_keyword_operation, "click")

                # Input Regex Field
                wd.perform_action(
                    "name", nf.KEYWORD_REGEX_INPUT, "sendkeys", keyword_value
                )

                # Click Add Button
                wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")

                logger.info(
                    f"Service Keyword Successfully Created for {keyword_key.upper()}"
                )

    except Exception as e:
        logger.info(f"An error has occurred while creating keyword\nERROR:{e}")
        wd.stop_process()


def get_keyword_operation(
    keyword_key,
    provision_keyword_value,
    deprovision_keyword_value,
    status_keyword_value,
    extend_keyword_value,
):
    # For Extend Flow only
    if keyword_key == "extend":
        keyword_value = extend_keyword_value
        selected_keyword_operation = nf.KEYWORD_OPERATION_EXTEND

    # For Declaring Status Keyword and Operation
    elif keyword_key == "status":
        keyword_value = status_keyword_value
        selected_keyword_operation = "foo"  # Mamsh declare mo na lng sa nf_constants yung xpath neto at dapat naka xpath, pde mo nlng gayahin ung ginawa ko na EXTEND

    # For Declaring Deprovision Keyword Declaration
    elif keyword_key == "deprovision":
        keyword_value = deprovision_keyword_value
        selected_keyword_operation = "foo"  # Mamsh declare mo na lng sa nf_constants yung xpath neto at dapat naka xpath, pde mo nlng gayahin ung ginawa ko na EXTEND

    # For Declaring Provision Keyword Declaration
    elif keyword_key == "provision":
        keyword_value = provision_keyword_value
        selected_keyword_operation = "foo"  # Mamsh declare mo na lng sa nf_constants yung xpath neto at dapat naka xpath, pde mo nlng gayahin ung ginawa ko na EXTEND

    return keyword_value, selected_keyword_operation
