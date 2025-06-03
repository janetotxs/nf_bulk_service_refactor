from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from utils.env_loader import get_env_variable
from utils.helpers import get_after_word
from utils.logger import setup_logger
from utils.logger2 import logger
from nf import flow_service as flow
from nf.nf_constants import NfConstants
import time
import os

# logger = setup_logger(service_name=f"NF {__name__}")

# Call Constants
nf = NfConstants()


# Function to start Steps service loop using BS successfully created rows/row
def start_nf_service_steps(bs_worksheet, bs_success_rows, webdriver, gsheet):
    global wd
    global gs

    wd = webdriver
    gs = gsheet

    # Start looping all the bulk service rows for 'Steps and Flow Construct' process
    for row in bs_success_rows:
        try:
            bs_row_data = bs_worksheet.row_values(row)
            logger.info(f"Bulk Service Data Row {row}: {bs_row_data}")

            # Create worksheet for ParamMatrix
            param_worksheet = gs.create_worksheet(
                nf.WORKSHEET_TAB_BULK_SERVICES_TAB_PARAM_MATRIX
            )

            # Start NF Service Step type process and return dictionary step details
            dict_steps_type = nf_start_steps_flow_construct(
                bs_row_data, param_worksheet, row
            )

            # Start Flow Process to Define Flow from 'step_from' to 'step_to'
            flow.nf_start_service_flows(
                dict_steps_type, bs_row_data[0], bs_worksheet, wd, gs, row
            )

        except Exception as e:
            error_msg = f"An error has occurred on 'start_nf_service_steps' function\n ERROR: {e}"
            logger.info(error_msg)
            gs.update_rpa_remarks_error(row, error_msg)
            continue


# Funcion to start Service Steps and flow construct
def nf_start_steps_flow_construct(bs_row_data, param_worksheet, row):
    # --------------------START STEPS PROCESS------------------------#
    logger.info("STARTING PROCESS FOR: ADD SERVICE STEPS")
    # Assign BS Service Id to variable 'bs_service_id'
    bs_service_id = bs_row_data[0]
    steps_id = None
    try:

        logger.info(f"STARTING DEFINING STEPS FOR: {bs_service_id} = {bs_row_data[1]}")
        # logger.info(f"BULK SERVICES ROW DATA : {bs_row_data}")

        # Determine what specific process to defining steps and flows for bulk services.
        # Execute Process For Step Type = Prepaid CTL With Data
        if bs_row_data[13].lower() == "prepaid ctl with data":
            logger.info(
                f"Steps and Flow Construct - Executing Process => '{bs_row_data[13]}'"
            )
            # Calling function to execute step type for prepaid ctl with data
            dict_steps_type = step_type_prepaid_ctl_with_data(
                bs_service_id, bs_row_data, param_worksheet
            )

            return dict_steps_type
            # Execute Flow Process to Define Flow 'step from' and 'step to'
            # flows.nf_start_service_flows(dict_steps_type, bs_service_id, row)

        else:
            logger.info(
                f"Value doesn't recognize '{bs_row_data[13]}' to process for steps and flows construct."
            )

    except Exception as e:
        error_msg = f"Something went wrong in the Process Sequence of 'SERVICE STEPS PROCESS'.\nERROR: {e}"
        logger.info(error_msg)
        gs.update_rpa_remarks_error(row, error_msg)
        logger.info("Terminating Bot")
        wd.stop_process()
    # --------------------END STEPS PROCESS------------------------#


# Function to enter default values to inputs
def nf_steps_default_input(name_value, steps_type_element):
    # Input Name Field
    wd.perform_action("xpath", os.getenv("NF_INPUT_NAME"), "sendkeys", name_value)

    # Select Bulk Service Dropdown DEFAULT = Current Bulk Service/Service ID
    wd.perform_action("xpath", steps_type_element, "click")

    # Input Retry Field
    wd.perform_action("name", os.getenv("NF_STEPS_RETRY_INPUT"), "sendkeys", 3)


