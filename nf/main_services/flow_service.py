from selenium.webdriver.common.by import By
from utils.env_loader import get_env_variable
from utils.logger2 import logger
from nf.main_services import bulk_service as bs
from nf.nf_constants import NfConstants

# logger = setup_logger(service_name=f"NF {__name__}")

# Call Constants
nf = NfConstants()


# Function to Start Service Flow Process
def nf_start_service_flows(
    double_extend_value,
    step_type_data,
    bs_row_data,
    bs_worksheet,
    webdriver,
    gsheet,
    bs_row,
):
    global wd
    global gs

    wd = webdriver
    gs = gsheet

    # --------------------START FLOWS PROCESS------------------------#
    try:
        # Declare Variables
        step_flow_construct_value = bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT]
        bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]

        logger.info(f"STARTING FLOW CREATION PROCESS")

        # Redirect to Add Service Flow Page
        url = f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=flows&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
        wd.driver.get(url)
        wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "visible")
        logger.info(f"Site reached! {url}")

        # Execute Flow process based on Step and Flow construct
        # Check if step and flow construct value has keyword of 'prepaid ctl'
        if "prepaid ctl" in step_flow_construct_value.lower():
            create_flow_prepaid_ctl(
                double_extend_value,
                step_type_data,
                bs_row_data,
                bs_worksheet,
                bs_row,
            )

        # Check if step and flow construct value has keyword of 'prepaid opm'
        elif "prepaid opm" in step_flow_construct_value.lower():
            "TODO"

    except Exception as e:
        error_msg = f"Something went wrong in the Process Sequence of 'SERVICE FLOW PROCESS'.\nERROR: {e}"
        logger.info(error_msg)
        logger.info("Terminating Bot")
        wd.stop_process()
        # --------------------END FLOWS PROCESS------------------------#


