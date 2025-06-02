from utils.logger import setup_logger
from utils.env_loader import get_env_variable
from utils.google_sheet import GSheetClient
from utils.web_driver import WebDriver
from smp.smp_constant import SMPConstants

logger = setup_logger(service_name="SMP")


#Calls SMP Constants
smp = SMPConstants()


def process_sequence_smp():
    logger.info(">>> Starting SMP process sequence")

    try:
        #login
        #Call Web Driver module
        wd = WebDriver()
        url_param = get_env_variable("SMP_WEBTOOL_URL")

        logger.info(">>> Redirecting to SMP login page")
        wd.redirect_nf_login_page(url_param) 
        wd.wait_until_element("name", get_env_variable("SMP_LOGIN_USERNAME_NAME"), "visible")

        logger.info(">>> Calling login sequence")
        login_sequence(wd)
        logger.info(">>> Login sequence completed")

        #Create New SMP Service
        add_smp_service(wd)

        #wd.stop_process()
    except Exception as e:
        logger.error(f"Error in SMP process: {e}")
        wd.stop_process()

# Login Sequence Function.
def login_sequence(wd):
    try:

        #Call Google Sheet module
        gs = GSheetClient()

        #Get Credential in Google sheet
        gsheet = smp.GSHEET_ID
        sheet_tab = smp.WORKSHEET_TAB_CREDENTIAL
        logger.info("Account Authorized!, Logging into SMP Webtool..")

        try:
            creds_data = gs.get_raw_values(gsheet, sheet_tab)
        except Exception as e:
             logger.error(f"Something went wrong fetching sheet data: {e}")
             raise
        
        # Skip the header (row 0), loop through each row of credentials
        for index, row in enumerate(creds_data[1:], start=2):  # Starting from row 2 (index 1)
            if len(row) < 2:
                logger.warning(f"Skipping row {index}: not enough columns for username/password.")
                continue
            username, password = row[0], row[1]

        # Input username and password then click Submit button
        wd.perform_action("name", get_env_variable("SMP_LOGIN_USERNAME_NAME"), "sendkeys", username)
        wd.perform_action("name", get_env_variable("SMP_LOGIN_PASSWORD_NAME"), "sendkeys", password)
        wd.perform_action("name", get_env_variable("SMP_LOGIN_BUTTON"), "click")

    except Exception as e:
        logger.info(f"\nSomething went wrong in the Login Sequence.\nERROR: {e}")
        wd.stop_process()

#Create New SMP Service
def add_smp_service(wd):
    try:
        wd.wait_until_element("xpath", smp.SUBSCRIBER_SERVICES, "visible")
        wd.perform_action("xpath", smp.SUBSCRIBER_SERVICES, "hover")

        wd.wait_until_element("xpath", smp.SUBSCRIBER_ADD_SERVICES, "clickable")
        wd.perform_action("xpath", smp.SUBSCRIBER_ADD_SERVICES, "click")
            
    
    except Exception as e:
             logger.error(f"Something went wrong creating SMP Service: {e}")
             raise

    
""" def get_data(wd):
    actions = ActionChains(wd)

    main_element = wd.wait_until_element_located("xpath", smp.SUBSCRIBER_GROUP )

    wd.find("xpath", smp.SUBSCRIBER_GROUP, "click")

    table = wd.find("xpath", "//table")

    # Parse table rows
    rows = table.find_elements(By.TAG_NAME, "tr")
    data = []
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        if not cells:  # Skip header
            cells = row.find_elements(By.TAG_NAME, "th")
        data.append([cell.text for cell in cells])

    # Convert to DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])
    print(df) """

    