# Function to execute process for step type IN CHARGE
def nf_steps_in_charge(bs_service_id, bs_row_data, param_worksheet):
    try:
        steps_type_id_name = []
        # Redirect to Add Service Steps Page with service id
        logger.info("Redirecting to Add Steps Page...")
        wd.driver.get(
            f"{os.getenv('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
        )
        wd.wait_until_element("id", os.getenv("NF_STEPS_TYPE_DROPDOWN"), "visible")
        print("ARRIVE CURRENT PAGE: ADD STEP")

        # Call function 'nf_steps_default_input' to fill up default values
        nf_steps_default_input(
            "IN_CHARGE", "//option[contains(text(), 'IN CHARGE') and @value='2']"
        )

        # Input Amount Field
        wd.perform_action("name", "param_amt_ccode[0][amount]", "sendkeys", 179)

        logger.info("Checking ParamMatrix")
        # Get ParamMatrix rows that equals to current Bulk service name
        bs_name_column = param_worksheet.col_count - 1
        param_matrix_pending_rows = gs.get_param_pending_rows(
            param_worksheet, bs_row_data[1], bs_name_column, param_worksheet.col_count
        )
        logger.info(f"ParamMatrix Pending Rows: {param_matrix_pending_rows}")
        if len(param_matrix_pending_rows) != 0:

            logger.info("Steps has multiple ParamMatrix for IN CHARGE.")
            for index, row in enumerate(param_matrix_pending_rows, 1):

                # Get ParamMatrix data values via row
                row_param_data = param_worksheet.row_values(row)

                logger.info("Filling up additional Param fields")
                # Click 'Add more Param - Amount - Charge Code' to add new field entry
                wd.perform_action(
                    "xpath",
                    "//a[@onclick='javascript: add_param_amount_chargecode_field();']",
                    "click",
                )

                logger.info(f"Param - Amount - Charge Code = ENTRY PARAM{index}")

                # Fill up Param Field
                wd.perform_action(
                    "name",
                    f"param_amt_ccode[{index}][param] type=",
                    "sendkeys",
                    row_param_data[0],
                )
                # Input Amount Field
                wd.perform_action(
                    "name",
                    f"param_amt_ccode[{index}][amount] type=",
                    "sendkeys",
                    row_param_data[1],
                )
                # Worksheet Update for ParamMatrix - Add BS Service ID Value to ParamMatrix Service ID column
                # gs.update_row(row, param_worksheet.col_count, param_worksheet, bs_service_id)
                logger.info(
                    f"\nWorksheet Updated: {param_worksheet}\nRow Updated: {row}"
                )

        # Click 'Add' button to submit.
        wd.perform_action("xpath", os.getenv("NF_ADD_BTN_INPUT"), "click")

        # Wait for the success message element to appear.
        wd.wait_until_element("xpath", "(//div[@id='content']//div)[1]", "visible")
        print("GET ELEMENT")
        element_value = wd.driver.find_element(
            By.XPATH, "(//div[@id='content']//div)[1]"
        ).text

        # Get Steps unique ID from success message
        steps_id = get_after_word(element_value, "step")
        # steps_id = 1021

        logger.info(f"Retrieved STEPS ID: {steps_id} for IN CHARGE")

        logger.info("STEPS IN CHARGE SUCCESSFULLY DEFINED!")
        steps_type_id_name.append(steps_id)
        steps_type_id_name.append("IN_CHARGE")
        logger.info(f"List IN CHARGE: {steps_type_id_name}")
        return steps_type_id_name

    except Exception as e:
        error_msg = f"An error has occurred while processing Step Type IN CHARGE 'nf_steps_in_charge'\n ERROR: {e}"
        logger.info(error_msg)
        raise Exception(error_msg)


