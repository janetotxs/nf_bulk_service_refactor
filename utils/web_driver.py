import logging
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from utils.helpers import stop_process

logger = logging.getLogger(__name__)

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

            if platform.system() == "Windows":
                pass
            elif platform.system() == "Linux":
                options.add_argument("--headless")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")

            service = Service(ChromeDriverManager().install())
            chrome_driver = webdriver.Chrome(service=service, options=options)
            return chrome_driver

        except Exception as e:
            print(f"Failed to create chrome driver. Error: {e}")
            stop_process(driver=chrome_driver, message="Error", logger=logger)
            raise


    # Function to wait until element to be visible.
    def wait_until_element_located(self,locator, element):
        try:
            driver_wait = WebDriverWait(self.driver, 10)

            match locator:
                case "id":
                    result = (By.ID, element)
                case "name":
                    result = (By.NAME, element)
                case "classname":
                    result = (By.CLASS_NAME, element)
                case "xpath":
                    result = (By.XPATH, element)

            driver_wait.until(EC.presence_of_element_located((result)))

        except TimeoutException as e:
            logger.info(
                f"Page time out, page took time to load or validation of element failed\nERROR: {e}"
            )
            stop_process()

        except NoSuchElementException:
            logger.info("Element not found! please check if element is correct")
            stop_process()

    # Method to find element with action.
    def perform_action(self, locator, element, action, variable=None):
        try:
            element = self.driver.find_element(getattr(By, locator.upper()), element)

            if action == "click":
                element.click()
            elif action == "sendkeys":
                element.clear()  # optional: clear before typing
                element.send_keys(variable)
            elif action == "clear":
                element.clear()

        except NoSuchElementException as e:
            logger.error(f"Element not found: {locator}={element}. ERROR: {e}")
            stop_process()

    # Redirect to NF Login page
    def redirect_nf_login_page(self, url):
        self.driver.get(url)
        try:
            self.wait_until_element_located("name", "uname")
            logger.info("Browser launched!")
        except Exception as e:
            logger.info(f"Unable to access website\nERROR: {e}")
            stop_process()

    # Method to find element with action.
    def find(self, locator, element, action, variable=None):
        try:
            by_map = {
                "id": By.ID,
                "name": By.NAME,
                "classname": By.CLASS_NAME,
                "xpath": By.XPATH,
            }

            by = by_map.get(locator.lower())
            if not by:
                raise ValueError(f"Unsupported locator type: {locator}")

            el = self.driver.find_element(by, element)

            if action == "click":
                el.click()
            elif action == "sendkeys":
                el.send_keys(variable)
            elif action == "clear":
                el.clear()
            else:
                raise ValueError(f"Unsupported action: {action}")

        except NoSuchElementException as e:
            logger.info(
                f"Element not found! Please check if the element is correct.\nERROR: {e}"
            )
            stop_process()

        except Exception as e:
            logger.info(f"An error occurred in 'find': {e}")
            stop_process()

