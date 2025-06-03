from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from utils.env_loader import get_env_variable
from utils.helpers import get_after_word
from utils.logger import setup_logger
from utils.logger2 import logger
from nf import bulk_service as bs
from nf.nf_constants import NfConstants
import time
import os

# logger = setup_logger(service_name=f"NF {__name__}")

# Call Constants
nf = NfConstants()


# Function to Start Service Flow Process
def nf_start_service_flows(
    step_type_data, bs_service_id, bs_worksheet, webdriver, gsheet, bs_row
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

        # Execute Flow process from Step and Flow construct
        nf_flow_prepaid_ctl_with_data(
            step_type_data, bs_service_id, bs_worksheet, bs_row
        )

    except Exception as e:
        error_msg = f"Something went wrong in the Process Sequence of 'SERVICE FLOWS PROCESS'.\nERROR: {e}"
        logger.info(error_msg)
        logger.info("Terminating Bot")
        wd.stop_process()
        # --------------------END FLOWS PROCESS------------------------#


# Function to Execute Flow process Specifically for Prepaid CTL With Data
def nf_flow_prepaid_ctl_with_data(step_type_data, bs_service_id, bs_worksheet, bs_row):
    try:
        logger.info("Defining flow for Prepaid CTL With Data")
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

        # Define step from EXTENDS FIRST EXPIRY to DATA PROV WITH KEYWORD MAPPING then update values to Flow worksheet calling gs.inser_new_row
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
        logger.info(
            f"An error has occurred in 'nf_flow_prepaid_ctl_with_data'\nERROR: {e}"
        )


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
