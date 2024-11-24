import logging
from env import LOG_LEVEL, LOG_FILE_PATH
import os

def setup_logger():
    # Map log level from string to logging level
    log_level = LOG_LEVEL  # Default to INFO if invalid level

    # Ensure log file directory exists
    os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

    # Get a logger specific to your application
    logger = logging.getLogger("tuya-2-mqtt")  # Use a unique name for your application

    # Clear any existing handlers (to avoid duplicates if `setup_logger` is called multiple times)
    logger.handlers.clear()

    # Set logging level
    logger.setLevel(log_level)

    # Create file handler
    file_handler = logging.FileHandler(LOG_FILE_PATH)
    file_handler.setLevel(log_level)

    # Create stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)

    # Define formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger  # Return the configured logger instance
