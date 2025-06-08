from selenium.webdriver.common.by import By
from utils import helpers as helper
from utils.env_loader import get_env_variable
from utils.logger import setup_logger
from utils.logger2 import logger
from nf.nf_constants import NfConstants

# Call Constants
nf = NfConstants()


# Function to start Step and Flow Construct Process for Prepaid CTL
def sf_construct_prepaid_ctl(
    double_extend_value, bs_service_id, bs_row_data, param_worksheet, webdriver, gsheet
):
    # Declare Global variable for Webdriver and Gsheet
    global wd
    global gs

    wd = webdriver
    gs = gsheet

    # Declare empty dictionary
    dict_step_type_data = {}
    dict_incharge_extend_data = {}
    step_flow_construct_value = bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT].lower()

    # Execute Step Type Processes [IN CHARGE and EXTEND FIRST EXPIRY] if double flow is false
    # Execute Step Type Process = IN CHARGE
    if double_extend_value != "double":
        logger.info("Processing IN CHARGE")
        in_charge_data = step_type_in_charge(
            double_extend_value, bs_service_id, bs_row_data, param_worksheet
        )
        dict_incharge_extend_data.update(in_charge_data)

        # Execute Step Type Process = EXTEND FIRST EXPIRY
        logger.info("Processing EXTEND FIRST EXPIRY")
        extend_first_expiry_data = step_type_extend_first_expiry(
            double_extend_value, bs_service_id, bs_row_data, param_worksheet
        )
        dict_incharge_extend_data.update(extend_first_expiry_data)
    else:
        logger.info("Skipping IN CHARGE and EXTEND FIRST EXPIRY - No Creation Needed")
        in_charge_data = {}
        extend_first_expiry_data = {}

    # If there's a 'data' keyword in Step and Flow Construct value, execute this Steps Type Process = DATA PROV WITH KEYWORD MAPPING or DATA PROV EXTENDS WITH KEYWORD MAPPING
    if "data" in step_flow_construct_value:
        logger.info("Processing DATA PROV PROCESS")
        data_volume_bulk_data = step_type_data_prov_process(
            double_extend_value, bs_service_id, bs_row_data, param_worksheet
        )

    else:
        data_volume_bulk_data = {}

    # If there's a 'Unli SMS' or 'Unli Voice' keyword in Step and Flow Construct value, execute this section: IN PROV SERVICE - UNLI SMS or IN PROV SERVICE - UNLI VOICE
    if (
        "unli sms" in step_flow_construct_value
        or "unli voice" in step_flow_construct_value
    ):
        # Conditions to execute Step Type IN PROV SERVICE/IN ADD WALLET FUP/IN EXTEND WALLET EXPIRY
        if double_extend_value == "double":
            logger.info("Processing IN ADD WALLET FUP")
            sms_voice_data = step_type_in_add_wallet_fup(
                double_extend_value, bs_service_id, bs_row_data
            )

        elif double_extend_value == "extend":
            logger.info("Processing IN EXTEND WALLET EXPIRY")
            "TODO"
        else:
            # Execute Step Type Process = IN PROV SERVICE - UNLI SMS and/or IN PROV SERVICE - UNLI VOICE
            logger.info("Processing IN PROV SERVICE")
            sms_voice_data = step_type_in_prov_service(
                double_extend_value, bs_service_id, bs_row_data
            )
    else:
        sms_voice_data = {}

    # Conditions to execute HLR PLY Step Type if there's a Unli Voice in Step and Flow Construct Value
    try:
        if (
            "unli voice" in step_flow_construct_value
            and double_extend_value != "double"
            and double_extend_value != "extend"
        ):

            # Execute Step Type Process = HLR PLY
            logger.info("Processing HLR - PLY")
            hlr_ply_data = step_type_hlr_ply(bs_service_id, bs_row_data)
            dict_incharge_extend_data.update(hlr_ply_data)

        else:
            logger.info("Skipping HLR PLY - No Creation Needed")
            hlr_ply_data = {}
    except Exception as e:
        logger.info("HL PLY FAILED - Continue Process..")

    # Add all keys and value to dict_step_type_data dictionary to use later for Flow process
    logger.info("Merging step data..")
    dict_step_type_data.update(
        {
            **in_charge_data,
            **extend_first_expiry_data,
            **data_volume_bulk_data,
            **sms_voice_data,
            **hlr_ply_data,
        }
    )
    logger.info(
        f"Successfully Retreived Step Type Ids and Names: {dict_step_type_data}"
    )

    return dict_step_type_data, dict_incharge_extend_data


