import logging
import os

from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

# Ensure the logs directory exists
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Define the logger
logger = logging.getLogger(__name__)

# Prevent duplicate handlers if the logger is already configured
if not logger.hasHandlers():
    logger.setLevel(logging.DEBUG)

    # Timed rotating file handler (rotates logs daily)
    current_date = datetime.now().strftime("%d-%m-%Y")
    log_file_path = os.path.join(LOG_DIR, f"{current_date}.log")
    file_handler = TimedRotatingFileHandler(
        log_file_path, when="D", interval=1, backupCount=7
    )
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler (prints logs to the console)
    console_handler = logging.StreamHandler()
    # Adjust the level for console logging if needed
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
