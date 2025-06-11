from selenium.webdriver.common.by import By
from utils import helpers as helper
from utils.env_loader import get_env_variable
from utils.logger import setup_logger
from utils.logger2 import logger
from nf.nf_constants import NfConstants

# Call Constants
nf = NfConstants()


# Function to start Step and Flow Construct Process for Prepaid CTL
def start_step_type_service(webdriver, gsheet):
    # Declare Global variable for Webdriver and Gsheet
    global wd
    global gs

    wd = webdriver
    gs = gsheet


# Function to enter default values to inputs
def nf_steps_default_input(name_value, steps_type_element, final_value=None):
    try:
        # Input Name Field
        wd.perform_action("xpath", nf.NF_INPUT_NAME, "sendkeys", name_value)

        # Select Bulk Service Dropdown DEFAULT = Current Bulk Service/Service ID
        wd.perform_action("xpath", steps_type_element, "click")

        # Checkbox Final Field
        if final_value:
            wd.perform_action("name", nf.NF_STEPS_FINAL_CHECKBOX, "click")

        # Input Retry Field
        wd.perform_action("name", nf.NF_STEPS_RETRY_INPUT, "sendkeys", 3)
    except Exception as e:
        logger.info(
            f"An error has occurred while fillinng up default values on 'nf_steps_default_input'\nERROR: {e}"
        )


# STEP TYPE 'IN CHARGE' Function to execute process for step type IN CHARGE
def step_type_in_charge(
    double_extend_value, bs_service_id, bs_row_data, param_worksheet
):
    try:
        logger.info("Executing Step Type: IN CHARGE")
        in_charge_name = (
            "EXTEND_CHARGE" if double_extend_value.lower() == "extend" else "IN_CHARGE"
        )
        param_amount = (
            nf.NF_INDEX_EXTEND_AMOUNT
            if double_extend_value.lower() == "extend"
            else nf.NF_INDEX_DEFAULT_AMOUNT
        )

        try:
            # Redirect to Add Service Steps Page with service id
            logger.info("Redirecting to Add Steps Page...")
            url_step_add_page = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"

            wd.driver.get(url_step_add_page)
            wd.wait_until_element("id", nf.NF_STEPS_TYPE_DROPDOWN, "visible")
        except Exception as e:
            logger.info(f"Unable to reach site {url_step_add_page}\n ERROR: {e}")

        logger.info("Step Add Page Successfully Reached!")

        # Call function 'nf_steps_default_input' to fill up default values
        nf_steps_default_input(
            in_charge_name, "//option[contains(text(), 'IN CHARGE') and @value='2']"
        )

        # Input Amount Field
        wd.perform_action(
            "name", "param_amt_ccode[0][amount]", "sendkeys", param_amount
        )

        # Get ParamMatrix rows that equals to current Bulk service name
        param_matrix_pending_rows = gs.get_param_pending_rows(
            param_worksheet,
            bs_row_data[nf.NF_INDEX_NAME],
            nf.COLUMN_PARAM_MATRIX_SERVICE_NAME,
            nf.COLUMN_PARAM_MATRIX_SERVICE_ID,
        )

        if len(param_matrix_pending_rows) != 0 and double_extend_value != "extend":

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
                    row_param_data[nf.INDEX_PARAM_MATRIX_PARAM],
                )
                # Input Amount Field
                wd.perform_action(
                    "name",
                    f"param_amt_ccode[{index}][amount] type=",
                    "sendkeys",
                    row_param_data[nf.INDEX_PARAM_MATRIX_AMOUNT],
                )
                # Worksheet Update for ParamMatrix - Add BS Service ID Value to ParamMatrix Service ID column
                # gs.update_row(row, param_worksheet.col_count, param_worksheet, bs_service_id)
                logger.info(
                    f"\nWorksheet Updated: {param_worksheet}\nRow Updated: {row}"
                )

        # Click 'Add' button to submit and wait for the success message element to appear.
        wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
        wd.wait_until_element("xpath", nf.STEP_SUCCESS_MESSAGE, "visible")
        logger.info("STEP TYPE 'IN CHARGE' SUCCESSFULLY DEFINED!")

        element_value = wd.driver.find_element(By.XPATH, nf.STEP_SUCCESS_MESSAGE).text

        # Get Steps unique ID from success message
        steps_id = helper.get_after_word(element_value, "step")
        # steps_id = 1021

        logger.info(f"STEP ID Retrieved: {steps_id} for IN CHARGE")

        # Set Step type result into Dictionary/Object then return
        dict_step_type_idname = {
            "in_charge_id": steps_id,
            "in_charge_name": in_charge_name,
        }
        logger.info(f"Step type IN CHARGE result: {dict_step_type_idname}")
        return dict_step_type_idname

    except Exception as e:
        error_msg = f"An error has occurred while processing Step Type IN CHARGE 'step_type_in_charge'\n ERROR: {e}"
        logger.info(error_msg)
        wd.stop_process()