# Function to enter default values to inputs
def nf_steps_default_input(name_value, steps_type_element, final_value=None):
    # Input Name Field
    wd.perform_action("xpath", nf.NF_INPUT_NAME, "sendkeys", name_value)

    # Select Bulk Service Dropdown DEFAULT = Current Bulk Service/Service ID
    wd.perform_action("xpath", steps_type_element, "click")

    # Checkbox Final Field
    if final_value:
        wd.perform_action("name", nf.NF_STEPS_FINAL_CHECKBOX, "click")

    # Input Retry Field
    wd.perform_action("name", nf.NF_STEPS_RETRY_INPUT, "sendkeys", 3)


# STEP TYPE 'IN CHARGE' Function to execute process for step type IN CHARGE
def step_type_in_charge(
    double_extend_value, bs_service_id, bs_row_data, param_worksheet
):
    try:
        logger.info("Executing Step Type: IN CHARGE")

        # Redirect to Add Service Steps Page with service id
        logger.info("Redirecting to Add Steps Page...")
        wd.driver.get(
            f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
        )
        wd.wait_until_element("id", nf.NF_STEPS_TYPE_DROPDOWN, "visible")
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

        # Click 'Add' button to submit and wait for the success message element to appear.
        wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
        wd.wait_until_element("xpath", "(//div[@id='content']//div)[1]", "visible")
        logger.info("STEP TYPE 'IN CHARGE' SUCCESSFULLY DEFINED!")

        element_value = wd.driver.find_element(
            By.XPATH, "(//div[@id='content']//div)[1]"
        ).text

        # Get Steps unique ID from success message
        steps_id = helper.get_after_word(element_value, "step")
        # steps_id = 1021

        logger.info(f"STEP ID Retrieved: {steps_id} for IN CHARGE")

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
        wd.stop_process()