# Function to Execute Flow process Specifically for Prepaid CTL With Data
def create_flow_prepaid_ctl(
    double_extend_value,
    step_type_data,
    bs_row_data,
    bs_worksheet,
    bs_row,
):
    try:
        # Declare Variables
        step_flow_construct_value = bs_row_data[nf.NF_INDEX_STEP_AND_FLOW_CONSTRUCT]
        bs_service_id = bs_row_data[nf.NF_INDEX_SERVICE_ID]
        flow_id = None

        logger.info(f"Defining Flow for {step_flow_construct_value}")

        # Input Step Name Field
        wd.perform_action("name", nf.NF_FLOWS_NAME_INPUT, "sendkeys", "PROVISION")

        # Dropdown First Step Field
        wd.perform_action(
            "xpath",
            f"//select[@name='first_step_id']//option[@value='{step_type_data['in_charge_id']}' and contains(text(), '{step_type_data['in_charge_name']}')]",
            "click",
        )

        # Click 'Add' Button
        wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
        logger.info("SERVICE FLOW SUCCESSFULLY CREATED!")

        # FOR TEST ONLY redirect to flow edit page
        # wd.driver.get(
        #    "http://10.47.69.195/nf/index.php?mod=flows&op=details&id=5039"
        # )

        # Get Unique Flow ID from div element page under Flow Details.
        wd.wait_until_element("xpath", "(//div)[85]//div[2]", "visible")
        flow_id = wd.driver.find_element(By.XPATH, "(//div)[85]//div[2]").text
        # flow_name = wd.driver.find_element(By.XPATH, "(//div)[88]//div[2]").text
        logger.info(f"Flow ID Retrieved: {flow_id}")

        # Define step from IN CHARGE to EXTENDS FIRST EXPIRY
        define_stepfrom_stepto(
            step_type_data["in_charge_id"],
            step_type_data["in_charge_name"],
            step_type_data["extend_first_expiry_id"],
            step_type_data["extend_first_expiry_name"],
        )

        # Determine what Flow to be executed based on Step and Flow Construct
        # Condition for Prepaid CTL with Data, Unli SMS and Unli Voice
        sf_construct_value = step_flow_construct_value.lower()

        if sf_construct_value == "prepaid ctl with data, unli sms and unli voice":
            try:
                # Define step from EXTENDS FIRST EXPIRY to DATA PROV WITH KEYWORD MAPPING
                define_stepfrom_stepto(
                    step_type_data["extend_first_expiry_id"],
                    step_type_data["extend_first_expiry_name"],
                    step_type_data["data_prov_id"],
                    step_type_data["data_prov_name"],
                )

                # Define step from DATA PROV WITH KEYWORD MAPPING to IN PROV SERVICE - Unli SMS
                define_stepfrom_stepto(
                    step_type_data["data_prov_id"],
                    step_type_data["data_prov_name"],
                    step_type_data["unli_sms_id"],
                    step_type_data["unli_sms_name"],
                )

                # Define step from IN PROV SERVICE - Unli SMS to IN PROV SERVICE - Unli Voice
                define_stepfrom_stepto(
                    step_type_data["unli_sms_id"],
                    step_type_data["unli_sms_name"],
                    step_type_data["unli_voice_id"],
                    step_type_data["unli_voice_name"],
                )

                # Define step from IN PROV SERVICE - Unli VOICE to HLR PLY
                if double_extend_value != "double":
                    define_stepfrom_stepto(
                        step_type_data["unli_voice_id"],
                        step_type_data["unli_voice_name"],
                        step_type_data["hlr_ply_id"],
                        step_type_data["hlr_ply_name"],
                    )

                logger.info(
                    "FLOW SUCCESSFULLY DEFINED FOR = Prepaid CTL With Data, Unli SMS and Unli Voice"
                )
            except Exception as e:
                logger.info(
                    f"An error has occurred while defining Flow of 'prepaid ctl with data, unli sms and unli voice': {e}"
                )

        # Condition for Prepaid CTL with Data and Unli SMS
        elif sf_construct_value == "prepaid ctl with data and unli sms":
            try:
                # Define step from EXTENDS FIRST EXPIRY to DATA PROV WITH KEYWORD MAPPING then update values to Flow worksheet calling gs.inser_new_row
                define_stepfrom_stepto(
                    step_type_data["extend_first_expiry_id"],
                    step_type_data["extend_first_expiry_name"],
                    step_type_data["data_prov_id"],
                    step_type_data["data_prov_name"],
                )

                # Define step from DATA PROV WITH KEYWORD MAPPING to IN PROV SERVICE - Unli SMS
                define_stepfrom_stepto(
                    step_type_data["data_prov_id"],
                    step_type_data["data_prov_name"],
                    step_type_data["unli_sms_id"],
                    step_type_data["unli_sms_name"],
                )

                logger.info(
                    "FLOW SUCCESSFULLY DEFINED FOR = Prepaid CTL With Data and Unli SMS"
                )
            except Exception as e:
                logger.info(
                    f"An error has occurred while defining Flow of 'prepaid ctl with data and unli sms': {e}"
                )

        # Condition for Prepaid CTL with Unli SMS and Unli Voice
        elif sf_construct_value == "prepaid ctl with unli sms and unli voice":
            try:
                # Define step from EXTENDS FIRST EXPIRY to IN PROV SERVICE - Unli SMS
                define_stepfrom_stepto(
                    step_type_data["extend_first_expiry_id"],
                    step_type_data["extend_first_expiry_name"],
                    step_type_data["unli_sms_id"],
                    step_type_data["unli_sms_name"],
                )

                # Define step from IN PROV SERVICE - Unli SMS to IN PROV SERVICE - Unli Voice
                define_stepfrom_stepto(
                    step_type_data["unli_sms_id"],
                    step_type_data["unli_sms_name"],
                    step_type_data["unli_voice_id"],
                    step_type_data["unli_voice_name"],
                )

                # Define step from IN PROV SERVICE - Unli VOICE to HLR PLY
                if double_extend_value != "double":
                    define_stepfrom_stepto(
                        step_type_data["unli_voice_id"],
                        step_type_data["unli_voice_name"],
                        step_type_data["hlr_ply_id"],
                        step_type_data["hlr_ply_name"],
                    )

                logger.info(
                    "FLOW SUCCESSFULLY DEFINED FOR = Prepaid CTL With Unli SMS and Unli Voice"
                )
            except Exception as e:
                logger.info(
                    f"An error has occurred while defining Flow of 'prepaid ctl with unli sms and unli voice': {e}"
                )

        # Condition for Prepaid CTL with Data
        elif sf_construct_value == "prepaid ctl with data":
            try:
                # Define step from EXTENDS FIRST EXPIRY to DATA PROV WITH KEYWORD MAPPIN
                define_stepfrom_stepto(
                    step_type_data["extend_first_expiry_id"],
                    step_type_data["extend_first_expiry_name"],
                    step_type_data["data_prov_id"],
                    step_type_data["data_prov_name"],
                )

                logger.info("FLOW SUCCESSFULLY DEFINED FOR = Prepaid CTL With Data")
            except Exception as e:
                logger.info(
                    f"An error has occurred while defining Flow of 'prepaid ctl with data': {e}"
                )

        # Call Function from bulk_service to execute defining Default and API Flow of Bulk Services using flow ID and flow name
        bs.nf_assign_bulk_service_flow(double_extend_value, bs_service_id, flow_id)
        flow_string = (
            f"{'Base' if double_extend_value == '' else double_extend_value.upper()}"
        )

        logger.info(f"Bulk Service {flow_string} Flow and API Flow Updated")

        try:
            # Update current row Bulk service RPA Remarks
            prefix_success_message = (
                bs_row_data[nf.NF_INDEX_RPA_REMARKS]
                if double_extend_value == "double" or double_extend_value == "extend"
                else "Bulk Service Successfully Created"
            )
            suffix_success_msg = f" | {'BASE' if double_extend_value == '' else double_extend_value.upper()} FLOW: SUCCESS"
            rpa_remarks_final_value = f"{prefix_success_message}{suffix_success_msg}"

            gs.update_row(
                bs_row,
                nf.COLUMN_BULK_SERVICE_RPA_REMARKS,
                bs_worksheet,
                rpa_remarks_final_value,
            )
            logger.info(
                f"BULK SERVICE SUCCESSFULLY DEFINED FOR SERVICE ID: {bs_service_id}{suffix_success_msg}"
            )
        except Exception as e:
            logger.info(
                f"An error has occurred while updating the Bulk Service RPA Remarks\nERROR: {e}"
            )

    except Exception as e:
        logger.info(f"An error has occurred in 'nf_flow_prepaid_ctl'\nERROR: {e}")


def define_stepfrom_stepto(
    step_type_id_from, step_type_name_from, step_type_id_to, step_type_name_to
):
    try:
        logger.info(
            f"Assigning Flow - STEP FROM: {step_type_name_from} STEP TO: {step_type_name_to}"
        )
        # Dropdown Step from Dropdown
        wd.perform_action(
            "xpath",
            f"//select[@name='step_id_from']//option[@value='{step_type_id_from}' and contains(text(), '{step_type_name_from}')]",
            "click",
        )

        # Dropdown Step to Dropdown
        wd.perform_action(
            "xpath",
            f"//select[@name='step_id_to']//option[@value='{step_type_id_to}' and contains(text(), '{step_type_name_to}')]",
            "click",
        )

        # Click 'Add' Button
        wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
        wd.wait_until_element(
            "xpath",
            f"//a[@href='index.php?mod=steps&op=details&id={step_type_id_to}']",
            "visible",
        )

        logger.info(
            f"Flow Successfully Added: From - {step_type_id_from} ({step_type_name_from}) To: {step_type_id_to} ({step_type_name_to}) Successfully Added"
        )
    except Exception as e:
        logger.info(
            f"Something went wrong in the function of 'define_stepfrom_stepto'\nERROR: {e}"
        )
