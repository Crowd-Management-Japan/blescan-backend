import os
from config import Config 
import logging

def create_folders():
    logging.debug("checking raspi log folders")
    if not os.path.exists(Config.RASPI_LOG_FOLDER):
        logging.debug("create folder")
        os.mkdir(Config.RASPI_LOG_FOLDER)


create_folders()