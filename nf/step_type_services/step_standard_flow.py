from selenium.webdriver.common.by import By
from utils import helpers as helper
from utils.logger import setup_logger
from utils.logger2 import logger
from nf.nf_constants import NfConstants
import os

# Call Constants
nf = NfConstants()


# Function to start Step and Flow Construct Process for Prepaid CTL
def sf_construct_prepaid_ctl(
    bs_service_id, bs_row_data, param_worksheet, webdriver, gsheet
):
    # Declare Global variable for Webdriver and Gsheet
    global wd
    global gs

    wd = webdriver
    gs = gsheet

    # Declare empty dictionary
    dict_steps_type = {}

    # Execute Step Type Process = IN CHARGE
    in_charge_data = step_type_in_charge(bs_service_id, bs_row_data, param_worksheet)

    # Execute Step Type Process = EXTENDS FIRST EXPIRY
    extend_first_expiry_data = step_type_extend_first_expiry(
        bs_service_id, bs_row_data, param_worksheet
    )

    # If there's a 'data' keyword in Step and Flow Construct value, execute this Steps Type Process = DATA PROV WITH KEYWORD MAPPING
    if "data" in bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT].lower():
        # Execute Step Type Process = DATA PROV WITH KEYWORD MAPPING
        data_volume_bulk_data = step_type_data_prov_with_keyword_mapping(
            bs_service_id, bs_row_data, param_worksheet
        )
    else:
        data_volume_bulk_data = {}

    # If there's a 'unli sms' keyword in Step and Flow Construct value, execute this Steps Type Process = IN PROV SERVICE - UNLI SMS
    if "unli sms" in bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT].lower():
        # Execute Step Type Process = IN PROV SERVICE - UNLI SMS
        in_prov_sms_data = step_type_in_prov_service_sms(bs_service_id, bs_row_data)
    else:
        in_prov_sms_data = {}

    # If there's a 'unli voice' keyword in Step and Flow Construct value, execute this Steps Type Process = IN PROV SERVICE - UNLI VOICE
    if "unli voice" in bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT].lower():
        # Execute Step Type Process = IN PROV SERVICE - UNLI VOICE
        in_prov_voice_data = step_type_in_prov_service_voice(bs_service_id, bs_row_data)
        # Execute Step Type Process = HLR PLY
        hlr_ply_data = step_type_hlr_ply(bs_service_id, bs_row_data)
    else:
        in_prov_voice_data = {}
        hlr_ply_data = {}

    # Add all keys and value to dict_steps_type dictionary to use later for Flow process
    dict_steps_type.update(
        {
            **in_charge_data,
            **extend_first_expiry_data,
            **data_volume_bulk_data,
            **in_prov_sms_data,
            **in_prov_voice_data,
            **hlr_ply_data,
        }
    )
    logger.info(f"Successfully Retreived Step Type Ids and Names: {dict_steps_type}")

    return dict_steps_type


# Function to enter default values to inputs
def nf_steps_default_input(name_value, steps_type_element, final_value=None):
    # Input Name Field
    wd.perform_action("xpath", os.getenv("NF_INPUT_NAME"), "sendkeys", name_value)

    # Select Bulk Service Dropdown DEFAULT = Current Bulk Service/Service ID
    wd.perform_action("xpath", steps_type_element, "click")

    # Checkbox Final Field
    if final_value:
        wd.perform_action("name", nf.NF_STEPS_FINAL_CHECKBOX, "click")

    # Input Retry Field
    wd.perform_action("name", os.getenv("NF_STEPS_RETRY_INPUT"), "sendkeys", 3)


# STEP TYPE 'IN CHARGE' Function to execute process for step type IN CHARGE
def step_type_in_charge(bs_service_id, bs_row_data, param_worksheet):
    try:
        logger.info("Executing Step Type: IN CHARGE")

        # Redirect to Add Service Steps Page with service id
        logger.info("Redirecting to Add Steps Page...")
        wd.driver.get(
            f"{os.getenv('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
        )
        wd.wait_until_element("id", os.getenv("NF_STEPS_TYPE_DROPDOWN"), "visible")
        logger.info("Step Add Page Successfully Reached!")

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
            param_worksheet,
            bs_row_data[nf.NF_INDEX_NAME],
            bs_name_column,
            param_worksheet.col_count,
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
        wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")

        # Wait for the success message element to appear.
        wd.wait_until_element("xpath", "(//div[@id='content']//div)[1]", "visible")
        print("GET ELEMENT")
        element_value = wd.driver.find_element(
            By.XPATH, "(//div[@id='content']//div)[1]"
        ).text

        # Get Steps unique ID from success message
        steps_id = helper.get_after_word(element_value, "step")
        # steps_id = 1021

        logger.info(f"STEP ID Retrieved: {steps_id} for IN CHARGE")

        logger.info("STEP TYPE 'IN CHARGE' SUCCESSFULLY DEFINED!")

        # Set Step type result into Dictionary/Object then return
        dict_step_type_idname = {
            "in_charge_id": steps_id,
            "in_charge_name": "IN_CHARGE",
        }
        logger.info(f"Step type IN CHARGE result: {dict_step_type_idname}")
        return dict_step_type_idname

    except Exception as e:
        error_msg = f"An error has occurred while processing Step Type IN CHARGE 'step_type_in_charge'\n ERROR: {e}"
        logger.info(error_msg)
        raise Exception(error_msg)