# Function to execute process for step type EXTENDS FIRST EXPIRY
def nf_steps_extend_first_expiry(bs_service_id, bs_row_data, param_worksheet):
    try:
        steps_type_id_name = []
        # Redirect to Add Service Steps Page with service id
        wd.driver.get(
            f"{os.getenv('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
        )
        wd.wait_until_element("id", os.getenv("NF_STEPS_TYPE_DROPDOWN"), "visible")
        print("ARRIVE CURRENT PAGE: ADD STEP")

        # Call function 'nf_steps_default_input' to fill up default values
        nf_steps_default_input(
            "EXTENDS_FIRST_EXPIRY",
            "//option[contains(text(), 'EXTEND FIRST EXPIRY') and @value='19']",
        )

        # Input Amount Field
        wd.perform_action("xpath", "(//input[@name='durations[]'])[1]", "sendkeys", 15)

        # Get ParamMatrix rows that equals to current Bulk service name
        bs_name_column = param_worksheet.col_count - 1
        param_matrix_rows = gs.get_param_pending_rows(
            param_worksheet, bs_row_data[1], bs_name_column, param_worksheet.col_count
        )
        if len(param_matrix_rows) != 0:
            logger.info("Steps has multiple ParamMatrix for EXTEND FIRWST EXPIRY.")
            for index, row in enumerate(param_matrix_rows, 2):

                # Get ParamMatrix data values via row
                row_param_data = param_worksheet.row_values(row)

                logger.info("Filling up additional Param fields")
                # Click 'Add more Param & Duration' to add new field entry
                wd.perform_action(
                    "xpath",
                    "//a[@onclick='javascript: add_param_duration_field();']",
                    "click",
                )

                logger.info(f"Param & Duration = ENTRY PARAM{index-1}")

                # Fill up Param Field
                wd.perform_action(
                    "xpath",
                    f"(//input[@name='pars[]'])[{index}]",
                    "sendkeys",
                    row_param_data[0],
                )
                # Input Duration Field
                wd.perform_action(
                    "xpath",
                    f"(//input[@name='durations[]'])[{index}]",
                    "sendkeys",
                    row_param_data[2],
                )
                # Worksheet Update for ParamMatrix - Added BS Service ID under 'Service ID' column.
                # gs.update_row(row, param_worksheet.col_count, param_worksheet, bs_service_id)
                logger.info(
                    f"\nWorksheet Updated: {param_worksheet}\nRow Updated: {row}"
                )
            else:
                logger.info("Additional Param not Found")

        # Click 'Add' button to submit.
        wd.perform_action("xpath", os.getenv("NF_ADD_BTN_INPUT"), "click")

        # Wait for the success message element to appear.
        wd.wait_until_element("xpath", "(//div[@id='content']//div)[1]", "visible")
        element_value = wd.driver.find_element(
            By.XPATH, "(//div[@id='content']//div)[1]"
        ).text

        # Get Steps unique ID from success message
        steps_id = get_after_word(element_value, "step")
        # steps_id = 1021
        logger.info(f"Retrieved STEPS ID: {steps_id} for EXTENDS FIRST EXPIRY")

        logger.info("STEPS EXTENDS FIRST EXPIRY SUCCESSFULLY DEFINED!")
        steps_type_id_name.append(steps_id)
        steps_type_id_name.append("EXTENDS_FIRST_EXPIRY")
        logger.info(f"List EXTENDS FIRST EXPIRY: {steps_type_id_name}")
        return steps_type_id_name

    except Exception as e:
        logger.info(
            f"An error has occurred while processing Step Type EXTENDS FIRST EXPIRY 'nf_steps_extends_first_expiry'\n ERROR: {e}"
        )

        wd.stop_process()


# Function to execute process for step type EXTENDS FIRST EXPIRY
def nf_steps_data_prov_with_keyword_mapping(
    bs_service_id, bs_row_data, param_worksheet
):
    try:
        steps_type_id_name = []
        # Redirect to Add Service Steps Page with service id
        wd.driver.get(
            f"{os.getenv('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
        )
        wd.wait_until_element("id", os.getenv("NF_STEPS_TYPE_DROPDOWN"), "visible")
        print("ARRIVE CURRENT PAGE: ADD STEP")

        # Call function 'nf_steps_default_input' to fill up default values
        nf_steps_default_input(
            bs_row_data[4],
            "//option[contains(text(), 'DATA PROV WITH KEYWORD MAPPING') and @value='95']",
        )

        # Input Jnetx Wallet Type Dropdown
        wd.perform_action(
            "xpath", f"//option[contains(text(), '{bs_row_data[4]}')]", "click"
        )

        # Input Default Wallet Keyword Field
        wd.perform_action(
            "xpath",
            f"(//input[@name='jnetxprov_walletkeywords2[]'])[1]",
            "sendkeys",
            "PR_GOEXTRA179GS8GB15DDVB",
        )

        # Input Default Data Alloc Field
        wd.perform_action(
            "xpath",
            f"(//input[@name='jnetxprov_dataallocs2[]'])[1]",
            "sendkeys",
            "8GB",
        )

        # Input Default Data Alloc Field
        wd.perform_action(
            "xpath",
            f"(//input[@name='jnetxprov_walletamounts2[]'])[1]",
            "sendkeys",
            8192,
        )

        # Input Default SDM Prov Keyword Field
        wd.perform_action(
            "xpath",
            f"(//input[@name='jnetxprov_sdmprovkeyword2[]'])[1]",
            "sendkeys",
            "PR_GOEXTRA179GS8GB15DDVB",
        )

        # Get ParamMatrix rows that equals to current Bulk service name
        bs_name_column = param_worksheet.col_count - 1
        param_matrix_rows = gs.get_param_pending_rows(
            param_worksheet, bs_row_data[1], bs_name_column, param_worksheet.col_count
        )
        if len(param_matrix_rows) != 0:
            logger.info(
                "Steps has multiple ParamMatrix for DATA PROV WITH KEYWORD MAPPING."
            )
            for index, row in enumerate(param_matrix_rows, 2):

                # Get ParamMatrix data values via row
                row_param_data = param_worksheet.row_values(row)

                logger.info("Filling up additional Param fields")
                # Click 'Add More Param to Wallet Keyword &Data Allocation Map' to add new field entry
                wd.perform_action(
                    "xpath",
                    "//a[@onclick='javascript: add_param_walletkeyword_dataalloc_field_sdm_prov();']",
                    "click",
                )

                logger.info(f"PARAM DATA PROV = ENTRY PARAM{index-1}")

                # Fill up Param Fields
                # Input Param Field
                wd.perform_action(
                    "xpath",
                    f"(//input[@name='jnetxprov_params2[]'])[{index}]",
                    "sendkeys",
                    row_param_data[0],
                )

                # Input Wallet Keyword Field
                wd.perform_action(
                    "xpath",
                    f"(//input[@name='jnetxprov_walletkeywords2[]'])[{index}]",
                    "sendkeys",
                    row_param_data[3],
                )

                # Input Data Alloc Field
                wd.perform_action(
                    "xpath",
                    f"(//input[@name='jnetxprov_dataallocs2[]'])[{index}]",
                    "sendkeys",
                    f"{int(row_param_data[4]) // 1024}GB",
                )

                # Input Wallet Amount Field
                wd.perform_action(
                    "xpath",
                    f"(//input[@name='jnetxprov_walletamounts2[]'])[{index}]",
                    "sendkeys",
                    row_param_data[4],
                )

                # Input Default SDM Prov Keyword Field
                wd.perform_action(
                    "xpath",
                    f"(//input[@name='jnetxprov_sdmprovkeyword2[]'])[{index}]",
                    "sendkeys",
                    "PR_GOEXTRA179GS8GB15DDVB",
                )

                # Worksheet Update for ParamMatrix - Added BS Service ID under 'Service ID' column.
                gs.update_row(
                    row, param_worksheet.col_count, param_worksheet, bs_service_id
                )
                logger.info(
                    f"\nWorksheet Updated: {param_worksheet}\nRow Updated: {row}"
                )
            else:
                logger.info("Additional Param not Found")

        # Click 'Add' button to submit.
        wd.perform_action("xpath", os.getenv("NF_ADD_BTN_INPUT"), "click")

        # Wait for the success message element to appear.
        wd.wait_until_element("xpath", "(//div[@id='content']//div)[1]", "visible")
        element_value = wd.driver.find_element(
            By.XPATH, "(//div[@id='content']//div)[1]"
        ).text

        # Get Steps unique ID from success message
        steps_id = get_after_word(element_value, "step")
        logger.info(
            f"Retrieved STEPS ID: {steps_id} for DATA PROV WITH KEYWORD MAPPING"
        )

        logger.info("STEPS EXTENDS FIRST EXPIRY SUCCESSFULLY DEFINED!")
        steps_type_id_name.append(steps_id)
        steps_type_id_name.append(bs_row_data[4])
        logger.info(f"List DATA PROV WITH KEYWORD MAPPING: {steps_type_id_name}")
        return steps_type_id_name

    except Exception as e:
        logger.info(
            f"An error has occurred while processing Step Type DATA PROV WITH KEYWORD MAPPING 'nf_steps_data_prov_with_keyword_mapping'\n ERROR: {e}"
        )
        wd.stop_process()


