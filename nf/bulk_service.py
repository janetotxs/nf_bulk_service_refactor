from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from utils.env_loader import get_env_variable
from utils.helpers import get_after_word
from utils.logger import setup_logger
from utils.logger2 import logger
from nf.nf_constants import NfConstants
import time
import os

# logger = setup_logger(service_name=f"NF - {__name__}")

# Call Constants
nf = NfConstants()


# Function to start Bulk Services Process
def nf_start_bulk_services(bs_worksheet, webdriver, gsheet):
    global wd
    global gs

    wd = webdriver
    gs = gsheet

    # ------------------START BULK SERVICES PROCESS----------------------#
    list_service_id = []

    # Service ID for TEST ONLY
    service_id = 3540

    column_rpa_remarks_count = bs_worksheet.col_count
    column_date_count = bs_worksheet.col_count - 1

    # Call 'get_pending_rows' from google_sheet function to get pending rows to process for bulk service
    pending_rows = gs.get_pending_rows(
        bs_worksheet, column_date_count, column_rpa_remarks_count
    )

    # Check if there's pending rows
    if len(pending_rows) == 0:
        logger.info("No pending rows as of the moment, terminating bot")
        wd.stop_process()

    print(f"PENDING ROWS: {pending_rows}")

    for i, row in enumerate(pending_rows):
        try:
            # Declare Service ID variable
            # service_id = None
            # Service id for test only
            # service_id += 1

            # Get row data using pending rows
            row_data = bs_worksheet.row_values(row)

            logger.info(f"BATCH {i+1} BULK SERVICES = ROW DATA : {row_data}")
            logger.info(f"STARTING ADD BULK SERVICES PROCESS FOR: {row_data[1]}")

            # Redirect to ADD BULK SERVICE PAGE
            wd.driver.get(os.getenv("WEBTOOL_BULK_SERVICES_ADD_FULL_URL"))
            wd.wait_until_element("xpath", os.getenv("NF_INPUT_NAME"), "visible")

            logger.info("Filling up Bulk Services Fields...")

            # Input Bulk Service Name Field
            wd.perform_action(
                "xpath",
                os.getenv("NF_INPUT_NAME"),
                "sendkeys",
                row_data[1],
            )

            # Tick Radio button for Service Class DEFAULT = Bulk Service
            wd.perform_action(
                "xpath", os.getenv("NF_BS_SERVICE_CLASS_BULK_SERVICE"), "click"
            )

            # Tick Checkbox for Group Status Inquiry
            handle_group_status_inquiry(row_data[2])
            # wd.perform_action("id", os.getenv("NF_BS_GROUP_STATUS_INQUIRY"), "click")

            # Tick Checkbox for Wallet Type
            handle_nf_bs_wallet_type(row_data[3])

            # Validate Wallet Handling => Check if wallet exist, if not, create wallet using function of 'create_nf_ds_new_wallet' method under 'process_wallet' function.
            logger.info(
                "Checking wallet value before proceeding to bulk services process.."
            )
            wallet_status = check_wallet(row_data[4])
            process_wallet(wallet_status)

            # Handle NF Status Dropdown option DEFAULT = ACTIVE
            handle_nf_bs_status("active")

            # Input Thread Count Field
            wd.perform_action(
                "name",
                os.getenv("NF_BS_THREAD_COUNT_INPUT_NAME"),
                "sendkeys",
                row_data[5],
            )

            # Handle NF Type Dropwdown option Default = Wallet-Based
            handle_nf_bs_type("Wallet-Based")

            # Handle Brands using function 'handle_nf_bs_brands'.
            handle_nf_bs_brands(row_data[6])

            # Input Timeout(sec) Field DEFAULT = 60
            wd.perform_action("name", os.getenv("NF_BS_TIMEOUT_SEC"), "sendkeys", 60)

            # Input Status Charged-Amount Field DEFAULT = 0
            wd.perform_action(
                "name", os.getenv("NF_BS_STATUS_CHARGED_AMOUNT"), "sendkeys", 0
            )

            # Input Balance Charged-Amount Field DEFAULT = 0
            wd.perform_action(
                "name", os.getenv("NF_BS_BALANCE_CHARGED_AMOUNT"), "sendkeys", 0
            )

            # Input SMP Name Field
            wd.perform_action(
                "name", os.getenv("NF_BS_SMP_NAME"), "sendkeys", row_data[7]
            )

            # Input Default Access Code Field DEFAULT = 8080
            wd.perform_action(
                "name", os.getenv("NF_BS_DEFAULT_ACCESS_CODE"), "sendkeys", 8080
            )

            # Input Queue Limit Field DEFAULT = 1000
            wd.perform_action("name", os.getenv("NF_BS_QUEUE_LIMIT"), "sendkeys", 1000)

            # Handle Deprov on Empty Checkbox
            handle_bs_deprov_on_empty(row_data[8])

            # Handle Cancel Pre-expiry Notifs on Empty Checkbox
            handle_bs_preexpiry_notifs("no")

            # Handle Subscription-Less Checkbox
            handle_bs_subscription_less(row_data[9])

            # Tick Max Recurrence DEFAULT = 'No Limit'
            wd.perform_action("id", os.getenv("NF_BS_MAX_RECURRENCE"), "click")

            # Input Max Daily Extensions
            wd.perform_action("name", os.getenv("NF_BS_MAX_DAILY_EXTENSION"), "clear")
            wd.perform_action(
                "name", os.getenv("NF_BS_MAX_DAILY_EXTENSION"), "sendkeys", row_data[10]
            )

            # Input Max Total Extensions
            wd.perform_action("name", os.getenv("NF_BS_MAX_TOTAL_EXTENSION"), "clear")
            wd.perform_action(
                "name", os.getenv("NF_BS_MAX_TOTAL_EXTENSION"), "sendkeys", row_data[11]
            )

            # Input Promo Name (optional) Field
            wd.perform_action(
                "name", os.getenv("NF_BS_PROMO_NAME"), "sendkeys", row_data[12]
            )

            # Handle Community Pool Checkbox = DEFAULT 'No' for now
            # handle_bs_community_pool(row_data[13])

            # Click Add button
            # wd.perform_action("xpath", os.getenv("NF_ADD_BTN_INPUT"), "click")

            # Get Bulk Services Service Id from Success Message Text
            # wd.wait_until_element("xpath", "//div[@class='success']", "visible")
            # success_msg = wd.driver.find_element(
            #    By.XPATH, "//div[@class='success']"
            # ).text
            # word_service_id = get_after_word(success_msg, "Service with id:")
            # service_id = word_service_id.replace(".", "")

            logger.info(f"BULK SERVICES PROCESS DONE! SERVICE ID CREATED: {service_id}")

            # Start defining Service Expiry
            nf_add_service_expiry(row_data, service_id)

            # After bulk services is created, get service id and update cell calling "gs.update_row"
            # Insert service id to Service ID Column
            gs.update_row(row, 1, bs_worksheet, service_id)

            # Update RPA Remarks Column
            gs.update_row(
                row,
                bs_worksheet.col_count,
                bs_worksheet,
                "Bulk Services Created, in progress defining of steps and flows",
            )
            logger.info(f"\nWorksheet Updated: {bs_worksheet}\nRow Updated: {row}")

            list_service_id.append(service_id)

        except Exception as e:
            error_msg = f"Something went wrong in the Process Sequence of 'BULK SERVICES PROCESS'.\nERROR: {e}"
            logger.info(error_msg)
            gs.update_rpa_remarks_error(row, error_msg, bs_worksheet)
            logger.info("PENDING ROWS :  " + str(pending_rows))
            continue

    # Check if there's a successfull Bulk Service Created
    if len(list_service_id) == 0:
        wd.stop_process()
        raise Exception(
            f"Bot didn't found any successful Bulk Services Created, terminating bot"
        )
    # Return all rows that are successfully created.
    else:
        list_success_rows = []
        for service_id in list_service_id:
            list_success_rows.append(
                bs_worksheet.find(str(service_id), in_column=1).row
            )

        logger.info(f"RETRIEVED SUCCESSFUL BULK SERVICES ROWS: {list_success_rows}")
        return list_success_rows
    # ------------ ------END BULK SERVICES PROCESS----------------------#


