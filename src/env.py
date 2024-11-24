import os

# Get environment variables for log file path and log level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "/app/logs/app.log")  # Default path in Docker

CONFIG_PATH = os.getenv("CONFIG_PATH", "/app/config.yaml")  # Default path in Docker