# STEP TYPE 'EXTENDS FIRST EXPIRY' Function to execute process for step type EXTENDS FIRST EXPIRY
def step_type_extend_first_expiry(bs_service_id, bs_row_data, param_worksheet):
    try:
        logger.info("Executing Step Type: EXTEMD FORST EXPIRY")

        # Redirect to Add Service Steps Page with service id
        wd.driver.get(
            f"{os.getenv('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
        )
        wd.wait_until_element("id", os.getenv("NF_STEPS_TYPE_DROPDOWN"), "visible")
        logger.info("Step Add Page Successfully Reached!")

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
            param_worksheet,
            bs_row_data[nf.NF_INDEX_NAME],
            bs_name_column,
            param_worksheet.col_count,
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
        steps_id = helper.get_after_word(element_value, "step")
        # steps_id = 1021
        logger.info(f"Retrieved STEPS ID: {steps_id} for EXTENDS FIRST EXPIRY")

        logger.info("STEPS EXTENDS FIRST EXPIRY SUCCESSFULLY DEFINED!")

        # Set Step type result into Dictionary/Object then return
        dict_step_type_idname = {
            "extend_first_expiry_id": steps_id,
            "extend_first_expiry_name": "EXTENDS_FIRST_EXPIRY",
        }

        logger.info(f"Step EXTENDS FIRST EXPIRY result: {dict_step_type_idname}")
        return dict_step_type_idname

    except Exception as e:
        logger.info(
            f"An error has occurred while processing Step Type EXTENDS FIRST EXPIRY 'nf_steps_extends_first_expiry'\n ERROR: {e}"
        )

        wd.stop_process()


