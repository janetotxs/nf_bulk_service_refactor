from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from utils.env_loader import get_env_variable
from utils.helpers import get_after_word
from utils.logger import setup_logger
from utils.logger2 import logger
from nf import bulk_service as bs
from nf.nf_constants import NfConstants
import os

# logger = setup_logger(service_name=f"NF {__name__}")

# Call Constants
nf = NfConstants()


# Function to Start Service Flow Process
def nf_start_service_flows(
    step_type_data,
    step_flow_construct_value,
    bs_service_id,
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
        logger.info(f"STARTING ADD FLOW PROCESS")

        # Redirect to Add Service Flow Page
        wd.driver.get(
            f"{os.getenv('WEBTOOL_BASE_URL')}/nf/index.php?mod=flows&op=add&svc_id={bs_service_id}&details_id={bs_service_id}"
        )
        wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "visible")

        # Execute Flow process based on Step and Flow construct

        # Check if sf value has keyword of prepaid ctl
        if "prepaid ctl" in step_flow_construct_value.lower():
            nf_flow_prepaid_ctl(
                step_type_data,
                bs_service_id,
                bs_worksheet,
                step_flow_construct_value,
                bs_row,
            )

        # Check if sf value has keyword of prepaid opm
        elif "prepaid opm" in step_flow_construct_value.lower():
            "TODO"

    except Exception as e:
        error_msg = f"Something went wrong in the Process Sequence of 'SERVICE FLOW PROCESS'.\nERROR: {e}"
        logger.info(error_msg)
        logger.info("Terminating Bot")
        wd.stop_process()
        # --------------------END FLOWS PROCESS------------------------#


