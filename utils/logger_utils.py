import logging
logger = logging.getLogger("petrotrack_logger")

def main_exception(view, exception, error_message=None):
    logger.error(f"Exception raised in {view} as {exception}")

def main_info(view, message):
    logger.info(f"Info log in {view}: {message}")