# STEP TYPE 'EXTENDS FIRST EXPIRY' Function to execute process for step type EXTENDS FIRST EXPIRY
def step_type_extend_first_expiry(
    double_extend_value, bs_service_id, bs_row_data, param_worksheet
):
    try:
        logger.info("Executing Step Type: EXTEMD FORST EXPIRY")

        # Redirect to Add Service Steps Page with service id
        wd.driver.get(
            f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
        )
        wd.wait_until_element("id", nf.NF_STEPS_TYPE_DROPDOWN, "visible")
        logger.info("Step Add Page Successfully Reached!")

        # Call function 'nf_steps_default_input' to fill up default values
        nf_steps_default_input(
            "EXTEND_FIRST_EXPIRY",
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

        # Click 'Add' button to submit and wait for the success message element to appear.
        wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
        wd.wait_until_element("xpath", "(//div[@id='content']//div)[1]", "visible")
        logger.info("STEPS EXTENDS FIRST EXPIRY SUCCESSFULLY CREATED!")

        element_value = wd.driver.find_element(
            By.XPATH, "(//div[@id='content']//div)[1]"
        ).text

        # Get Steps unique ID from success message
        steps_id = helper.get_after_word(element_value, "step")
        # steps_id = 1021
        logger.info(f"Retrieved STEPS ID: {steps_id} for EXTENDS FIRST EXPIRY")

        # Set Step type result into Dictionary/Object then return
        dict_step_type_idname = {
            "extend_first_expiry_id": steps_id,
            "extend_first_expiry_name": "EXTEND_FIRST_EXPIRY",
        }

        logger.info(f"Step EXTENDS FIRST EXPIRY result: {dict_step_type_idname}")
        return dict_step_type_idname

    except Exception as e:
        logger.info(
            f"An error has occurred while processing Step Type EXTENDS FIRST EXPIRY 'nf_steps_extends_first_expiry'\n ERROR: {e}"
        )
        wd.stop_process()


# Function Step Type 'DATA PROV WITH KEYWORD MAPPING' or 'DATA PROV EXTENSION WITH KEYWORD MAPPING' process
def step_type_data_prov_process(
    double_extend_value, bs_service_id, bs_row_data, param_worksheet
):
    try:
        dict_step_type_idname = {}

        # Declare double_flow_true or extend_flow_true with boolean for double and extend flow handling
        double_flow_true = True if double_extend_value == "double" else False
        step_type_name = (
            "Data Prov Extension With Keyword Mapping"
            if double_extend_value == "double"
            else (
                "Data Extend Wallet Expiry"
                if double_extend_value == "extend"
                else "Data Prov With Keyword Mapping"
            )
        )

        # Declare Variable for Bulk Service Wallet Value
        bs_wallet = f"{double_extend_value.upper()}{'' if double_extend_value == '' else '_'}{bs_row_data[nf.NF_INDEX_WALLET]}"

        logger.info(f"Executing Step Type: {step_type_name.upper()}")

        # Redirect to Add Service Step Page with service id
        wd.driver.get(
            f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
        )
        wd.wait_until_element("id", nf.NF_STEPS_TYPE_DROPDOWN, "visible")
        logger.info("Add Step Page Successfully Reached! Filling up Step Fields...")

        # Call function 'nf_steps_default_input' to fill up the common fields
        # 95 = DATA PROV WITH KEYWORD MAPPING
        # 96 = DATA PROV EXTEND WITH KEYWORD MAPPING <= FOR DOUBLE FLOW
        nf_steps_default_input(
            bs_wallet,
            f"//select[@id='dd_stype_id']//option[@value='{96 if double_flow_true else 95}']",
        )
        # Section to Input Default Values from BS Worksheet
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

        # Get ParamMatrix rows that equals between ParamMatrix 'Service Name' and 'Bulk Service Name'
        bs_name_column = param_worksheet.col_count - 1
        param_matrix_rows = gs.get_param_pending_rows(
            param_worksheet,
            bs_row_data[nf.NF_INDEX_NAME],
            bs_name_column,
            param_worksheet.col_count,
        )
        # If bot didn't found available to fill up using parammatrix value, skip.
        if len(param_matrix_rows) != 0:
            logger.info(f"Steps has multiple ParamMatrix for {step_type_name}")
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
                    row_param_data[nf.NF_PARAMMATRIX_INDEX_PARAM],
                )

                # Input Wallet Keyword Field
                wd.perform_action(
                    "xpath",
                    f"(//input[@name='jnetxprov_walletkeywords2[]'])[{index}]",
                    "sendkeys",
                    row_param_data[nf.NF_PARAMMATRIX_INDEX_WALLET_KEYWORD],
                )

                # Input Data Alloc Field
                wd.perform_action(
                    "xpath",
                    f"(//input[@name='jnetxprov_dataallocs2[]'])[{index}]",
                    "sendkeys",
                    f"{int(row_param_data[nf.NF_PARAMMATRIX_INDEX_WALLET_AMOUNT]) // 1024}GB",
                )

                # Input Wallet Amount Field
                wd.perform_action(
                    "xpath",
                    f"(//input[@name='jnetxprov_walletamounts2[]'])[{index}]",
                    "sendkeys",
                    row_param_data[nf.NF_PARAMMATRIX_INDEX_WALLET_AMOUNT],
                )

                # Input Default SDM Prov Keyword Field
                wd.perform_action(
                    "xpath",
                    f"(//input[@name='jnetxprov_sdmprovkeyword2[]'])[{index}]",
                    "sendkeys",
                    bs_row_data[nf.NF_INDEX_DEFAULT_WALLET_KEYWORD],
                )

                # Worksheet Update for ParamMatrix - Added BS Service ID under 'Service ID' column.
                gs.update_row(
                    row,
                    param_worksheet.col_count,
                    param_worksheet,
                    bs_service_id,
                )
                logger.info(
                    f"\nWorksheet Updated: {param_worksheet}\nRow Updated: {row}"
                )
            else:
                logger.info("Additional Param not Found")

        # Click 'Add' button to submit and wait for the success message element to appear.
        wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
        wd.wait_until_element("xpath", "(//div[@id='content']//div)[1]", "visible")
        logger.info(f"STEP '{step_type_name.upper()}' SUCCESSFULLY CREATED!")

        # Get Steps unique ID from success message
        element_value = wd.driver.find_element(
            By.XPATH, "(//div[@id='content']//div)[1]"
        ).text
        step_id = helper.get_after_word(element_value, "step")
        logger.info(f"STEP ID Retrieved: {step_id} for {step_type_name.upper()}")

        # Declare dictionary step type data with step id and name to use it later for Flow sequence.
        dict_step_type_idname = {
            "data_prov_id": step_id,
            "data_prov_name": bs_wallet,
        }

        logger.info(
            f"Step Type {step_type_name.upper()} Data Result: {dict_step_type_idname}"
        )

        return dict_step_type_idname

    except Exception as e:
        logger.info(
            f"An error has occurred while processing Step Type {step_type_name.upper()} 'nf_steps_data_prov_with_keyword_mapping'\n ERROR: {e}"
        )
        wd.stop_process()


