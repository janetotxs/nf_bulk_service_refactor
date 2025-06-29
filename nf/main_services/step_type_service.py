from selenium.webdriver.common.by import By
from utils import helpers as helper
from utils.env_loader import get_env_variable
from utils.logger import setup_logger
from utils.logger2 import logger
from nf.nf_constants import NfConstants
from selenium.common.exceptions import TimeoutException
import time

# Call Constants
nf = NfConstants()


class StepTypeService:
    def __init__(self, webdriver, gsheet, worksheets):
        self.wd = webdriver
        self.gs = gsheet
        self.worksheets = worksheets
        self.row = None
        self.double_extend_value = None
        self.bs_row_data = None
        self.rpa_column = None
        self.url_step_page = None
        self.param_rows = []
        self.bs_rpa_remark_fail = {}
        self.param_rpa_remark_fail = {}

    # Function to setup the reusable variables
    def initial_setup(self, row, double_extend_value, bs_row_data, bs_service_id):
        logger.info("Initializing Step Service..")
        self.row = row
        self.double_extend_value = double_extend_value
        self.bs_row_data = bs_row_data
        self.url_step_page = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
        self.rpa_column = (
            nf.COLUMN_BULK_SERVICE_RPA_REMARKS_EXTEND_FLOW
            if double_extend_value == "extend"
            else (
                nf.COLUMN_BULK_SERVICE_RPA_REMARKS_DOUBLE_FLOW
                if double_extend_value == "double"
                else nf.BS_INDEX_RPA_REMARKS_BASE_FLOW
            )
        )
        # Get ParamMatrix rows that equals to current Bulk service name
        logger.info(
            f"Checking for ParamMatrix Values For this Service Name: {bs_row_data[nf.NF_INDEX_NAME]}"
        )
        self.param_rows = self.gs.get_rows_by_name(
            self.worksheets["paramMatrix"], bs_row_data[nf.NF_INDEX_NAME]
        )
        logger.info("Step Service Initialized.")

    # Function to enter default values to inputs
    def nf_steps_default_input(
        self, name_value, steps_type_element, final_value=None, sms_voice=None
    ):
        try:
            logger.info("Filling up step fields...")
            # Input Name Field
            logger.info(f"Input Name: {name_value}")
            self.wd.perform_action("xpath", nf.NF_INPUT_NAME, "sendkeys", name_value)

            # Select Bulk Service Dropdown DEFAULT = Current Bulk Service/Service ID
            logger.info(f"Select Step Type: {steps_type_element}")
            self.wd.perform_action("xpath", steps_type_element, "click")

            # Checkbox Final Field
            if sms_voice:
                if "voice" in sms_voice:
                    logger.info(f"Checkbox Final: Checked")
                    self.wd.perform_action("name", nf.NF_STEPS_FINAL_CHECKBOX, "click")

            # Input Retry Field
            logger.info(f"Input Retry: 3")
            self.wd.perform_action("name", nf.NF_STEPS_RETRY_INPUT, "sendkeys", 3)

        except Exception as e:
            logger.info(
                f"An error has occurred while entering default values. Function 'nf_steps_default_input'\nERROR: {e}"
            )

    # STEP TYPE 'IN CHARGE' Function to execute process for step type IN CHARGE
    def step_type_in_charge(
        self,
        param_worksheet,
        retry=1,
        max_retries=2,
    ):
        logger.info("Executing Step Type: IN CHARGE")
        in_charge_name = (
            "EXTEND_CHARGE"
            if self.double_extend_value.lower() == "extend"
            else "IN_CHARGE"
        )
        while retry < max_retries + 1:
            try:
                # Redirect to Add Step Page
                self.wd.redirect_to_page(self.url_step_page, nf.NF_ADD_BTN_INPUT)
                # self.wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")

                param_amount = (
                    self.bs_row_data[nf.NF_INDEX_EXTEND_AMOUNT]
                    if self.double_extend_value.lower() == "extend"
                    else self.bs_row_data[nf.NF_INDEX_DEFAULT_AMOUNT]
                )

                # Call function 'nf_steps_default_input' to fill up default values
                self.nf_steps_default_input(
                    in_charge_name,
                    "//option[contains(text(), 'IN CHARGE') and @value='2']",
                )

                # Input Amount Field
                logger.info("Input Param: DEFAULT")
                logger.info(f"Input Amount: {param_amount}")
                self.wd.perform_action(
                    "name", "param_amt_ccode[0][amount]", "sendkeys", param_amount
                )

                if len(self.param_rows) != 0 and self.double_extend_value != "extend":
                    logger.info(
                        "Filling up step type sub fields using ParamMatrix values.."
                    )
                    for index, row in enumerate(self.param_rows, 1):
                        try:
                            # Get ParamMatrix data values via row
                            row_param_data = param_worksheet.row_values(row)
                            logger.info(f"Param Row: {row}")
                            # Click 'Add more Param - Amount - Charge Code' to add new field entry
                            self.wd.perform_action(
                                "xpath",
                                "//a[@onclick='javascript: add_param_amount_chargecode_field();']",
                                "click",
                            )

                            # Fill up Param Field
                            logger.info(
                                f"Input Param: {row_param_data[nf.INDEX_PARAM_MATRIX_PARAM]}"
                            )
                            self.wd.perform_action(
                                "name",
                                f"param_amt_ccode[{index}][param] type=",
                                "sendkeys",
                                row_param_data[nf.INDEX_PARAM_MATRIX_PARAM],
                            )
                            # Input Amount Field
                            logger.info(
                                f"Input Amount: {row_param_data[nf.INDEX_PARAM_MATRIX_AMOUNT]}"
                            )
                            self.wd.perform_action(
                                "name",
                                f"param_amt_ccode[{index}][amount] type=",
                                "sendkeys",
                                row_param_data[nf.INDEX_PARAM_MATRIX_AMOUNT],
                            )
                        except Exception as e:
                            logger.info(
                                f"An error has occurred while using paramMatrix values, will continue to next step.."
                            )
                            # Store ParamMatrix RPA Remark Failed in hashmap
                            self.param_rpa_remark_fail[in_charge_name] = "Failed"
                else:
                    logger.info(
                        f"No ParamMatrix found for this service name {self.bs_row_data[nf.NF_INDEX_NAME]}, will proceed to next step.."
                    )

                # Section to get success message after clicking submit button
                element_value = self.wd.submit_form_and_wait_for_success(
                    "xpath", nf.NF_ADD_BTN_INPUT, nf.STEP_SUCCESS_MESSAGE
                )

                logger.info("STEP TYPE 'IN CHARGE' SUCCESSFULLY DEFINED!")

                # Get Steps unique ID from success message
                steps_id = helper.get_after_word(element_value, "step")
                logger.info(f"STEP ID Retrieved: {steps_id} for IN CHARGE")

                # Set Step type result into Dictionary/Object then return
                dict_step_type_idname = {
                    "in_charge_id": steps_id,
                    "in_charge_name": in_charge_name,
                }
                logger.info(f"Step type IN CHARGE result: {dict_step_type_idname}")
                return dict_step_type_idname

            except Exception as e:
                if retry == max_retries:
                    logger.error(
                        f"An error has occurred while processing Step Type IN CHARGE 'step_type_in_charge'\n ERROR: {e}"
                    )
                    # Store RPA Remark failed to hashmap
                    self.bs_rpa_remark_fail[in_charge_name] = "Failed"
                    break

                # Trigger continue loop
                retry += 1
                logger.warning(f"Failed to create step type IN CHARGE, retrying...")

    # STEP TYPE 'EXTENDS FIRST EXPIRY' Function to execute process for step type EXTENDS FIRST EXPIRY
    def step_type_extend_first_expiry(
        self,
        bs_service_id,
        param_worksheet,
        old_step_id=None,
        retry=1,
        max_retries=2,
    ):
        while retry < max_retries + 1:
            try:
                # Section for Extend flow only. No Creation needed, Update existing step and add PARAM
                if self.double_extend_value == "extend":
                    try:
                        extend_data_id_name = self.modify_extend_first_expiry(
                            old_step_id,
                            self.bs_row_data[nf.NF_INDEX_EXTEND_AMOUNT],
                            self.bs_row_data[nf.NF_INDEX_EXTEND_DURATION_IN_DAYS],
                        )

                        return extend_data_id_name
                    except Exception as e:
                        logger.info(
                            f"An error has occurred in EXTEND FLOW - EXTEND FIRST EXPIRY\nERROR: {e}"
                        )

                logger.info("Executing Step Type: EXTEND FIRST EXPIRY")
                # Redirect to Add Step Page
                self.wd.redirect_to_page(self.url_step_page, nf.NF_ADD_BTN_INPUT)
                # self.wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")

                # Call function 'nf_steps_default_input' to fill up default values
                self.nf_steps_default_input(
                    "EXTEND_FIRST_EXPIRY",
                    "//option[contains(text(), 'EXTEND FIRST EXPIRY') and @value='19']",
                )

                # Input Default Amount Field
                logger.info(f"Input Default Param: DEFAULT")
                logger.info(
                    f"Input Default Durations: {self.bs_row_data[nf.NF_INDEX_DEFAULT_DURATION_IN_DAYS]} (days)"
                )
                self.wd.perform_action(
                    "xpath",
                    "(//input[@name='durations[]'])[1]",
                    "sendkeys",
                    self.bs_row_data[nf.NF_INDEX_DEFAULT_DURATION_IN_DAYS],
                )

                if len(self.param_rows) != 0:
                    logger.info(
                        "Filling up step type sub fields using ParamMatrix values.."
                    )
                    try:
                        for index, row in enumerate(self.param_rows, 2):
                            # Get ParamMatrix data values via row
                            row_param_data = param_worksheet.row_values(row)
                            logger.info(
                                f"Param Row: {row} - {index} - data: {row_param_data}"
                            )
                            # Click 'Add more Param & Duration' to add new field entry
                            self.wd.perform_action(
                                "xpath",
                                "//a[@onclick='javascript: add_param_duration_field();']",
                                "click",
                            )

                            # Fill up Param Field
                            # Input Amount Field
                            logger.info(
                                f"Input Param: {row_param_data[nf.NF_PARAMMATRIX_INDEX_PARAM]}"
                            )
                            self.wd.perform_action(
                                "xpath",
                                f"(//input[@name='pars[]'])[{index}]",
                                "sendkeys",
                                row_param_data[nf.NF_PARAMMATRIX_INDEX_PARAM],
                            )
                            # Input Duration Field
                            logger.info(
                                f"Input Duration: {row_param_data[nf.NF_PARAMMATRIX_INDEX_DURATION_IN_DAYS]} (days)"
                            )
                            self.wd.perform_action(
                                "xpath",
                                f"(//input[@name='durations[]'])[{index}]",
                                "sendkeys",
                                row_param_data[
                                    nf.NF_PARAMMATRIX_INDEX_DURATION_IN_DAYS
                                ],
                            )

                            # Worksheet Update for ParamMatrix - Add BS Service Id to Param Service Id Column for each row.
                            self.gs.update_row(
                                row,
                                nf.COLUMN_PARAM_MATRIX_SERVICE_ID,
                                param_worksheet,
                                bs_service_id,
                            )

                            logger.info(
                                f"Worksheet Updated: {param_worksheet} Row Updated: {row}"
                            )
                    except Exception as e:
                        logger.info(
                            f"An error has occurred while using paramMatrix values, will continue to next step..\nERROR {e}"
                        )
                        # store paramMatrix RPA Remark failed to hashmap
                        self.param_rpa_remark_fail["EXTEND_FIRST_EXPIRY"] = "Failed"
                else:
                    logger.info(
                        f"No ParamMatrix found for this service name {self.bs_row_data[nf.NF_INDEX_NAME]}, will proceed to next step.."
                    )

                # Section to get success message after clicking submit button
                element_value = self.wd.submit_form_and_wait_for_success(
                    "xpath", nf.NF_ADD_BTN_INPUT, nf.STEP_SUCCESS_MESSAGE
                )

                logger.info("STEPS EXTENDS FIRST EXPIRY SUCCESSFULLY CREATED!")

                # Get Steps unique ID from success message
                steps_id = helper.get_after_word(element_value, "step")
                # steps_id = 1021
                logger.info(f"Retrieved STEPS ID: {steps_id} for EXTENDS FIRST EXPIRY")

                # Set Step type result into Dictionary/Object then return
                dict_step_type_idname = {
                    "extend_first_expiry_id": steps_id,
                    "extend_first_expiry_name": "EXTEND_FIRST_EXPIRY",
                }

                logger.info(
                    f"Step EXTENDS FIRST EXPIRY result: {dict_step_type_idname}"
                )
                return dict_step_type_idname

            except Exception as e:
                if retry == max_retries:
                    logger.error(
                        f"An error has occurred while processing Step Type EXTENDS FIRST EXPIRY 'nf_steps_extends_first_expiry'\n ERROR: {e}"
                    )
                    # store rpa remark to hashmap
                    self.bs_rpa_remark_fail["EXTEND_FIRST_EXPIRY"] = "Failed"
                    break

                # Trigger continue loop
                retry += 1
                logger.warning(
                    f"Failed to create step type EXTEND FIRST EXPIRY, retrying..."
                )
                time.sleep(2)

    # Function Step Type 'DATA PROV WITH KEYWORD MAPPING' or 'DATA PROV EXTENSION WITH KEYWORD MAPPING' process
    def step_type_data_prov_process(
        self,
        bs_service_id,
        param_worksheet,
        retry=1,
        max_retries=2,
    ):
        while retry < max_retries + 1:
            try:
                logger.info("PROCESSING DATA PROV PROCESS")
                dict_step_type_idname = {}

                # Declare double_flow_true or extend_flow_true with boolean for double and extend flow handling
                double_flow_true = (
                    True if self.double_extend_value == "double" else False
                )
                step_type_name = (
                    "Data Prov Extension With Keyword Mapping"
                    if self.double_extend_value == "double"
                    else (
                        "Data Extend Wallet Expiry"
                        if self.double_extend_value == "extend"
                        else "Data Prov With Keyword Mapping"
                    )
                )

                # Declare Variable for Bulk Service Wallet Value
                bs_wallet = f"{self.double_extend_value.upper()}{'' if self.double_extend_value == '' else '_'}{self.bs_row_data[nf.NF_INDEX_WALLET]}"

                logger.info(f"Executing Step Type: {step_type_name.upper()}")
                # Redirect to Add Step Page
                self.wd.redirect_to_page(self.url_step_page, nf.NF_ADD_BTN_INPUT)
                # self.wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")

                # Call function 'nf_steps_default_input' to fill up the common fields
                # 95 = DATA PROV WITH KEYWORD MAPPING
                # 96 = DATA PROV EXTEND WITH KEYWORD MAPPING <= FOR DOUBLE FLOW
                self.nf_steps_default_input(
                    bs_wallet,
                    f"//select[@id='dd_stype_id']//option[@value='{96 if double_flow_true else 95}']",
                )
                # Section to Input Default Values from BS Worksheet
                # Input Default Jnetx Wallet Type Dropdown
                self.wd.perform_action(
                    "xpath",
                    f"//select[@name='jnetx_wallet_type_id']//option[contains(text(), '{self.bs_row_data[nf.NF_INDEX_WALLET]}')][1]",
                    "click",
                )

                # Input Default Wallet Keyword Field
                logger.info("Input Default Param: DEFAULT")
                logger.info(
                    f"Input Default Wallet Keyword: {self.bs_row_data[nf.NF_INDEX_WALLET]}"
                )
                self.wd.perform_action(
                    "xpath",
                    f"(//input[@name='jnetxprov_walletkeywords2[]'])[1]",
                    "sendkeys",
                    self.bs_row_data[nf.NF_INDEX_WALLET],
                )

                # Input Default Data Alloc Field
                data_alloc = f"{int(self.bs_row_data[nf.NF_INDEX_DEFAULT_WALLET_AMOUNT]) // 1024}GB"
                logger.info(f"Input Default Data Alloc: {data_alloc}")
                self.wd.perform_action(
                    "xpath",
                    f"(//input[@name='jnetxprov_dataallocs2[]'])[1]",
                    "sendkeys",
                    data_alloc,
                )

                # Input Default Wallet Amount Field
                logger.info(
                    f"Input Default Wallet Amount: {self.bs_row_data[nf.NF_INDEX_DEFAULT_WALLET_AMOUNT]}"
                )
                self.wd.perform_action(
                    "xpath",
                    f"(//input[@name='jnetxprov_walletamounts2[]'])[1]",
                    "sendkeys",
                    self.bs_row_data[nf.NF_INDEX_DEFAULT_WALLET_AMOUNT],
                )

                # Input Default SDM Prov Keyword Field
                logger.info(
                    f"Input Default SDM Prov Keyword: {self.bs_row_data[nf.NF_INDEX_DEFAULT_WALLET_KEYWORD]}"
                )
                self.wd.perform_action(
                    "xpath",
                    f"(//input[@name='jnetxprov_sdmprovkeyword2[]'])[1]",
                    "sendkeys",
                    self.bs_row_data[nf.NF_INDEX_DEFAULT_WALLET_KEYWORD],
                )

                # If bot didn't found available to fill up using parammatrix value, skip.
                if len(self.param_rows) != 0:
                    logger.info(
                        "Filling up step type sub fields using ParamMatrix values.."
                    )
                    try:
                        for index, row in enumerate(self.param_rows, 2):
                            # Get ParamMatrix data values via row
                            row_param_data = param_worksheet.row_values(row)
                            logger.info(f"Param Row: {row}")
                            # Click 'Add More Param to Wallet Keyword &Data Allocation Map' to add new field entry
                            self.wd.perform_action(
                                "xpath",
                                "//a[@onclick='javascript: add_param_walletkeyword_dataalloc_field_sdm_prov();']",
                                "click",
                            )

                            # Fill up Param Fields
                            # Input Param Field
                            logger.info(
                                f"Input Param: {row_param_data[nf.INDEX_PARAM_MATRIX_PARAM]}"
                            )
                            self.wd.perform_action(
                                "xpath",
                                f"(//input[@name='jnetxprov_params2[]'])[{index}]",
                                "sendkeys",
                                row_param_data[nf.INDEX_PARAM_MATRIX_PARAM],
                            )

                            # Input Wallet Keyword Field
                            logger.info(
                                f"Input Wallet Keyword: {row_param_data[nf.NF_PARAMMATRIX_INDEX_WALLET_KEYWORD]}"
                            )
                            self.wd.perform_action(
                                "xpath",
                                f"(//input[@name='jnetxprov_walletkeywords2[]'])[{index}]",
                                "sendkeys",
                                row_param_data[nf.NF_PARAMMATRIX_INDEX_WALLET_KEYWORD],
                            )

                            # Input Data Alloc Field
                            data_alloc_param = f"{int(row_param_data[nf.NF_PARAMMATRIX_INDEX_WALLET_AMOUNT]) // 1024}GB"
                            logger.info(f"Input Data Alloc: {data_alloc_param}")
                            self.wd.perform_action(
                                "xpath",
                                f"(//input[@name='jnetxprov_dataallocs2[]'])[{index}]",
                                "sendkeys",
                                data_alloc_param,
                            )

                            # Input Wallet Amount Field
                            logger.info(
                                f"Input Wallet Amount: {row_param_data[nf.NF_PARAMMATRIX_INDEX_WALLET_AMOUNT]}"
                            )
                            self.wd.perform_action(
                                "xpath",
                                f"(//input[@name='jnetxprov_walletamounts2[]'])[{index}]",
                                "sendkeys",
                                row_param_data[nf.NF_PARAMMATRIX_INDEX_WALLET_AMOUNT],
                            )

                            # # Input Default SDM Prov Keyword Field
                            # logger.info(
                            #     f"Input SDM Prov Keyword: {row_param_data[nf.]}"
                            # )
                            # self.wd.perform_action(
                            #     "xpath",
                            #     f"(//input[@name='jnetxprov_sdmprovkeyword2[]'])[{index}]",
                            #     "sendkeys",
                            #     row_param_data[nf.NF_PARAMMATRIX_INDEX_WALLET_KEYWORD],
                            # )
                    except Exception as e:
                        logger.info(
                            f"An error has occurred while using paramMatrix values, will continue to next step.."
                        )
                        # store paramMatrix RPA Remark failed to hashmap
                        self.param_rpa_remark_fail["DATA"] = "Failed"
                else:
                    logger.info(
                        f"No ParamMatrix found for this service name {self.bs_row_data[nf.NF_INDEX_NAME]}, will proceed to next step.."
                    )

                # Section to get success message after clicking submit button
                element_value = self.wd.submit_form_and_wait_for_success(
                    "xpath", nf.NF_ADD_BTN_INPUT, nf.STEP_SUCCESS_MESSAGE
                )

                logger.info(f"STEP '{step_type_name.upper()}' SUCCESSFULLY CREATED!")

                step_id = helper.get_after_word(element_value, "step")
                logger.info(
                    f"STEP ID Retrieved: {step_id} for {step_type_name.upper()}"
                )

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
                if retry == max_retries:
                    logger.error(
                        f"An error has occurred while processing Step Type {step_type_name}\n ERROR: {e}"
                    )
                    # store rpa remark to hashmap
                    self.bs_rpa_remark_fail["DATA"] = "Failed"
                    break

                # Trigger continue loop
                retry += 1
                logger.warning(
                    f"Failed to create step type {step_type_name}, retrying..."
                )
                time.sleep(2)

    def step_type_in_add_wallet_fup(self, bs_service_id, retry=1, max_retries=2):
        while retry < max_retries + 1:
            try:
                dict_in_prov_data = {}
                step_flow_construct_value = self.bs_row_data[
                    nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT
                ].lower()
                sms_voice_conditions = {
                    # If Step and flow construct has Unli SMS
                    "unli_sms": (
                        True if "unli sms" in step_flow_construct_value else False
                    ),
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
                            self.double_extend_value, sms_voice_key, "sms_voice_service"
                        )
                        if sms_voice_key == "unli_sms":
                            step_name = "DOUBLE_SMS_ALLNET_UNLI"
                            amount_field_value = (
                                500
                                if self.bs_row_data[nf.NF_INDEX_BRAND].lower() == "ghp"
                                else 700
                            )
                        else:
                            step_name = "DOUBLE_VOICE_ALLNET_UNLI"
                            amount_field_value = (
                                300
                                if self.bs_row_data[nf.NF_INDEX_BRAND].lower() == "ghp"
                                else 200
                            )

                        logger.info(f"Executing Step Type: {step_type_name.upper()}")

                        # Redirect to Add Step Page
                        self.wd.redirect_to_page(
                            self.url_step_page, nf.NF_ADD_BTN_INPUT
                        )
                        # self.wd.wait_until_element(
                        #     "xpath", nf.NF_ADD_BTN_INPUT, "clickable"
                        # )

                        # Call function 'nf_steps_default_input' to fill up default field values
                        self.nf_steps_default_input(
                            step_name,
                            f"//select[@id='dd_stype_id']//option[@value='129']",
                            sms_voice=sms_voice_key,
                        )

                        # Input IN Serivce Field
                        in_service_value = 196 if sms_voice_key == "unli_sms" else 197
                        logger.info(f"Dropdwn IN Service: {in_service_value}")
                        self.wd.perform_action(
                            "xpath",
                            f"//select[@name='in_fup_step_service']//option[@value='{in_service_value}']",
                            "click",
                        )

                        # Input Amount Field
                        logger.info(f"Input Amount: {amount_field_value}")
                        self.wd.perform_action(
                            "name",
                            nf.NF_STEP_AMOUNT_FIELD,
                            "sendkeys",
                            amount_field_value,
                        )
                        # Section to get success message after clicking submit button
                        element_value = self.wd.submit_form_and_wait_for_success(
                            "xpath", nf.NF_ADD_BTN_INPUT, nf.STEP_SUCCESS_MESSAGE
                        )

                        logger.info(
                            f"STEP FOR '{step_type_name.upper()}' SUCCESSFULLY CREATED!"
                        )

                        # Get Steps unique ID from success message
                        steps_id = helper.get_after_word(element_value, "step")
                        logger.info("Step ID Collected")

                        logger.info(
                            f"STEP ID Retrieved: {steps_id} for {step_type_name}"
                        )

                        # Set Step type result into Dictionary/Object then return
                        dict_in_prov = {
                            f"{sms_voice_key}_id": steps_id,
                            f"{sms_voice_key}_name": step_name,
                        }
                        logger.info(
                            f"Step type {step_type_name} result: {dict_in_prov}"
                        )
                        dict_in_prov_data.update(dict_in_prov)

                return dict_in_prov_data

            except Exception as e:
                if retry == max_retries:
                    logger.error(
                        f"An error has occurred while processing Step Type IN ADD WALLET FUP - {sms_voice_key.upper()} 'in_add_wallet_fup'\n ERROR: {e}"
                    )
                    # store rpa remark to hashmap
                    self.bs_rpa_remark_fail[
                        sms_voice_key.replace("unli_", "").upper()
                    ] = "Failed"
                    break

                # Trigger continue loop
                retry += 1
                logger.warning(
                    f"Failed to create step type IN ADD WALLET FUP - {sms_voice_key.upper()}, retrying..."
                )
                time.sleep(2)

    def step_type_in_prov_service(self, bs_service_id, retry=1, max_retries=2):
        while retry < max_retries + 1:
            try:
                dict_in_prov_data = {}
                step_flow_construct_value = self.bs_row_data[
                    nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT
                ].lower()

                sms_voice_conditions = {
                    # If Step and flow construct has Unli SMS
                    "unli_sms": (
                        True if "unli sms" in step_flow_construct_value else False
                    ),
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
                            self.double_extend_value, sms_voice_key, "sms_voice_service"
                        )
                        if sms_voice_key == "unli_sms":
                            brands = self.bs_row_data[nf.NF_INDEX_BRAND].lower()
                            step_name = "SMS_ALLNET_UNLI"

                            amount_field_value = 500 if brands == "ghp" else 700
                        else:
                            step_name = "VOICE_ALLNET_UNLI"
                            amount_field_value = 300 if brands == "ghp" else 200

                        logger.info(f"Executing Step Type: {step_type_name.upper()}")

                        # Redirect to Add Step Page
                        self.wd.redirect_to_page(
                            self.url_step_page, nf.NF_ADD_BTN_INPUT
                        )
                        # self.wd.wait_until_element(
                        #     "xpath", nf.NF_ADD_BTN_INPUT, "clickable"
                        # )

                        logger.info(
                            "Add Step Page Successfully Reached! Filling up Step Fields..."
                        )

                        # Call function 'nf_steps_default_input' to fill up default field values
                        self.nf_steps_default_input(
                            step_name,
                            f"//select[@id='dd_stype_id']//option[@value='5']",
                            sms_voice=sms_voice_key,
                        )

                        # Input IN Serivce Field
                        self.wd.perform_action(
                            "xpath",
                            f"//select[@name='in_service_id']//option[@value='{196 if sms_voice_key == 'unli_sms' else 197}']",
                            "click",
                        )

                        self.wd.perform_action(
                            "name",
                            nf.NF_STEP_FUP_AMOUNT_FIELD,
                            "sendkeys",
                            amount_field_value,
                        )

                        # Section to get success message after clicking submit button
                        element_value = self.wd.submit_form_and_wait_for_success(
                            "xpath", nf.NF_ADD_BTN_INPUT, nf.STEP_SUCCESS_MESSAGE
                        )

                        logger.info(
                            f"STEP FOR '{step_type_name}' SUCCESSFULLY CREATED!"
                        )

                        # Get Steps unique ID from success message
                        steps_id = helper.get_after_word(element_value, "step")
                        logger.info("Step ID Collected")

                        logger.info(
                            f"STEP ID Retrieved: {steps_id} for {step_type_name}"
                        )

                        # Set Step type result into Dictionary/Object then return
                        dict_in_prov = {
                            f"{sms_voice_key}_id": steps_id,
                            f"{sms_voice_key}_name": step_name,
                        }
                        logger.info(
                            f"Step type {step_type_name} result: {dict_in_prov}"
                        )
                        dict_in_prov_data.update(dict_in_prov)

                return dict_in_prov_data

            except Exception as e:
                if retry == max_retries:
                    logger.error(
                        f"An error has occurred while processing Step Type IN PROV SERVICE step_type_in_prov_service_sms'\n ERROR: {e}"
                    )
                    # store rpa remark to hashmap
                    self.bs_rpa_remark_fail[
                        sms_voice_key.replace("unli_", "").upper()
                    ] = "Failed"
                    break

                # Trigger continue loop
                retry += 1
                logger.warning(
                    f"Failed to create step type IN PROV SERVICE - {sms_voice_key.upper()}, retrying..."
                )
                time.sleep(2)

    def step_type_hlr_ply(self, bs_service_id, retry=1, max_retries=2):
        while retry < max_retries + 1:
            try:
                logger.info("Executing Step Type: HLR - PLY")

                # Redirect to Add Step Page
                self.wd.redirect_to_page(self.url_step_page, nf.NF_ADD_BTN_INPUT)
                # self.wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")

                self.nf_steps_default_input(
                    "HLR_PLY",
                    "//option[contains(text(), 'HLR PLY') and @value='40']",
                )

                # Input HLR Ply Service Dropdown Field
                self.wd.perform_action(
                    "xpath",
                    (
                        "//select[@name='hlr_ply_service_id']//option[@value='3']"
                        if self.bs_row_data[nf.NF_INDEX_BRAND].lower() == "ghp"
                        else "//select[@name='hlr_ply_service_id']//option[@value='2']"
                    ),
                    "click",
                )
                # Section to get success message after clicking submit button
                element_value = self.wd.submit_form_and_wait_for_success(
                    "xpath", nf.NF_ADD_BTN_INPUT, nf.STEP_SUCCESS_MESSAGE
                )

                logger.info("STEP FOR 'HLR PLY' SUCCESSFULLY CREATED!")

                # Get Steps unique ID from success message
                steps_id = helper.get_after_word(element_value, "step")
                logger.info("Step ID Collected")

                logger.info(f"Step ID Retrieved: {steps_id} for HLR PLY")

                # Set Step type result into Dictionary/Object then return
                dict_step_type_idname = {
                    "hlr_ply_id": steps_id,
                    "hlr_ply_name": "HLR_PLY",
                }
                logger.info(f"Step type HLR - PLY result: {dict_step_type_idname}")
                return dict_step_type_idname

            except Exception as e:
                if retry == max_retries:
                    logger.error(
                        f"Failed to process step type 'HLR PLY', will proceed to defining Flow\n ERROR: {e}"
                    )
                    # store rpa remark to hashmap
                    self.bs_rpa_remark_fail["HLR"] = "Failed"
                    break

                # Trigger continue loop
                retry += 1
                logger.warning(f"Failed to create step type HLR PLY, retrying...")
                time.sleep(2)

    def modify_extend_first_expiry(self, old_step_id, extend_amount, extend_duration):
        try:
            # Redirection to Edit page for Extend First Expiry using its old step id
            logger.info(
                f"Modifying Existing Step Type: EXTEND FLOW - EXTEND FIRST EXPIRY = {old_step_id}"
            )
            logger.info(
                f"Redirecting to Edit Page Using Extend First Expiry ID : {old_step_id}"
            )
            url_step_edit_page = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=steps&op=details&id={old_step_id}"
            self.wd.driver.get(url_step_edit_page)
            self.wd.wait_until_element(
                "xpath", nf.EDIT_STEP_INPUT_FIELD_PARAM, "visible"
            )
            logger.info(f"Site Successfully Reached! {url_step_edit_page}")

            # Input Amount Field for Extend Flow
            logger.info("Adding PARAM Values for existing Extend First Expiry...")
            self.wd.perform_action(
                "xpath",
                nf.EDIT_STEP_INPUT_FIELD_PARAM,
                "sendkeys",
                extend_amount,
            )
            self.wd.perform_action(
                "xpath",
                nf.EDIT_STEP_INPUT_FIELD_DURATION,
                "sendkeys",
                extend_duration,
            )

            # Click 'Add' Button
            logger.info("Saving changes...")
            self.wd.perform_action("xpath", nf.NF_STEP_ADD_BTN_INPUT, "click")

            # Trigger Time sleep, helps to finish loading edit webpage..
            time.sleep(6)

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
                f"An error has occurred while modifying EXTEND FIRST EXPIRY\nERROR: {e}"
            )

    def step_type_data_extend_wallet_expiry(
        self, bs_service_id, retry=1, max_retries=2
    ):
        while retry < max_retries + 1:
            try:
                logger.info("Executing Step Type: DATA EXTEND WALLET EXPIRY")
                # Redirect to Add Step Page
                self.wd.redirect_to_page(self.url_step_page, nf.NF_ADD_BTN_INPUT)
                # self.wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "clickable")
                # Declare wallet name
                bs_wallet = f"EXTEND_{self.bs_row_data[nf.NF_INDEX_WALLET]}"

                # Section to Input Default Values from BS Worksheet
                # Call function 'nf_steps_default_input' to fill up default field values
                self.nf_steps_default_input(
                    bs_wallet,
                    nf.STEP_TYPE_DATA_EXTEND_WALLET_EXPIRY,
                )

                # Input Default Jnetx Wallet Type Dropdown
                logger.info(
                    f"Input Jnetx Wallet: {self.bs_row_data[nf.NF_INDEX_WALLET]}"
                )
                self.wd.perform_action(
                    "xpath",
                    f"//select[@name='jnetx_wallet_type_id']//option[contains(text(), '{self.bs_row_data[nf.NF_INDEX_WALLET]}')][1]",
                    "click",
                )

                # Input Expiry Field
                logger.info(
                    f"Input Expiry: {int(self.bs_row_data[nf.NF_INDEX_EXTEND_DURATION_IN_DAYS]) * 24}"
                )
                self.wd.perform_action(
                    "xpath",
                    f"(//input[@name='extend_step_expiries[]'])[1]",
                    "sendkeys",
                    f"{int(self.bs_row_data[nf.NF_INDEX_EXTEND_DURATION_IN_DAYS]) * 24}",
                )

                # Section to get success message after clicking submit button
                element_value = self.wd.submit_form_and_wait_for_success(
                    "xpath", nf.NF_ADD_BTN_INPUT, nf.STEP_SUCCESS_MESSAGE
                )

                logger.info(f"STEP 'DATA EXTEND WALLET EXPIRY' SUCCESSFULLY CREATED!")

                # Get Steps unique ID from success message
                step_id = helper.get_after_word(element_value, "step")
                logger.info(
                    f"STEP ID Retrieved: {step_id} for 'DATA EXTEND WALLET EXPIRY'"
                )

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
                if retry == max_retries:
                    logger.error(
                        f"An error has occurred in function of EXTEND DATA WALLET EXPIRY\nERROR: {e}"
                    )
                    # store rpa remark to hashmap
                    self.bs_rpa_remark_fail["DATA"] = "Failed"
                    break

                # Trigger continue loop
                retry += 1
                logger.warning(
                    f"Failed to create step type EXTEND DATA WALLET EXPIRY, retrying..."
                )
                time.sleep(2)

    def step_type_in_extend_wallet_expiry(self, bs_service_id, retry=1, max_retries=2):
        while retry < max_retries + 1:
            try:
                dict_in_prov_data = {}
                step_flow_construct_value = self.bs_row_data[
                    nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT
                ].lower()

                sms_voice_conditions = {
                    # If Step and flow construct has Unli SMS
                    "unli_sms": (
                        True if "unli sms" in step_flow_construct_value else False
                    ),
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

                        # Redirect to Add Step Page
                        self.wd.redirect_to_page(
                            self.url_step_page, nf.NF_ADD_BTN_INPUT
                        )
                        # self.wd.wait_until_element(
                        #     "xpath", nf.NF_ADD_BTN_INPUT, "clickable"
                        # )
                        # Call function 'nf_steps_default_input' to fill up default field values
                        self.nf_steps_default_input(
                            step_name,
                            nf.STEP_TYPE_IN_EXTEND_WALLET_EXPIRY,
                            sms_voice=sms_voice_key,
                        )

                        # Input IN Serivce Field
                        logger.info(
                            f"Dropdwn IN Service: {196 if sms_voice_key == 'unli_sms' else 197}"
                        )
                        self.wd.perform_action(
                            "xpath",
                            f"//select[@name='in_service_id']//option[@value='{196 if sms_voice_key == 'unli_sms' else 197}']",
                            "click",
                        )

                        # Input Expiry Field
                        logger.info(
                            f"Input Expiry: {int(self.bs_row_data[nf.NF_INDEX_EXTEND_DURATION_IN_DAYS]) * 24}"
                        )
                        self.wd.perform_action(
                            "xpath",
                            f"(//input[@name='extend_step_expiries[]'])[1]",
                            "sendkeys",
                            f"{int(self.bs_row_data[nf.NF_INDEX_EXTEND_DURATION_IN_DAYS]) * 24}",
                        )

                        # Section to get success message after clicking submit button
                        element_value = self.wd.submit_form_and_wait_for_success(
                            "xpath", nf.NF_ADD_BTN_INPUT, nf.STEP_SUCCESS_MESSAGE
                        )

                        logger.info(
                            f"STEP FOR 'IN EXTEND WALLET EXPIRY' SUCCESSFULLY CREATED!"
                        )

                        # Get Steps unique ID from success message
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
                if retry == max_retries:
                    logger.error(
                        f"An error has occurred while processing Step Type IN EXTEND WALLET EXPIRY - step_type_in_extend_wallet_expiry'\n ERROR: {e}"
                    )
                    # store rpa remark to hashmap
                    self.bs_rpa_remark_fail[
                        sms_voice_key.replace("unli_", "").upper()
                    ] = "Failed"
                    break

                # Trigger continue loop
                retry += 1
                logger.warning(
                    f"Failed to create step type IN EXTEND WALLET EXPIRY - {sms_voice_key.upper()}, retrying..."
                )
                time.sleep(2)
