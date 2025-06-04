from utils.env_loader import get_env_variable
from utils.logger import setup_logger
from utils.google_sheet import GSheetClient
from utils.web_driver import WebDriver
from nf import bulk_service as bs
from nf import step_service as step
from utils.logger2 import logger
from nf.nf_constants import NfConstants
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import logging
import os
import platform
import sys
import datetime
import time

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
wd = WebDriver()
gs = GSheetClient()


def perform_action(self, locator, element, action, variable=None):
    try:
        by = LOCATOR_MAP.get(locator.lower())
        if not by:
            raise ValueError(f"Unsupported locator type: {locator}")

        element = driver.find_element(by, element)
        actions = ActionChains(self.driver)

        if action == "click":
            element.click()
        elif action == "sendkeys":
            element.clear()  # optional: clear before typing
            element.send_keys(variable)
        elif action == "clear":
            element.clear()
        elif action == "hover":
            actions.move_to_element(element).perform()

    except NoSuchElementException as e:
        logger.error(f"Element not found: {locator}={element}. ERROR: {e}")


options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)

url = driver.command_executor._url
session_id = driver.session_id
driver = webdriver.Remote(command_executor=url, desired_capabilities={})
driver.close()  # this prevents the dummy browser
driver.session_id = session_id

driver.get("http://10.47.69.195/nf/index.php?mod=steps&op=add")

brands = "GHP"

perform_action(
    "name",
    "//select[@name='in_service_id']//option[contains(text(), 'SMS_ALLNET_UNLI') and @value='196']",
    "click",
)

perform_action(
    "name",
    nf.NF_STEP_FUP_AMOUNT_FIELD,
    "sendkeys",
    500 if brands == "ghp" else 700,
)
