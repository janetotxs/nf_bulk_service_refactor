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
    # Ensure the log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Format log file name
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"{service_name}_{timestamp}.log"
    log_path = os.path.join(log_dir, log_filename)

    # Create a custom logger
    logger = logging.getLogger(service_name)
    logger.setLevel(log_level)

    # Prevent duplicate handlers if already set up
    if not logger.handlers:
        # Console Handler
        console_handler = logging.StreamHandler()
        console_format = logging.Formatter(
            f"[%(asctime)s] [{service_name}] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_format)

        # File Handler
        file_handler = logging.FileHandler(log_path)
        file_format = logging.Formatter(
            f"[%(asctime)s] [{service_name}] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_format)

        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