# Handle Service Steps Final Single Checkbox
def handle_steps_final(final_value):

    if final_value.lower() == "yes":
        wd.perform_action("name", os.getenv("NF_STEPS_FINAL_CHECKBOX"), "click")
    else:
        pass


def step_type_prepaid_ctl_with_data(bs_service_id, bs_row_data, param_worksheet):
    # Declare Dictionary variable
    dict_steps_type = {}

    # Execute Steps Type Process = IN CHARGE
    list_in_charge = nf_steps_in_charge(bs_service_id, bs_row_data, param_worksheet)
    # Added IN CHARGE ID to 'dict_steps_type' Dictionary/Object
    dict_steps_type = {
        "in_charge_id": list_in_charge[0],
        "in_charge_name": list_in_charge[1],
    }

    # Execute Steps Type Process = EXTENDS FIRST EXPIRY
    list_extend_first_expiry = nf_steps_extend_first_expiry(
        bs_service_id, bs_row_data, param_worksheet
    )
    # Added EXTEND FIRST EXPIRY to 'dict_steps_type' Dictionary/Object
    dict_steps_type["extend_first_expiry_id"] = list_extend_first_expiry[0]
    dict_steps_type["extend_first_expiry_name"] = list_extend_first_expiry[1]

    # Execute Steps Type Process = DATA PROV WITH KEYWORD MAPPING
    list_data_prov_with_keyword_mapping = nf_steps_data_prov_with_keyword_mapping(
        bs_service_id, bs_row_data, param_worksheet
    )
    # Added DATA PROV WITH KEYWORD MAPPING ID to 'dict_steps_type' Dictionary/Object
    dict_steps_type["data_prov_id"] = list_data_prov_with_keyword_mapping[0]
    dict_steps_type["data_prov_name"] = list_data_prov_with_keyword_mapping[1]

    logger.info(f"Retreived Success Step Type IDs: {dict_steps_type}")

    return dict_steps_type