# STEP TYPE 'EXTENDS FIRST EXPIRY' Function to execute process for step type EXTENDS FIRST EXPIRY
def step_type_extend_first_expiry(
    double_extend_value, old_step_id, bs_service_id, bs_row_data, param_worksheet
):
    try:
        # Section for Extend flow only. No Creation needed, Update existing step and add PARAM
        if double_extend_value == "extend":
            try:
                extend_data_id_name = modify_extend_first_expiry(
                    old_step_id,
                    bs_row_data[nf.NF_INDEX_EXTEND_AMOUNT],
                    bs_row_data[nf.NF_INDEX_EXTEND_DURATION_IN_DAYS],
                )
                return extend_data_id_name
            except Exception as e:
                logger.info(
                    f"An error has occurred in EXTEND FLOW - EXTEND FIRST EXPIRY\nERROR: {e}"
                )

        logger.info("Executing Step Type: EXTEND FIRST EXPIRY")

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
        wd.perform_action(
            "xpath",
            "(//input[@name='durations[]'])[1]",
            "sendkeys",
            nf.NF_INDEX_DEFAULT_DURATION_IN_DAYS,
        )

        # Get ParamMatrix rows that equals to current Bulk service name
        param_matrix_rows = gs.get_param_pending_rows(
            param_worksheet,
            bs_row_data[nf.NF_INDEX_NAME],
            nf.COLUMN_PARAM_MATRIX_SERVICE_NAME,
            nf.COLUMN_PARAM_MATRIX_SERVICE_ID,
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
        wd.wait_until_element("xpath", nf.STEP_SUCCESS_MESSAGE, "visible")
        logger.info("STEPS EXTENDS FIRST EXPIRY SUCCESSFULLY CREATED!")

        element_value = wd.driver.find_element(By.XPATH, nf.STEP_SUCCESS_MESSAGE).text

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
        param_matrix_rows = gs.get_param_pending_rows(
            param_worksheet,
            bs_row_data[nf.NF_INDEX_NAME],
            nf.COLUMN_PARAM_MATRIX_SERVICE_NAME,
            nf.COLUMN_PARAM_MATRIX_SERVICE_ID,
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
                    row_param_data[nf.INDEX_PARAM_MATRIX_PARAM],
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
                    nf.COLUMN_PARAM_MATRIX_SERVICE_ID,
                    param_worksheet,
                    bs_service_id,
                )
                # Worksheet Update for ParamMatrix for RPA Remarks.
                gs.update_row(
                    row,
                    nf.COLUMN_PARAM_MATRIX_RPA_REMARKS,
                    param_worksheet,
                    "PARAM Successfully Defined",
                )
                logger.info(
                    f"\nWorksheet Updated: {param_worksheet}\nRow Updated: {row}"
                )
            else:
                logger.info("Additional Param not Found")

        # Click 'Add' button to submit and wait for the success message element to appear.
        wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
        wd.wait_until_element("xpath", nf.STEP_SUCCESS_MESSAGE, "visible")
        logger.info(f"STEP '{step_type_name.upper()}' SUCCESSFULLY CREATED!")

        # Get Steps unique ID from success message
        element_value = wd.driver.find_element(By.XPATH, nf.STEP_SUCCESS_MESSAGE).text
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
                wd.wait_until_element("xpath", nf.STEP_SUCCESS_MESSAGE, "visible")
                logger.info(
                    f"STEP FOR '{step_type_name.upper()}' SUCCESSFULLY CREATED!"
                )

                element_value = wd.driver.find_element(
                    By.XPATH, nf.STEP_SUCCESS_MESSAGE
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
        wd.stop_process()


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

        # Start loop for unli sms and unli voice
        for sms_voice_key, sms_voice_true in sms_voice_conditions.items():
            if sms_voice_true:
                # Declare double_extend_value and double_flow_true for double flow handling
                # Declare step_type_name
                step_type_name, double_flow_true = helper.nf_get_in_prov_values(
                    double_extend_value, sms_voice_key, "sms_voice_service"
                )
                if sms_voice_key == "unli_sms":
                    brands = bs_row_data[nf.NF_INDEX_BRAND].lower()
                    step_name = "SMS_ALLNET_UNLI"

                    amount_field_value = 500 if brands == "ghp" else 700
                else:
                    step_name = "VOICE_ALLNET_UNLI"
                    amount_field_value = 300 if brands == "ghp" else 200

                logger.info(f"Executing Step Type: {step_type_name.upper()}")

                try:
                    # Redirect to Add Service Step Page with service id
                    logger.info("Redirecting to Add Step Page...")
                    url_step_page = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
                    wd.driver.get(url_step_page)
                    wd.wait_until_element("id", nf.NF_STEPS_TYPE_DROPDOWN, "visible")
                except Exception as e:
                    logger.info(f"Unable to reach site {url_step_page}\nERROR: {e}")

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
                wd.wait_until_element("xpath", nf.STEP_SUCCESS_MESSAGE, "visible")
                logger.info(f"STEP FOR '{step_type_name}' SUCCESSFULLY CREATED!")

                element_value = wd.driver.find_element(
                    By.XPATH, nf.STEP_SUCCESS_MESSAGE
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
        wd.wait_until_element("xpath", nf.STEP_SUCCESS_MESSAGE, "visible")
        logger.info("STEP FOR 'HLR PLY' SUCCESSFULLY CREATED!")

        element_value = wd.driver.find_element(By.XPATH, nf.STEP_SUCCESS_MESSAGE).text

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


def modify_extend_first_expiry(old_step_id, extend_amount, extend_duration):
    try:
        # Redirection to Edit page for Extend First Expiry using its old step id
        logger.info(f"OLD STEP ID: {old_step_id}")
        logger.info("Executing Step Type: EXTEND FLOW - EXTEND FIRST EXPIRY")
        url_step_edit_page = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=details&id={old_step_id}"
        wd.driver.get(url_step_edit_page)
        wd.wait_until_element("xpath", nf.EDIT_STEP_INPUT_FIELD_PARAM, "visible")
        logger.info(f"Site Successfully Reached! {url_step_edit_page}")

        # Input Amount Field for Extend Flow
        logger.info("Upating PARAM for existing Extend First Expiry")
        wd.perform_action(
            "xpath",
            nf.EDIT_STEP_INPUT_FIELD_PARAM,
            "sendkeys",
            extend_amount,
        )
        wd.perform_action(
            "xpath",
            nf.EDIT_STEP_INPUT_FIELD_DURATION,
            "sendkeys",
            extend_duration,
        )
        wd.perform_action("xpath", nf.NF_STEP_ADD_BTN_INPUT, "click")

        # Set Step type result into Dictionary/Object then return
        data_id_name = {
            "extend_first_expiry_id": old_step_id,
            "extend_first_expiry_name": "EXTEND_FIRST_EXPIRY",
        }
        logger.info(
            "STEP TYPE 'EXTEND FLOW - EXTEND FIRST EXPIRY' SUCCESSFULLY UPDATED"
        )
        return data_id_name
    except Exception as e:
        logger.info(
            f"An error has occurred in EXTEND FLOW - EXTEND FIRST EXPIRY\nERROR: {e}"
        )


def step_type_data_extend_wallet_expiry(bs_service_id, bs_row_data):
    try:

        # Declare wallet name
        bs_wallet = f"EXTEND_{bs_row_data[nf.NF_INDEX_WALLET]}"
        try:
            # Redirect to Add Service Step Page using service id
            logger.info("Redirecting to Add Step Page...")
            url_step_page = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
            wd.driver.get(url_step_page)
            wd.wait_until_element("id", nf.NF_STEPS_TYPE_DROPDOWN, "visible")
        except Exception as e:
            logger.info(f"Unable to reach site {url_step_page}\nERROR: {e}")

        logger.info("Add Step Page Successfully Reached! Filling up Step Fields...")

        # Section to Input Default Values from BS Worksheet
        # Call function 'nf_steps_default_input' to fill up default field values
        nf_steps_default_input(
            bs_wallet,
            nf.STEP_TYPE_DATA_EXTEND_WALLET_EXPIRY,
        )

        # Input Default Jnetx Wallet Type Dropdown
        wd.perform_action(
            "xpath",
            f"//select[@name='jnetx_wallet_type_id']//option[contains(text(), '{bs_row_data[nf.NF_INDEX_WALLET]}')][1]",
            "click",
        )

        # Input Expiry Field
        wd.perform_action(
            "xpath",
            f"(//input[@name='extend_step_expiries[]'])[1]",
            "sendkeys",
            f"{int(bs_row_data[nf.NF_INDEX_EXTEND_DURATION_IN_DAYS]) * 24}",
        )

        # Click 'Add' button to submit and wait for the success message element to appear.
        wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
        wd.wait_until_element("xpath", nf.STEP_SUCCESS_MESSAGE, "visible")
        logger.info(f"STEP 'DATA EXTEND WALLET EXPIRY' SUCCESSFULLY CREATED!")

        # Get Steps unique ID from success message
        element_value = wd.driver.find_element(By.XPATH, nf.STEP_SUCCESS_MESSAGE).text
        step_id = helper.get_after_word(element_value, "step")
        logger.info(f"STEP ID Retrieved: {step_id} for 'DATA EXTEND WALLET EXPIRY'")

        # Declare dictionary step type data with step id and name to use it later for Flow sequence.
        dict_step_type_idname = {
            "data_prov_id": step_id,
            "data_prov_name": bs_wallet,
        }

        logger.info(
            f"Step Type 'DATA EXTEND WALLET EXPIRY' Data Result: {dict_step_type_idname}"
        )

        return dict_step_type_idname

    except Exception as e:
        logger.info(
            f"An error has occurred in function of EXTEND DATA WALLET EXPIRY\nERROR: {e}"
        )


def step_type_in_extend_wallet_expiry(
    bs_service_id,
    bs_row_data,
):
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

        # Start loop for unli sms and unli voice
        for sms_voice_key, sms_voice_true in sms_voice_conditions.items():
            if sms_voice_true:
                step_name = (
                    "EXTEND_VOICE_ALLNET_UNLI"
                    if sms_voice_key == "unli_voice"
                    else "EXTEND_SMS_ALLNET_UNLI"
                )
                logger.info(f"Executing Step Type: IN EXTEND WALLET EXPIRY")

                try:
                    # Redirect to Add Service Step Page with service id
                    logger.info("Redirecting to Add Step Page...")
                    url_step_page = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
                    wd.driver.get(url_step_page)
                    wd.wait_until_element("id", nf.NF_STEPS_TYPE_DROPDOWN, "visible")
                except Exception as e:
                    logger.info(f"Unable to reach site {url_step_page}\nERROR: {e}")

                logger.info(
                    "Add Step Page Successfully Reached! Filling up Step Fields..."
                )

                # Call function 'nf_steps_default_input' to fill up default field values
                nf_steps_default_input(
                    step_name,
                    nf.STEP_TYPE_IN_EXTEND_WALLET_EXPIRY,
                )

                # Input IN Serivce Field
                wd.perform_action(
                    "xpath",
                    f"//select[@name='in_service_id']//option[@value='{196 if sms_voice_key == 'unli_sms' else 197}']",
                    "click",
                )

                # Input Expiry Field
                wd.perform_action(
                    "xpath",
                    f"(//input[@name='extend_step_expiries[]'])[1]",
                    "sendkeys",
                    f"{int(bs_row_data[nf.NF_INDEX_EXTEND_DURATION_IN_DAYS]) * 24}",
                )

                # Click 'Add' button to submit and wait for the success message element to appear
                wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
                wd.wait_until_element("xpath", nf.STEP_SUCCESS_MESSAGE, "visible")
                logger.info(f"STEP FOR 'IN EXTEND WALLET EXPIRY' SUCCESSFULLY CREATED!")

                element_value = wd.driver.find_element(
                    By.XPATH, nf.STEP_SUCCESS_MESSAGE
                ).text

                # Get Steps unique ID from success message
                # steps_id = 1021 #FOR TEST
                steps_id = helper.get_after_word(element_value, "step")
                logger.info("Step ID Collected")
                logger.info(
                    f"STEP ID Retrieved: {steps_id} for IN EXTEND WALLET EXPIRY"
                )

                # Set Step type result into Dictionary/Object then return
                dict_in_prov = {
                    f"{sms_voice_key}_id": steps_id,
                    f"{sms_voice_key}_name": step_name,
                }
                logger.info(
                    f"Step type 'IN EXTEND WALLET EXPIRY' result: {dict_in_prov}"
                )
                dict_in_prov_data.update(dict_in_prov)

        return dict_in_prov_data

    except Exception as e:
        error_msg = f"An error has occurred while processing Step Type IN EXTEND WALLET EXPIRY - step_type_in_extend_wallet_expiry'\n ERROR: {e}"
        logger.info(error_msg)
        wd.stop_process()
