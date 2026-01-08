import logging

from eagle_eye.core.set_value import set_value
from eagle_eye.interfaces.api.app import run_api
from eagle_eye.utils.logger import setup_logger

if __name__ == "__main__":
    set_value()
    setup_logger()
    logging.info("Starting Eagle Eye...")
    run_api()