def step_type_in_add_wallet_fup(double_extend_value, bs_service_id, bs_row_data):
    try:
        dict_in_prov_data = {}
        step_flow_construct_value = bs_row_data[
            nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT
        ].lower()
        sms_voice_conditions = {
            # If Step and flow construct has Unli SMS
            "unli_sms": (True if "unli sms" in step_flow_construct_value else False),
            # If Step and flow construct has Unli Voice
            "unli_voice": (
                True if "unli voice" in step_flow_construct_value else False
            ),
        }

        for sms_voice_key, sms_voice_true in sms_voice_conditions.items():
            if sms_voice_true:
                # Declare double_extend_value and double_flow_true for double flow handling
                # Declare step_type_name
                step_type_name, double_flow_true = helper.nf_get_in_prov_values(
                    double_extend_value, sms_voice_key, "sms_voice_service"
                )
                if sms_voice_key == "unli_sms":
                    step_name = "DOUBLE_SMS_ALLNET_UNLI"
                    amount_field_value = (
                        500 if bs_row_data[nf.NF_INDEX_BRAND].lower() == "ghp" else 700
                    )
                else:
                    step_name = "DOUBLE_VOICE_ALLNET_UNLI"
                    amount_field_value = (
                        300 if bs_row_data[nf.NF_INDEX_BRAND].lower() == "ghp" else 200
                    )

                logger.info(f"Executing Step Type: {step_type_name.upper()}")

                # Redirect to Add Service Step Page with service id
                logger.info("Redirecting to Add Step Page...")
                wd.driver.get(
                    f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
                )
                wd.wait_until_element("id", nf.NF_STEPS_TYPE_DROPDOWN, "visible")
                logger.info(
                    "Add Step Page Successfully Reached! Filling up Step Fields..."
                )

                # Call function 'nf_steps_default_input' to fill up default field values
                nf_steps_default_input(
                    step_name,
                    f"//select[@id='dd_stype_id']//option[@value='129']",
                )

                # Input IN Serivce Field
                wd.perform_action(
                    "xpath",
                    f"//select[@name='in_fup_step_service']//option[@value='{196 if sms_voice_key == 'unli_sms' else 197}']",
                    "click",
                )

                # Amount
                wd.perform_action(
                    "name",
                    nf.NF_STEP_AMOUNT_FIELD,
                    "sendkeys",
                    amount_field_value,
                )

                # Click 'Add' button to submit and wait for the success message element to appear
                wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
                wd.wait_until_element(
                    "xpath", "(//div[@id='content']//div)[1]", "visible"
                )
                logger.info(
                    f"STEP FOR '{step_type_name.upper()}' SUCCESSFULLY CREATED!"
                )

                element_value = wd.driver.find_element(
                    By.XPATH, "(//div[@id='content']//div)[1]"
                ).text

                # Get Steps unique ID from success message
                # steps_id = 1021 #FOR TEST
                steps_id = helper.get_after_word(element_value, "step")
                logger.info("Step ID Collected")

                logger.info(f"STEP ID Retrieved: {steps_id} for {step_type_name}")

                # Set Step type result into Dictionary/Object then return
                dict_in_prov = {
                    f"{sms_voice_key}_id": steps_id,
                    f"{sms_voice_key}_name": step_name,
                }
                logger.info(f"Step type {step_type_name} result: {dict_in_prov}")
                dict_in_prov_data.update(dict_in_prov)

        return dict_in_prov_data

    except Exception as e:
        error_msg = f"An error has occurred while processing Step Type IN PROV SERVICE - UNLI SMS 'step_type_in_prov_service_sms'\n ERROR: {e}"
        logger.info(error_msg)
        raise Exception(error_msg)


