from utils.logger2 import logger
from nf.nf_constants import NfConstants
from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.common.exceptions import NoSuchElementException

from selenium.webdriver.common.action_chains import ActionChains


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


def perform_action(locator, element, action, variable=None):
    try:
        by = LOCATOR_MAP.get(locator.lower())
        if not by:
            raise ValueError(f"Unsupported locator type: {locator}")

        element = driver.find_element(by, element)
        actions = ActionChains(driver)

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
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=options)

driver.get("http://10.47.69.195/nf/index.php?mod=steps&op=add")
# http://10.47.69.195/nf/index.php?mod=flows&op=details&id=37790

brands = "TM"

perform_action(
    "xpath", "//option[contains(text(), 'HLR PLY') and @value='40']", "click"
)

perform_action(
    "xpath",
    (
        "//select[@name='hlr_ply_service_id']//option[@value='3']"
        if brands.lower() == "ghp"
        else "//select[@name='hlr_ply_service_id']//option[@value='2']"
    ),
    "click",
)
