import logging
import os
import sys

def setup_logger(name="SmartRetailAI"):
    """
    Sets up a simple, centralized logger for the project.
    It logs to both the console and a file inside the logs/ directory.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if logger is already initialized
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console Handler (to see logs in terminal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (to save logs for debugging)
    file_handler = logging.FileHandler(os.path.join(log_dir, "app.log"))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# Single instance for the whole app to use
logger = setup_logger()