# Handle Include in Group Status Inquiry Checkbox
def handle_nf_bs_include_group_status_inquiry(nf_group_status_inquiry_value):
    try:
        element = None

        if nf_group_status_inquiry_value.lower() == "yes":
            element = os.getenv("NF_BS_GROUP_STATUS_INQUIRY")
        else:
            pass

        wd.perform_action("id", element, "click")

    except Exception as e:
        logger.info(
            f"An error has occurred on function of 'handle_nf_bs_include_group_status_inquiry' function. ERROR: {e}"
        )


def handle_group_status_inquiry(group_status_value):
    try:
        element = None

        if group_status_value.lower() == "yes":
            element = nf.NF_BS_GROUP_STATUS_INQUIRY
        else:
            pass

        wd.perform_action("id", element, "click")

    except Exception as e:
        logger.info(
            f"An error has occurred in 'handle_group_status_inquiry' function. ERROR: {e}"
        )
        wd.stop_process()


# Handle Radio Button Wallet Type.
def handle_nf_bs_wallet_type(wallet_type_value):
    try:
        element = None

        if wallet_type_value.lower() == "sms/voice":
            element = os.getenv("BS_WALLET_TYPE_SMSVOICE")
        elif wallet_type_value.lower() == "data":
            element = os.getenv("BS_WALLET_TYPE_DATA")
        elif wallet_type_value.lower() == "sps":
            element = os.getenv("BS_WALLET_TYPE_SPS")
        else:
            element = os.getenv("BS_WALLET_TYPE_CPS")

        wd.perform_action("xpath", element, "click")

    except Exception as e:
        logger.info(
            f"An error has occurred in 'handle_nf_bs_wallet_type' function. ERROR: {e}"
        )