# Function to Execute Flow process Specifically for Prepaid CTL With Data
def nf_flow_prepaid_ctl(
    step_type_data, bs_service_id, bs_worksheet, step_flow_construct_value, bs_row
):
    try:
        logger.info(f"Defining Flow for {step_flow_construct_value}")
        flow_id = None
        # Input Step Name Field
        wd.perform_action("name", nf.NF_FLOWS_NAME_INPUT, "sendkeys", "PROVISION")

        # Dropdown First Step Field
        wd.perform_action(
            "xpath",
            f"//select[@name='first_step_id']//option[@value='{step_type_data['in_charge_id']}' and contains(text(), '{step_type_data['in_charge_name']}')]",
            "click",
        )

        # Click 'Add' Button
        wd.perform_action("xpath", os.getenv("NF_ADD_BTN_INPUT"), "click")
        logger.info("SERVICE FLOW ADDED")

        # FOR TEST ONLY redirect to flow edit page
        # wd.driver.get(
        #    "http://10.47.69.195/nf/index.php?mod=flows&op=details&id=5039"
        # )

        # Get Unique Flow ID from div element page under Flow Details.
        wd.wait_until_element("xpath", "(//div)[85]//div[2]", "visible")
        flow_id = wd.driver.find_element(By.XPATH, "(//div)[85]//div[2]").text
        flow_name = wd.driver.find_element(By.XPATH, "(//div)[88]//div[2]").text
        logger.info(f"Flow ID Retrieved: {flow_id}")

        # Define step from IN CHARGE to EXTENDS FIRST EXPIRY then update values to Flow worksheet calling gs.inser_new_row
        define_stepfrom_stepto(
            step_type_data["in_charge_id"],
            step_type_data["in_charge_name"],
            step_type_data["extend_first_expiry_id"],
            step_type_data["extend_first_expiry_name"],
        )

        # Determine what Flow to be executed based on Step and Flow Construct
        # Condition for Prepaid CTL with Data, Unli SMS and Unli Voice
        sf_construct_value = step_flow_construct_value.lower()
        if (
            "data" in sf_construct_value
            and "unli sms" in sf_construct_value
            and "unli voice" in sf_construct_value
        ):
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
                step_type_data["in_prov_service_sms_id"],
                step_type_data["in_prov_service_sms_name"],
            )

            # Define step from IN PROV SERVICE - Unli SMS to IN PROV SERVICE - Unli Voice
            define_stepfrom_stepto(
                step_type_data["in_prov_service_sms_id"],
                step_type_data["in_prov_service_sms_name"],
                step_type_data["in_prov_service_voice_id"],
                step_type_data["in_prov_service_voice_name"],
            )

            # Define step from IN PROV SERVICE - Unli VOICE to HLR PLY
            define_stepfrom_stepto(
                step_type_data["in_prov_service_voice_id"],
                step_type_data["in_prov_service_voice_name"],
                step_type_data["hlr_ply_id"],
                step_type_data["hlr_ply_name"],
            )

            logger.info(
                "FLOW SUCCESSFULLY DEFINED FOR = Prepaid CTL With Data, Unli SMS and Unli Voice"
            )

        # Condition for Prepaid CTL with Data and Unli SMS
        elif "data" in sf_construct_value and "unli sms" in sf_construct_value:
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
                step_type_data["in_prov_service_sms_id"],
                step_type_data["in_prov_service_sms_name"],
            )

            logger.info(
                "FLOW SUCCESSFULLY DEFINED FOR = Prepaid CTL With Data and Unli SMS"
            )

        # Condition for Prepaid CTL with Unli SMS and Unli Voice
        elif "unli sms" in sf_construct_value and "unli voice" in sf_construct_value:
            # Define step from EXTENDS FIRST EXPIRY to IN PROV SERVICE - Unli SMS
            define_stepfrom_stepto(
                step_type_data["extend_first_expiry_id"],
                step_type_data["extend_first_expiry_name"],
                step_type_data["in_prov_service_sms_id"],
                step_type_data["in_prov_service_sms_name"],
            )

            # Define step from IN PROV SERVICE - Unli SMS to IN PROV SERVICE - Unli Voice
            define_stepfrom_stepto(
                step_type_data["in_prov_service_sms_id"],
                step_type_data["in_prov_service_sms_name"],
                step_type_data["in_prov_service_voice_id"],
                step_type_data["in_prov_service_voice_name"],
            )

            # Define step from IN PROV SERVICE - Unli VOICE to HLR PLY
            define_stepfrom_stepto(
                step_type_data["in_prov_service_voice_id"],
                step_type_data["in_prov_service_voice_name"],
                step_type_data["hlr_ply_id"],
                step_type_data["hlr_ply_name"],
            )

            logger.info(
                "FLOW SUCCESSFULLY DEFINED FOR = Prepaid CTL With Unli SMS and Unli Voice"
            )

        # Condition for Prepaid CTL with Data
        elif "data" in sf_construct_value:
            # Define step from EXTENDS FIRST EXPIRY to DATA PROV WITH KEYWORD MAPPIN
            define_stepfrom_stepto(
                step_type_data["extend_first_expiry_id"],
                step_type_data["extend_first_expiry_name"],
                step_type_data["data_prov_id"],
                step_type_data["data_prov_name"],
            )

        logger.info("FLOW SUCCESSFULLY DEFINED FOR = Prepaid CTL With Data")

        # Call Function from bulk_service to execute defining Default and API Flow of Bulk Services using flow ID and flow name
        bs.nf_assign_api_default_flow(bs_service_id, flow_id, flow_name)
        logger.info("Bulk Service Default and API Flow Updated")

        # Update current Bulk service RPA Remarks
        gs.update_row(
            bs_row,
            bs_worksheet.col_count,
            bs_worksheet,
            f"Bulk Services Successfully Defined",
        )
        logger.info(
            f"BULK SERVICE SUCCESSFULLY DEFINED FOR SERVICE ID: {bs_service_id}"
        )

    except Exception as e:
        logger.info(f"An error has occurred in 'nf_flow_prepaid_ctl'\nERROR: {e}")


def define_stepfrom_stepto(
    step_type_id_from, step_type_name_from, step_type_id_to, step_type_name_to
):
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
        f"Flow From: {step_type_id_from} ({step_type_name_from}) To: {step_type_id_to} ({step_type_name_to}) Successfully Added"
    )
