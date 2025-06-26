import datetime
from utils.logger2 import logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from utils.env_loader import get_env_variable
from nf.main_services import bulk_service as bs
from selenium.webdriver.support import expected_conditions as EC
from nf.nf_constants import NfConstants
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from nf.main_services.message_service import create_message
from utils.web_driver import WebDriver
from utils.google_sheet import GSheetClient
from dotenv import load_dotenv

load_dotenv()


LOCATOR_MAP = {
    "id": By.ID,
    "name": By.NAME,
    "classname": By.CLASS_NAME,
    "xpath": By.XPATH,
    "css": By.CSS_SELECTOR,
    "tag": By.TAG_NAME,
    "link": By.LINK_TEXT,
    "partial_link": By.PARTIAL_LINK_TEXT,
}

nf = NfConstants()
global wd
global gs
# wd = WebDriver()
gs = GSheetClient()


# wd.redirect_to_page(get_env_variable("WEBTOOL_LOGIN_FULL_URL"))


# def perform_action(locator, element, action, variable=None):
#     try:
#         by = LOCATOR_MAP.get(locator.lower())
#         if not by:
#             raise ValueError(f"Unsupported locator type: {locator}")

#         element = wd.driver.find_element(by, element)
#         actions = ActionChains(wd.driver)

#         if action == "click":
#             element.click()
#         elif action == "sendkeys":
#             element.clear()  # optional: clear before typing
#             element.send_keys(variable)
#         elif action == "clear":
#             element.clear()
#         elif action == "hover":
#             actions.move_to_element(element).perform()

#     except NoSuchElementException as e:
#         logger.error(f"Element not found: {locator}={element}. ERROR: {e}")


# # Input username and password then click Submit button
# perform_action("name", "uname", "sendkeys", 10012838)
# perform_action("name", "passwd", "sendkeys", "FEBruary!123321")
# # perform_action("id", nf.NF_LOGIN_BUTTON, "click")
# add_btn_element = WebDriverWait(wd.driver, 10).until(
#     EC.visibility_of_element_located((By.ID, "login-button"))
# )
# add_btn_element.click()

logger.info("Login Successful!")

dict_worksheets = {
    "bulkService": nf.WORKSHEET_TAB_BULK_SERVICES,
    "paramMatrix": nf.WORKSHEET_TAB_BULK_SERVICES_TAB_PARAM_MATRIX,
    "messages": nf.WORKSHEET_TAB_BULK_SERVICES_TAB_MESSAGES,
}
worksheets = gs.create_worksheets(dict_worksheets)

print(worksheets)
current_date = datetime.datetime.now().strftime("%Y-%m-%d")
bulk_data = worksheets["bulkService"].findall(current_date)

print(bulk_data[0].row)

# Declare Keyword value and Operation
# list_keywords = []
# provision_keyword_value = "TEST"
# deprovision_keyword_value = ""
# status_keyword_value = "TEST"
# extend_keyword_value = "^(GOLONGER|GOLONGER |GO LONGER|GO LONGER )(10)$"
# # list_keywords.append(provision_keyword_value)
# # list_keywords.append(deprovision_keyword_value)
# # list_keywords.append(status_keyword_value)
# # list_keywords.append(extend_keyword_value)

# keyword_conditions = {
#     "Provision": True if provision_keyword_value else False,
#     "Deprovision": True if deprovision_keyword_value else False,
#     "Status": True if status_keyword_value else False,
#     "Extend": (
#         True if extend_keyword_value and double_extend_value == "extend" else False
#     ),
# }

# # Start Loop for each keyword that is set to True
# for keyword_key, keyword_true in keyword_conditions.items():
#     if keyword_true:
#         logger.info(f"LOOPING: {keyword_key}")
#         # Get keyword value and operiations by calling function get_keyword_operation
#         keyword_value, selected_keyword_operation = get_keyword_operation(
#             keyword_key.lower(),
#             provision_keyword_value,
#             deprovision_keyword_value,
#             status_keyword_value,
#             extend_keyword_value,
#         )

#         logger.info(f"Keyword Operation: {keyword_key} Keyword Value: {keyword_value}")

#         # Redirect to Keyword Add Page using bulk service id
#         driver.get(
#             f"{get_env_variable('WEBTOOL_BASE_URL')}/nf/index.php?mod=service_keywords&op=add&details_id={bs_service_id}"
#         )

# add_btn_element = WebDriverWait(driver, 10).until(
#     EC.visibility_of_element_located((By.XPATH, nf.NF_ADD_BTN_INPUT))
# )

# Section to fill up the fields
# Dropdown Operation Field
# perform_action("xpath", selected_keyword_operation, "click")

# # Input Regex Field
# perform_action("name", nf.KEYWORD_REGEX_INPUT, "sendkeys", keyword_value)

# # Click Add Button
# # perform_action("xpath", nf.NF_ADD_BTN_INPUT, "click")

# logger.info(f"Service Keyword Successfully Created for {keyword_key.upper()}")
