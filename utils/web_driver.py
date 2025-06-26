from utils.logger2 import logger
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
from requests.exceptions import ReadTimeout
import time
import uuid

# logger = logging.getLogger(__name__)

# Optional: You can set this globally or make it a class attribute
DEFAULT_WAIT_TIME = 60

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
            options.page_load_strategy = "none"
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
                f"Timeout waiting for element: ({locator_type}, {element_value}) with condition '{condition}'"
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
            raise

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

    def stop_process(self):
        self.driver.quit()
        sys.exit("Terminating bot...")

    def redirect_to_page(self, url, xpath_btn_element=None):
        max_retries = 5
        # original_timeout = self.driver.timeouts.page_load
        logger.info(f"Redirecting to Page {url}")

        # We'll set a higher page load timeout to not interfere
        # self.driver.set_page_load_timeout(80)

        for attempt in range(1, max_retries + 1):
            logger.info(f"Loading page... (Attempts {attempt}/{max_retries})")

            try:
                load_start = time.time()
                self.driver.get(url)
                if not xpath_btn_element:
                    return

                self.wait_until_element("xpath", xpath_btn_element, "clickable")
                logger.info("Site has been reached")
                break  # success

            except TimeoutException as e:
                logger.warning(
                    f"Attempt {attempt} timed out (Selenium timeout). Stopping + refreshing..."
                )
                self.driver.execute_script("window.stop();")
                self.driver.refresh()

            except Exception as e:
                logger.warning(f"Unexpected error: {e}")
                # If stuck too long, stop the load manually
                if time.time() - load_start > 30:
                    logger.warning("Manually stopping load due to long hang.")
                    self.driver.execute_script("window.stop();")
                if attempt == max_retries:
                    logger.error("Max retries reached. Giving up.")
                    raise Exception(
                        f"Page load failed after {max_retries} attempts\nERROR: {e}"
                    )
                else:
                    logger.info("Refreshing and retrying...")
                    self.driver.refresh()

            # finally:
            #     self.driver.set_page_load_timeout(original_timeout)

    # currently using
    def submit_form_and_wait_for_success(
        self,
        locator,
        element_button,
        success_xpath,
        max_retries=2,
        wait_timeout=120,
        max_total_time=180,
        skip=False,
    ):
        start_time = time.time()
        logger.info(f"Submitting button...")
        by_type = LOCATOR_MAP.get(locator.lower())
        button = self.driver.find_element(by_type, element_button)
        self.driver.execute_script("arguments[0].click();", button)

        for attempt in range(1, max_retries):
            try:
                elapsed = time.time() - start_time
                if elapsed > max_total_time:
                    raise TimeoutException(
                        f"Total time {elapsed:.1f}s exceeded max {max_total_time}s"
                    )
                logger.info(f"Polling up to {wait_timeout}s for success message...")
                logger.info(
                    f"Fetching/Validating success message.. (Attempts {attempt}/{max_retries})"
                )
                success_found = False
                poll_start = time.time()

                while time.time() - poll_start < wait_timeout:
                    try:
                        element_success = self.driver.find_element(
                            By.XPATH, success_xpath
                        )
                        if element_success.is_displayed():
                            logger.info("Success message found!")
                            self.driver.execute_script(
                                "window.stop();"
                            )  # Stop loading ASAP
                            logger.info(f"Success Text = {element_success.text}")
                            return element_success.text
                            break

                    except (Exception, TimeoutError, ReadTimeout):
                        # If Element not found yet, catch exception, pass, then re-loop
                        pass

                    time.sleep(5)

                logger.warning(f"Attempt {attempt} timed out waiting for success.")
                self.driver.execute_script("window.stop();")
                if attempt < max_retries:
                    logger.warning("Refreshing page for next attempt...")
                    self.driver.refresh()
                    time.sleep(2)
                else:
                    logger.error("Max retries reached. No success message found.")
                    raise TimeoutException(
                        "Failed to detect success message after retries."
                    )

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt}: {e}")
                self.driver.execute_script("window.stop();")
                if attempt < max_retries:
                    self.driver.refresh()
                    time.sleep(2)
                else:
                    raise