def step_type_in_prov_service(double_extend_value, bs_service_id, bs_row_data):
    try:
        dict_in_prov_data = {}
        step_flow_construct_value = bs_row_data[
            nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT
        ].lower()
        sms_voice_conditions = {
            # If Step and flow construct has Unli SMS
            "unli_sms": (True if "unli sms" in step_flow_construct_value else False),
            # If Step and flow construct has Unli Voice
            "unli_voice": (
                True if "unli voice" in step_flow_construct_value else False
            ),
        }

        for sms_voice_key, sms_voice_true in sms_voice_conditions.items():
            if sms_voice_true:
                # Declare double_extend_value and double_flow_true for double flow handling
                # Declare step_type_name
                step_type_name, double_flow_true = helper.nf_get_in_prov_values(
                    double_extend_value, sms_voice_key, "sms_voice_service"
                )
                if sms_voice_key == "unli_sms":
                    step_name = "SMS_ALLNET_UNLI"
                    amount_field_value = (
                        500 if bs_row_data[nf.NF_INDEX_BRAND].lower() == "ghp" else 700
                    )
                else:
                    step_name = "VOICE_ALLNET_UNLI"
                    amount_field_value = (
                        300 if bs_row_data[nf.NF_INDEX_BRAND].lower() == "ghp" else 200
                    )

                logger.info(f"Executing Step Type: {step_type_name.upper()}")

                # Redirect to Add Service Step Page with service id
                logger.info("Redirecting to Add Step Page...")
                wd.driver.get(
                    f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
                )
                wd.wait_until_element("id", nf.NF_STEPS_TYPE_DROPDOWN, "visible")
                logger.info(
                    "Add Step Page Successfully Reached! Filling up Step Fields..."
                )

                # Call function 'nf_steps_default_input' to fill up default field values
                nf_steps_default_input(
                    step_name,
                    f"//select[@id='dd_stype_id']//option[@value='5']",
                )

                # Input IN Serivce Field
                wd.perform_action(
                    "xpath",
                    f"//select[@name='in_service_id']//option[@value='{196 if sms_voice_key == 'unli_sms' else 197}']",
                    "click",
                )

                wd.perform_action(
                    "name",
                    nf.NF_STEP_FUP_AMOUNT_FIELD,
                    "sendkeys",
                    amount_field_value,
                )

                # Click 'Add' button to submit and wait for the success message element to appear
                wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
                wd.wait_until_element(
                    "xpath", "(//div[@id='content']//div)[1]", "visible"
                )
                logger.info(f"STEP FOR '{step_type_name}' SUCCESSFULLY CREATED!")

                element_value = wd.driver.find_element(
                    By.XPATH, "(//div[@id='content']//div)[1]"
                ).text

                # Get Steps unique ID from success message
                # steps_id = 1021 #FOR TEST
                steps_id = helper.get_after_word(element_value, "step")
                logger.info("Step ID Collected")

                logger.info(f"STEP ID Retrieved: {steps_id} for {step_type_name}")

                # Set Step type result into Dictionary/Object then return
                dict_in_prov = {
                    f"{sms_voice_key}_id": steps_id,
                    f"{sms_voice_key}_name": step_name,
                }
                logger.info(f"Step type {step_type_name} result: {dict_in_prov}")
                dict_in_prov_data.update(dict_in_prov)

        return dict_in_prov_data

    except Exception as e:
        error_msg = f"An error has occurred while processing Step Type IN PROV SERVICE step_type_in_prov_service_sms'\n ERROR: {e}"
        logger.info(error_msg)
        wd.stop_process()


def step_type_hlr_ply(bs_service_id, bs_row_data):
    try:
        logger.info("Executing Step Type: HLR - PLY")

        # Redirect to Add Service Steps Page with service id
        logger.info("Redirecting to Add Steps Page...")
        wd.driver.get(
            f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
        )
        wd.wait_until_element("id", nf.NF_STEPS_TYPE_DROPDOWN, "visible")
        logger.info("Add Step Page Successfully Reached! Filling up Step Fields...")

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

        # Click 'Add' button to submit and wait for the success message element to appear.
        wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
        wd.wait_until_element("xpath", "(//div[@id='content']//div)[1]", "visible")
        logger.info("STEP FOR 'HLR PLY' SUCCESSFULLY CREATED!")

        element_value = wd.driver.find_element(
            By.XPATH, "(//div[@id='content']//div)[1]"
        ).text

        # Get Steps unique ID from success message
        steps_id = helper.get_after_word(element_value, "step")
        logger.info("Step ID Collected")
        # steps_id = 1021

        logger.info(f"Step ID Retrieved: {steps_id} for HLR PLY")

        # Set Step type result into Dictionary/Object then return
        dict_step_type_idname = {
            "hlr_ply_id": steps_id,
            "hlr_ply_name": "HLR_PLY",
        }
        logger.info(f"Step type HLR - PLY result: {dict_step_type_idname}")
        return dict_step_type_idname

    except Exception:
        logger.info(
            f"Failed to process step type 'HLR PLY', will proceed to defining Flow..."
        )


def modify_extend_first_expiry():
    "TODO"


def step_type_data_extend_wallet_expiry():
    "TODO"


def step_type_in_extend_wallet_expiry():
    "TODO"
