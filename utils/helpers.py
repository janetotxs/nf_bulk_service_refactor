import sys
import logging

logger = logging.getLogger(__name__)

def stop_process(driver=None, message=None, logger=None):
    """
    Stops the process by optionally quitting the driver , logs the name of the module it was called from.

    Args:
        driver (webdriver, optional): A Selenium WebDriver instance to quit. Defaults to None.
        message (str, optional): An optional error message to log before exiting. Defaults to None.
        logger (logging.Logger, optional): A logger instance to use for logging messages. If not provided, a default logger for the current module will be used.
    """

    if logger is None:
        logger = logging.getLogger(__name__)

    if message:
        logger.error(message)
        print(message)

    if driver:
        try:
            driver.quit()
        except Exception as e:
            logger.warning(f"Could not quit driver cleanly: {e}")

    sys.exit(1)