# Handle Bulk Service Status Dropdown
def handle_nf_bs_status(nf_status_value):
    try:
        element = None

        if nf_status_value.lower() == "inactive":
            element = os.getenv("BS_STATUS_INACTIVE")
        elif nf_status_value.lower() == "no prov":
            element = os.getenv("BS_STATUS_NOPROV")
        else:
            element = os.getenv("BS_STATUS_ACTIVE")

        wd.perform_action("xpath", element, "click")

    except Exception as e:
        logger.info(
            f"An error has occurred in 'handle_nf_bs_status' function. ERROR: {e}"
        )


# Function to check if wallet value exist return boolean True, if not, return False
def check_wallet(wallet_value):
    value = wallet_value.strip()
    print(value)
    try:
        wd.driver.find_element(
            By.XPATH, "//option[contains(text(),'" + value + "')]"
        ).click()
    except NoSuchElementException:
        return [False, value]
    return [True, value]


# Function to decide if Wallet should create new wallet or choose the existing wallet.
def process_wallet(wallet_array):
    try:
        print(wallet_array)
        if wallet_array[0] == True:
            logger.info("WALLET FOUND!")
            wd.perform_action(
                "xpath", "//option[contains(text(),'" + wallet_array[1] + "')]", "click"
            )
            return
        else:
            logger.info("WALLET NOT FOUND, creating wallet...")
            create_nf_ds_new_wallet(wallet_array[1])

    except Exception as e:
        logger.info(
            f"An error has occured on function 'input_create_wallet' ERROR: {e}"
        )


# Whole process to create a new wallet
def create_nf_ds_new_wallet(wallet_name):
    try:
        logger.info("Creating new wallet: " + wallet_name)

        wd.driver.get(os.getenv("WEBTOOL_DATA_SERVICES_ADD_FULL_URL"))
        wd.wait_until_element(
            "name", os.getenv("NF_DATA_SERVICES_INPUT_NAME"), "visible"
        )

        # Proceed to input fields in Add Data Services Page

        logger.info("CURRENT PAGE: ADD DATA SERVICES")
        wd.perform_action(
            "name", os.getenv("NF_DATA_SERVICES_INPUT_NAME"), "sendkeys", wallet_name
        )
        wd.perform_action(
            "xpath", os.getenv("NF_DATA_SERVICE_TYPE_WALLET_BASED"), "click"
        )
        # find("name", os.getenv("NF_DATA_SERVICES_ADD_BUTTON_NAME"), "click")

        logger.info("WALLET CREATED FOR " + wallet_name + "- WALLET-BASED")
        time.sleep(3)

        # redirect_nf_data_services_add_page()
        wd.driver.get(os.getenv("WEBTOOL_BULK_SERVICES_ADD_FULL_URL"))
        wd.wait_until_element("xpath", os.getenv("NF_INPUT_NAME"), "visible")

        # in the future handling if there's a unique id for each row.
        "TODO"
    except Exception as e:
        logger.info(f"An error has occurred on 'create_nf_ds_new_wallet'\nERROR: {e}")


# Handle Bulk Service Type Dropdown
def handle_nf_bs_type(nf_type_value):
    try:
        element = None

        if nf_type_value == "Time-Based":
            element = os.getenv("NF_BS_TYPE_TIME_BASED")
        else:
            element = os.getenv("NF_BS_TYPE_WALLET_BASED")

        wd.perform_action("xpath", element, "click")

    except Exception as e:
        logger.info(f"An error has occurred in 'get_nf_type' function. ERROR: {e}")


# Handle Bulk Service Brands Multiple Checkbox
def handle_nf_bs_brands(brands_value):
    try:
        match brands_value.lower():
            case "ghp":
                element = nf.NF_BS_BRAND_GHP
            case "tm":
                element = nf.NF_BS_BRAND_TM
            case "postpaid":
                element = nf.NF_BS_BRAND_POSTPAID
            case "pw":
                element = nf.NF_BS_BRAND_PW

        wd.perform_action("id", element, "click")

    except Exception as e:
        logger.info(
            f"An error has occurred on function 'handle_nf_bs_brands'\nERROR: {e}"
        )
        wd.stop_process()


