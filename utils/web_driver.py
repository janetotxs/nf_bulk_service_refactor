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
import time

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
            # options.add_argument("--headless")

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

    def redirect_to_page(self, url):
        max_retries = 5
        original_timeout = self.driver.timeouts.page_load
        logger.info(f"Redirecting to Page {url}")

        # We'll set a higher page load timeout to not interfere
        self.driver.set_page_load_timeout(60)

        for attempt in range(1, max_retries + 1):
            logger.info(f"Attempting to load the page {attempt}/{max_retries}")

            try:
                load_start = time.time()
                self.driver.get(url)

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

            finally:
                self.driver.set_page_load_timeout(original_timeout)

    # def redirect_to_page(self, url):
    #     max_retries = 5
    #     original_timeout = self.driver.timeouts.page_load
    #     logger.info(f"Redirecting to Page {url}")
    #     self.driver.set_page_load_timeout(45)  # Set timeout (seconds)

    #     for attempt in range(1, max_retries + 1):
    #         logger.info(f"Attempt {attempt} to load the page...")

    #         try:
    #             self.driver.get(url)
    #             # self.wait_until_element("xpath", "//input[@type='submit']", "clickable")
    #             logger.info("Site has been reached")
    #             break

    #         except TimeoutException as e:
    #             logger.warning(
    #                 f"Attempt {attempt} timed out. Refreshing and retrying..."
    #             )
    #             self.driver.execute_script("window.stop();")  # stop page load if needed
    #             self.driver.refresh()
    #             if attempt == max_retries:
    #                 logger.error("Max retries reached. Page did not load.")
    #                 raise Exception(f"Page timeout\nERROR: {e}")

    #         except Exception as e:
    #             logger.error(f"Unexpected error on attempt {attempt}: {e}")
    #             if attempt == max_retries:
    #                 raise
    #         finally:
    #             self.driver.set_page_load_timeout(original_timeout)

    # # Function to get success message after clicking submit button with retries using recursion
    # def click_jsbtn_get_success(
    #     self, locator, element, xpath_success_element, attempts=0
    # ):
    #     try:
    #         max_retries = 3
    #         logger.info("Click Submit Button...")
    #         by_type = LOCATOR_MAP.get(locator.lower())
    #         btn = self.driver.find_element(by_type, element)
    #         self.driver.execute_script("arguments[0].click();", btn)
    #         self.driver.execute_script("window.stop();")
    #         logger.info("Fetching Success Message...")
    #         self.wait_until_element(
    #             "xpath", xpath_success_element, "visible", timeout=13
    #         )
    #         success_msg = self.driver.find_element(
    #             By.XPATH, "//div[@class='success']"
    #         ).text

    #         logger.info(f"Success Message Retrieved: {success_msg}")
    #         return success_msg
    #     except TimeoutException as e:
    #         if attempts == max_retries:
    #             logger.error(f"Max retries reached. Page time out.. \nERROR: {e}")
    #             raise
    #         logger.warning(
    #             f"Page took time to load, refreshing page... Attempts {attempts+1}/{max_retries}"
    #         )
    #         time.sleep(2)
    #         self.driver.refresh()
    #         return self.click_jsbtn_get_success(
    #             locator, element, xpath_success_element, attempts + 1
    #         )

    def click_jsbtn_get_success(self, locator, element, xpath_success_element):
        max_retries = 3

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Click Submit Button... Attempt {attempt}")
                by_type = LOCATOR_MAP.get(locator.lower())
                button = self.driver.find_element(by_type, element)
                self.driver.execute_script("arguments[0].click();", button)
                time.sleep(2)

                logger.info("Fetching Success Message...")
                self.wait_until_element(
                    "xpath", xpath_success_element, "visible", timeout=13
                )
                success_msg = self.driver.find_element(
                    By.XPATH, xpath_success_element
                ).text
                logger.info(f"Success Message Retrieved: {success_msg}")
                return success_msg

            except TimeoutException as e:
                logger.warning(f"Timeout — Attempt {attempt}/{max_retries}")
                self.driver.execute_script("window.stop();")
                if attempt == max_retries:
                    logger.error(f"Max retries reached. Failing.\nERROR: {e}")
                    raise
                self.driver.refresh()
                time.sleep(2)

    # Function to wait until success message found or not after clicking submit button with retries using recursion
    def click_jsbtn_wait_stop(self, locator, element, xpath_success, attempts=0):
        try:
            max_retries = 2
            logger.info("Click Add Button...")
            by_type = LOCATOR_MAP.get(locator.lower())
            button = self.driver.find_element(by_type, element)
            self.driver.execute_script("arguments[0].click();", button)

            logger.info("Waiting for success page to load...")
            self.wait_until_element("xpath", xpath_success, "visible", timeout=30)

            logger.info(f"Success Message Found!, will proceed to next process..")
            return
        except TimeoutException as e:
            if attempts == max_retries:
                logger.warning(
                    f"Max retries reached. Stopping page from loading... \nERROR: {e}"
                )
                self.driver.execute_script("window.stop();")
                return
            logger.warning(
                f"TimeoutException occurred after clicking Add. Refreshing page.. Attempts {attempts+1}/{max_retries}"
            )
            time.sleep(2)
            self.driver.refresh()
            return self.click_jsbtn_wait_stop(
                locator, element, xpath_success, attempts + 1
            )

    def submit_form_and_wait_for_success(
        self,
        locator,
        element_button,
        success_xpath,
        max_retries=3,
        wait_timeout=15,
        max_total_time=60,
    ):
        """
        Clicks a submit button and waits for success message. Refreshes and retries if page hangs.

        Args:
            driver: Selenium WebDriver instance
            submit_locator: tuple (By.TYPE, value) e.g. (By.XPATH, "//button[@id='submit']")
            success_xpath: str, xpath for success message
            max_retries: int, how many times to retry on hang
            wait_timeout: int, seconds to wait for success per try
            max_total_time: int, hard limit in seconds for entire function

        Returns:
            str: success message text if found

        Raises:
            TimeoutException if success message not found after retries
        """
        start_time = time.time()

        for attempt in range(1, max_retries + 1):
            try:
                elapsed = time.time() - start_time
                if elapsed > max_total_time:
                    raise TimeoutException(
                        f"Total time {elapsed:.1f}s exceeded max {max_total_time}s"
                    )

                # Submit button
                logger.info(f"Attempt {attempt}: Clicking submit...")
                by_type = LOCATOR_MAP.get(locator.lower())
                button = self.driver.find_element(by_type, element_button)
                self.driver.execute_script("arguments[0].click();", button)

                logger.info(f"Waiting up to {wait_timeout}s for success message...")
                WebDriverWait(self.driver, wait_timeout).until(
                    EC.visibility_of_element_located((By.XPATH, success_xpath))
                )

                # Get success message
                success_msg = self.driver.find_element(By.XPATH, success_xpath).text
                logger.info(f"Success message found: {success_msg}")
                return success_msg

            except TimeoutException:
                logger.warning(f"Attempt {attempt} timed out waiting for success.")
                self.driver.execute_script("window.stop();")
                if attempt < max_retries:
                    logger.warning("Refreshing page to retry...")
                    self.driver.refresh()
                    time.sleep(2)
                else:
                    logger.warning("Max retries reached, failing.")
                    raise

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt}: {e}")
                self.driver.execute_script("window.stop();")
                if attempt < max_retries:
                    self.driver.refresh()
                    time.sleep(2)
                else:
                    raise

    def submit_form_and_validate_success(
        self,
        locator,
        element_button,
        success_xpath,
        max_retries=3,
        wait_timeout=13,
        max_total_time=60,
    ):
        """
        Click submit button and validate success message appears.
        If page load hangs, refresh and retry. On final retry, stop page load and continue.

        Args:
            driver: Selenium WebDriver instance
            submit_locator: tuple (By.TYPE, value) e.g. (By.XPATH, "//button[@id='submit']")
            success_xpath: str, xpath for success message
            max_retries: int, max attempts
            wait_timeout: int, seconds to wait for success per attempt
            max_total_time: int, overall hard limit in seconds
        """
        start_time = time.time()

        for attempt in range(1, max_retries + 1):
            try:
                elapsed = time.time() - start_time
                if elapsed > max_total_time:
                    logger.info(
                        f"Exceeded max total time {max_total_time}s. Continuing anyway."
                    )
                    return

                logger.info(f"Attempt {attempt}: Clicking submit...")
                by_type = LOCATOR_MAP.get(locator.lower())
                button = self.driver.find_element(by_type, element_button)
                self.driver.execute_script("arguments[0].click();", button)

                logger.info(
                    f"Waiting up to {wait_timeout}s for success message (ignore full load)..."
                )
                WebDriverWait(self.driver, wait_timeout).until(
                    EC.visibility_of_element_located((By.XPATH, success_xpath))
                )

                logger.info("Success message appeared. Continuing.")
                return  # success found → done

            except TimeoutException:
                logger.info(
                    f"Timeout waiting for success message on attempt {attempt}."
                )
                if attempt < max_retries:
                    self.driver.execute_script("window.stop();")
                    logger.info("Refreshing page to retry...")
                    self.driver.refresh()
                    time.sleep(2)
                else:
                    logger.info(
                        "Final retry failed — stopping page load and continuing anyway."
                    )
                    self.driver.execute_script("window.stop();")
                    return

            except Exception as e:
                logger.warning(f"Unexpected error: {e}")
                self.driver.execute_script("window.stop();")
                if attempt < max_retries:
                    logger.warning("Refreshing page due to error...")
                    self.driver.refresh()
                    time.sleep(2)
                else:
                    logger.warning(
                        "Final retry on error — stopping page load and continuing anyway."
                    )
                    self.driver.execute_script("window.stop();")
                    return
