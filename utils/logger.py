import logging
import os
from datetime import datetime

def setup_logger(service_name: str, log_level=logging.INFO, log_dir="logs") -> logging.Logger:
    """
    Set up and return a logger instance for the given service name.

    :param service_name: Name of the RPA service (e.g., 'NF', 'SMP').
    :param log_level: Logging level (default: INFO).
    :param log_dir: Directory to store log files.
    :return: Configured logger.
    """
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"{service_name}_{timestamp}.log"
    log_path = os.path.join(log_dir, log_filename)

    logger = logging.getLogger(service_name)
    logger.setLevel(log_level)

    if not logger.handlers:
        formatter = logging.Formatter(
            fmt=f"[%(asctime)s,%(msecs)03d]: [{service_name}] : [%(levelname)s]:[%(filename)s:%(lineno)d - %(funcName)s()]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # File Handler
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
#Full tracebacks only to the log file
def log_traceback(logger):
    import traceback
    traceback_str = traceback.format_exc()
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.acquire()
            try:
                handler.stream.write(traceback_str + "\n")
                handler.flush()
            finally:
                handler.release()