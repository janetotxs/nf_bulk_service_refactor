import logging
from utils.logger2 import logger
import os
import platform
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# logger = logging.getLogger(__name__)

# Optional: You can set this globally or make it a class attribute
DEFAULT_WAIT_TIME = 10

# Mapping of string locator types to Selenium By types
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

# Mapping of string wait conditions to Selenium EC functions
WAIT_CONDITION_MAP = {
    "presence": EC.presence_of_element_located,
    "visible": EC.visibility_of_element_located,
    "clickable": EC.element_to_be_clickable,
}


class WebDriver:

    def __init__(self):
        self.driver = self.create_chrome_driver()

    def create_chrome_driver(self):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            options.add_experimental_option("detach", True)
            options.add_argument("--no-sandbox")
            options.add_argument("--ignore-ssl-errors=yes")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--log-level=3")
            options.add_argument("--headless")

            if platform.system() == "Linux":
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")

            service = Service(ChromeDriverManager().install())
            chrome_driver = webdriver.Chrome(service=service, options=options)
            return chrome_driver

        except Exception as e:
            logger.info(f"Failed to create chrome driver. Error: {e}")
            raise

    # Function to wait until element to be visible.
    def wait_until_element(
        self,
        locator_type: str,
        element_value: str,
        condition: str,
        timeout: int = DEFAULT_WAIT_TIME,
    ):
        try:
            by_type = LOCATOR_MAP.get(locator_type.lower())
            if by_type is None:
                raise ValueError(f"Invalid locator type: {locator_type}")

            wait_condition = WAIT_CONDITION_MAP.get(condition.lower())
            if wait_condition is None:
                raise ValueError(f"Invalid wait condition: {condition}")

            driver_wait = WebDriverWait(self.driver, timeout)
            return driver_wait.until(wait_condition((by_type, element_value)))

        except TimeoutException as e:
            logger.info(
                f"Timeout waiting for element: ({locator_type}, {element_value}) with condition '{condition}'\nERROR: {e}"
            )
            raise

        except NoSuchElementException as e:
            logger.info(
                f"Element not found! Locator: ({locator_type}, {element_value})\nERROR: {e}"
            )
            raise

        except Exception as e:
            logger.exception(
                f"Unexpected error occurred while waiting for element: ({locator_type}, {element_value})\nERROR: {e}"
            )
            self.stop_process()

    # Method to find element with action.
    def perform_action(self, locator, element, action, variable=None):
        try:
            by = LOCATOR_MAP.get(locator.lower())
            if not by:
                raise ValueError(f"Unsupported locator type: {locator}")

            element = self.driver.find_element(by, element)
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

        except Exception as e:
            logger.error(f"Element not found: {locator}={element}. ERROR: {e}")
            raise

    # Redirect to  Login page
    def redirect_nf_login_page(self, url):
        try:
            self.driver.get(url)
        except Exception as e:
            logger.info(f"Unable to access website\nERROR: {e}")

    def stop_process(self):
        self.driver.quit()
        sys.exit("Terminating bot...")

    def redirect_to_page(self, url):
        logger.info(f"Redirecting to Page {url}")
        max_retries = 5
        # self.driver.set_page_load_timeout(30)  # Set timeout (seconds)

        for attempt in range(1, max_retries + 1):
            logger.info(f"Attempt {attempt} to load the page...")

            try:
                self.driver.get(url)
                self.wait_until_element("xpath", "//input[@type='submit']", "clickable")
                logger.info("Site reached!")
                break

            except TimeoutException as e:
                logger.warning(
                    f"Attempt {attempt} timed out. Refreshing and retrying..."
                )
                self.driver.execute_script("window.stop();")  # stop page load if needed
                self.driver.refresh()
                if attempt == max_retries:
                    logger.error("Max retries reached. Page did not load.")
                    raise Exception(f"Page timeout\nERROR: {e}")

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt}: {e}")
                if attempt == max_retries:
                    raise