# Handle Bulk Service Deprov on empty Radio Button
def handle_bs_deprov_on_empty(deprov_value):
    element = None
    try:
        if deprov_value.lower() == "yes":
            element = os.getenv("NF_BS_DEPROV_ON_EMPTY_YES")
        else:
            element = os.getenv("NF_BS_DEPROV_ON_EMPTY_NO")

        wd.perform_action("xpath", element, "click")

    except Exception as e:
        logger.info(
            f"An error has occurred on function 'handle_bs_deprov_on_empty'\nERROR: {e}"
        )
        wd.stop_process()


# Handle Bulk Service Pre expiry notif Radio Button
def handle_bs_preexpiry_notifs(preexpiry_value):
    element = None
    try:
        if preexpiry_value.lower() == "yes":
            element = os.getenv("NF_BS_CANCEL_PRE_EXPIRY_YES")
        else:
            element = os.getenv("NF_BS_CANCEL_PRE_EXPIRY_NO")

        wd.perform_action("xpath", element, "click")

    except Exception as e:
        logger.info(
            f"An error has occurred on function 'handle_bs_preexpiry_notifs'\nERROR: {e}"
        )
        wd.stop_process()


# Handle Bulk Service Subscriptonless Radio Button
def handle_bs_subscription_less(subscription_value):
    element = None
    try:
        if subscription_value.lower() == "yes":
            element = os.getenv("NF_BS_SUBSCRIPTION_LESS")
        else:
            element = os.getenv("NF_BS_NOTSUBSCRIPTION_LESS")

        wd.perform_action("id", element, "click")

    except Exception as e:
        logger.info(
            f"An error has occurred on function 'handle_bs_subscription_less'\nERROR: {e}"
        )
        wd.stop_process()


# Handle Bulk Service Community Pool Radio Button
def handle_bs_community_pool(community_pool_value):
    element = None
    try:
        if community_pool_value.lower() == "yes":
            element = os.getenv("NF_BS_COMM_POOL_YES")
        else:
            element = os.getenv("NF_BS_COMM_POOL_NO")

        wd.perform_action("xpath", element, "click")

    except Exception as e:
        logger.info(
            f"An error has occurred on function 'handle_bs_community_pool'\nERROR: {e}"
        )
        wd.stop_process()


# Function to define the Service Expiry of Bulk Services
def nf_add_service_expiry(row_data, service_id):
    try:
        logger.info("Creating Service Expiry...")
        wd.driver.get(
            f"http://10.47.69.195/nf/index.php?mod=service_expiries&op=add&details_id={service_id}"
        )
        wd.wait_until_element("xpath", nf.NF_ADD_BTN_INPUT, "visible")

        # If Default Duration in Days value is No Expiry, choose radio button no expiry, else, multiple by 24
        if "no" in row_data[20].lower():
            wd.perform_action("id", "et_2", "click")
        else:
            # Input Expiry
            wd.perform_action("id", "expiry", "sendkeys", int(row_data[16]) * 24)

        # Click Add button
        wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")
        logger.info("Service Expiry Created with Default Values")
    except Exception as e:
        logger.info(
            f"An error has occurred on function 'nf_add_service_expiry'\nERROR: {e}"
        )
        wd.stop_process()


def nf_assign_api_default_flow(bs_service_id, flow_id, flow_name):
    try:
        logger.info(f"Assigning Default Flow and API Flow in Bulk Services For: ")

        # Redirect to Bulk Service Edit page for current service id
        wd.driver.get(
            f"{os.getenv('WEBTOOL_BASE_URL')}/nf/index.php?mod=bulk_services&op=edit&id={bs_service_id}"
        )
        wd.wait_until_element("xpath", os.getenv("NF_ADD_BTN_INPUT"), "visible")

        # Input Default Flow Dropwdown
        wd.perform_action(
            "xpath",
            f"//select[@name='default_flow']//option[@value='{flow_id}' and contains(text(), '{flow_name}')]",
            "click",
        )
        # Input API Flow Dropdown
        wd.perform_action(
            "xpath",
            f"//select[@name='api_flow']//option[@value='{flow_id}' and contains(text(), '{flow_name}')]",
            "click",
        )

        # Click Update button
        wd.perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")

    except Exception as e:
        logger.info(
            f"An error has occurred on function 'nf_assign_api_default_flow'\nERROR: {e}"
        )
        wd.stop_process()
