from config import LOGS_DIR
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_FILE = os.path.join(LOGS_DIR, f"app_{timestamp}.log")

def setup_logging(log_level=logging.INFO):
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # File handler with rotation
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5)
    file_handler.setFormatter(formatter)

    # Root logger setup
    logging.basicConfig(
        level=log_level,
        handlers=[console_handler, file_handler]
    )

    # Reduce noise from third-party libraries
    logging.getLogger("playwright").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)