# STEP TYPE 'DATA PROV WITH KEYWORD MAPPING' Function to execute process for step type EXTENDS FIRST EXPIRY
def step_type_data_prov_with_keyword_mapping(
    bs_service_id, bs_row_data, param_worksheet
):
    try:
        logger.info("Executing Step Type: DATA PROV WITH KEYWORD MAPPING")

        # Redirect to Add Service Steps Page with service id
        wd.driver.get(
            f"{os.getenv('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
        )
        wd.wait_until_element("id", os.getenv("NF_STEPS_TYPE_DROPDOWN"), "visible")
        logger.info("Add Step Page Successfully Reached!")

        # Call function 'nf_steps_default_input' to fill up the common/generic fields
        nf_steps_default_input(
            bs_row_data[nf.NF_INDEX_WALLET],
            "//option[contains(text(), 'DATA PROV WITH KEYWORD MAPPING') and @value='95']",
        )

        # Section to Input Default Values
        # Input Default Jnetx Wallet Type Dropdown
        wd.perform_action(
            "xpath",
            f"//option[contains(text(), '{bs_row_data[nf.NF_INDEX_WALLET]}')]",
            "click",
        )

        # Input Default Wallet Keyword Field
        wd.perform_action(
            "xpath",
            f"(//input[@name='jnetxprov_walletkeywords2[]'])[1]",
            "sendkeys",
            bs_row_data[nf.NF_INDEX_WALLET],
        )

        # Input Default Data Alloc Field
        wd.perform_action(
            "xpath",
            f"(//input[@name='jnetxprov_dataallocs2[]'])[1]",
            "sendkeys",
            f"{int(bs_row_data[nf.NF_INDEX_DEFAULT_WALLET_AMOUNT]) // 1024}GB",
        )

        # Input Default Wallet Amount Field
        wd.perform_action(
            "xpath",
            f"(//input[@name='jnetxprov_walletamounts2[]'])[1]",
            "sendkeys",
            bs_row_data[nf.NF_INDEX_DEFAULT_WALLET_AMOUNT],
        )

        # Input Default SDM Prov Keyword Field
        wd.perform_action(
            "xpath",
            f"(//input[@name='jnetxprov_sdmprovkeyword2[]'])[1]",
            "sendkeys",
            bs_row_data[nf.NF_INDEX_DEFAULT_WALLET_KEYWORD],
        )

        # Get ParamMatrix rows that equals to current Bulk service name
        bs_name_column = param_worksheet.col_count - 1
        param_matrix_rows = gs.get_param_pending_rows(
            param_worksheet,
            bs_row_data[nf.NF_INDEX_NAME],
            bs_name_column,
            param_worksheet.col_count,
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
        steps_id = helper.get_after_word(element_value, "step")
        logger.info(
            f"Retrieved STEPS ID: {steps_id} for DATA PROV WITH KEYWORD MAPPING"
        )

        logger.info("STEPS EXTENDS FIRST EXPIRY SUCCESSFULLY DEFINED!")

        # Set Step type result into Dictionary/Object then return
        dict_step_type_idname = {
            "data_prov_id": steps_id,
            "data_prov_name": bs_row_data[nf.NF_INDEX_WALLET],
        }

        logger.info(
            f"Setp DATA PROV WITH KEYWORD MAPPING result: {dict_step_type_idname}"
        )
        return dict_step_type_idname

    except Exception as e:
        logger.info(
            f"An error has occurred while processing Step Type DATA PROV WITH KEYWORD MAPPING 'nf_steps_data_prov_with_keyword_mapping'\n ERROR: {e}"
        )
        wd.stop_process()


def step_type_in_prov_service_sms(bs_service_id, bs_row_data):
    try:
        logger.info("Executing Step Type: IN PROV SERVICE - UNLI SMS")

        # Redirect to Add Service Steps Page with service id
        logger.info("Redirecting to Add Steps Page...")
        wd.driver.get(
            f"{os.getenv('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
        )
        wd.wait_until_element("id", os.getenv("NF_STEPS_TYPE_DROPDOWN"), "visible")
        logger.info("Add Step Page Successfully Reached!")

        # Call function 'nf_steps_default_input' to fill up default field values
        nf_steps_default_input(
            "SMS_ALLNET_UNLI",
            "//option[contains(text(), 'IN PROV SERVICE') and @value='5']",
        )

        # Input IN Serivce Field
        wd.perform_action(
            "xpath",
            "//select[@name='in_service_id']//option[contains(text(), 'SMS_ALLNET_UNLI') and @value='196']",
            "click",
        )

        wd.perform_action(
            "name",
            nf.NF_STEP_FUP_AMOUNT_FIELD,
            "sendkeys",
            500 if bs_row_data[nf.NF_INDEX_BRAND].lower() == "ghp" else 700,
        )

        # Click 'Add' button to submit.
        wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")

        # Wait for the success message element to appear.
        logger.info("Getting Step ID...")
        wd.wait_until_element("xpath", "(//div[@id='content']//div)[1]", "visible")

        element_value = wd.driver.find_element(
            By.XPATH, "(//div[@id='content']//div)[1]"
        ).text

        # Get Steps unique ID from success message
        steps_id = helper.get_after_word(element_value, "step")
        logger.info("Step ID Collected")
        # steps_id = 1021

        logger.info(f"STEP ID Retrieved: {steps_id} for IN PROV SERVICE - UNLI SMS")
        logger.info("STEP FOR 'IN PROV SERVICE - UNLI SMS' SUCCESSFULLY CREATED!")

        # Set Step type result into Dictionary/Object then return
        dict_step_type_idname = {
            "in_prov_service_sms_id": steps_id,
            "in_prov_service_sms_name": "SMS_ALLNET_UNLI",
        }
        logger.info(
            f"Step type IN PROV SERVICE - UNLI SMS result: {dict_step_type_idname}"
        )
        return dict_step_type_idname

    except Exception as e:
        error_msg = f"An error has occurred while processing Step Type IN PROV SERVICE - UNLI SMS 'step_type_in_prov_service_sms'\n ERROR: {e}"
        logger.info(error_msg)
        raise Exception(error_msg)


def step_type_in_prov_service_voice(bs_service_id, bs_row_data):
    try:
        logger.info("Executing Step Type: IN PROV SERVICE - UNLI VOICE")

        # Redirect to Add Service Steps Page with service id
        logger.info("Redirecting to Add Steps Page...")
        wd.driver.get(
            f"{os.getenv('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
        )
        wd.wait_until_element("id", os.getenv("NF_STEPS_TYPE_DROPDOWN"), "visible")
        logger.info("Add Step Page Successfully Reached!")

        # Call function 'nf_steps_default_input' to fill up default field values
        nf_steps_default_input(
            "VOICE_ALLNET_UNLI",
            "//option[contains(text(), 'IN PROV SERVICE') and @value='5']",
            "yes",
        )

        # Checkbox Final Field
        wd.perform_action("name", nf.NF_STEPS_FINAL_CHECKBOX, "click")

        # Input IN Serivce Field
        wd.perform_action(
            "xpath",
            "//select[@name='in_service_id']//option[contains(text(), 'VOICE_ALLNET_UNLI') and @value='197']",
            "click",
        )
        # Input FUP Amount Field
        wd.perform_action(
            "name",
            nf.NF_STEP_FUP_AMOUNT_FIELD,
            "sendkeys",
            300 if bs_row_data[nf.NF_INDEX_BRAND].lower() == "ghp" else 200,
        )

        # Click 'Add' button to submit.
        wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")

        # Wait for the success message element to appear.
        logger.info("Getting Step ID...")
        wd.wait_until_element("xpath", "(//div[@id='content']//div)[1]", "visible")

        element_value = wd.driver.find_element(
            By.XPATH, "(//div[@id='content']//div)[1]"
        ).text

        # Get Steps unique ID from success message
        steps_id = helper.get_after_word(element_value, "step")
        logger.info("Step ID Collected")
        # steps_id = 1021

        logger.info(f"STEP ID Retrieved: {steps_id} for IN PROV SERVICE - UNLI VOICE")
        logger.info("STEP FOR 'IN PROV SERVICE - UNLI VOICE' SUCCESSFULLY CREATED!")

        # Set Step type result into Dictionary/Object then return
        dict_step_type_idname = {
            "in_prov_service_voice_id": steps_id,
            "in_prov_service_voice_name": "VOICE_ALLNET_UNLI",
        }
        logger.info(
            f"Step type IN PROV SERVICE - UNLI VOICE result: {dict_step_type_idname}"
        )
        return dict_step_type_idname

    except Exception as e:
        error_msg = f"An error has occurred while processing Step Type IN PROV SERVICE - UNLI VOICE 'step_type_in_prov_service_voice'\n ERROR: {e}"
        logger.info(error_msg)
        raise Exception(error_msg)


def step_type_hlr_ply(bs_service_id, bs_row_data):
    try:
        logger.info("Executing Step Type: HLR - PLY")

        # Redirect to Add Service Steps Page with service id
        logger.info("Redirecting to Add Steps Page...")
        wd.driver.get(
            f"{os.getenv('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
        )
        wd.wait_until_element("id", os.getenv("NF_STEPS_TYPE_DROPDOWN"), "visible")
        logger.info("Add Step Page Successfully Reached!")

        # Call function 'nf_steps_default_input' to fill up default field values
        nf_steps_default_input(
            "HLR_PLY",
            "//option[contains(text(), 'HLR PLY') and @value='40']",
        )

        # Input HLR Ply Service Dropdown Field
        wd.perform_action(
            "xpath",
            (
                "//select[@name='hlr_ply_service_id']//option[@value='3']"
                if bs_row_data[nf.NF_INDEX_BRAND].lower() == "ghp"
                else "//select[@name='hlr_ply_service_id']//option[@value='2']"
            ),
            "click",
        )

        # Click 'Add' button to submit.
        wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")

        # Wait for the success message element to appear.
        logger.info("Getting Step ID...")
        wd.wait_until_element("xpath", "(//div[@id='content']//div)[1]", "visible")

        element_value = wd.driver.find_element(
            By.XPATH, "(//div[@id='content']//div)[1]"
        ).text

        # Get Steps unique ID from success message
        steps_id = helper.get_after_word(element_value, "step")
        logger.info("Step ID Collected")
        # steps_id = 1021

        logger.info(f"STEP ID Retrieved: {steps_id} for HLR PLY")
        logger.info("STEP FOR 'HLR PLY' SUCCESSFULLY CREATED!")

        # Set Step type result into Dictionary/Object then return
        dict_step_type_idname = {
            "hlr_ply_id": steps_id,
            "hlr_ply_name": "HLR_PLY",
        }
        logger.info(
            f"Step type IN PROV SERVICE - UNLI VOICE result: {dict_step_type_idname}"
        )
        return dict_step_type_idname

    except Exception:
        logger.info(
            f"Failed to process step type 'HLR PLY', will proceed to defining Flow..."
        )
