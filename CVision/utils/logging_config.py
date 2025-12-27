import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("project.log", mode="a"),  # Single log file for the project
        logging.StreamHandler()  # Also log to console
    ]
)

# Get the logger instance
logger = logging.getLogger("project_logger")