from typing import Dict, List
from datetime import datetime
import logging
import requests
import os
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import json

from app.config import Configs

DOTENV_PATH = "app/cloud/.env"

class CloudService:

    # These values are read from the file specified by `DOTENV_PATH`.

    CLOUD_TOKEN = None
    CLOUD_ADDRESS = None

    def __init__(self):
        self.filter = []
        self.reload_env()

    def reload_env(self, path=DOTENV_PATH):
        """
        The file specified by the parameter path (default is the constant `DOTENV_PATH`) contains simple key-value pairs (VAR = "VAL").
        This prevents sensitive information beeing published to git, because the .env file is never pushed.

        For the cloud service it is necessary to define
        CLOUD_ADDRESS = "address"
        CLOUD_TOKEN = "access token"
        """
        dotenv_loaded = load_dotenv(dotenv_path=path)
        if not dotenv_loaded:
            logging.error(f"could not load dotenv for cloud service. (file: {DOTENV_PATH})")

        logging.debug(f"cloud address: {os.getenv('CLOUD_ADDRESS')}")
        self.CLOUD_TOKEN = os.getenv("CLOUD_TOKEN")
        self.CLOUD_ADDRESS = os.getenv("CLOUD_ADDRESS")


    def set_id_filter(self, ids: List[int]):
        self.filter = ids

    def send_to_cloud(self, data: Dict):

        devID = data['id']

        device_filter = Configs.CloudConfig.DEVICES_TO_SEND

        if device_filter and devID not in device_filter:
            logging.debug(f"device {devID} not in cloud device filter ({device_filter})")
            return

        if not (self.CLOUD_ADDRESS and self.CLOUD_TOKEN):
            logging.error(f"no cloud address and token. Maybe the file {DOTENV_PATH} is missing?")
            return

        # send the data

        date = data['timestamp'].strftime("%Y-%m-%d")
        time = data['timestamp'].strftime("%Y%m%d%H%M%S")
        url = f"{self.CLOUD_ADDRESS}/objects/v1/utokyo_sandbox/utokyo/ble{devID}/{date}/{time}.json"

        logging.debug(f"sending data to {url}")

        formatted_data = self._format_data(data)
        #logging.debug(f"data to send to cloud: {formatted_data}")
        response = requests.put(url, headers={"Authorization": f"Basic {self.CLOUD_TOKEN}"}, data=formatted_data)


        logging.debug(f"response code: {response.status_code}")

    def _format_data(self, data: Dict) -> Dict:
        timestamp = data['timestamp'].isoformat(timespec='seconds')

        keys_to_send = set(['close', 'count', 'latitude', 'longitude', 'rssi_avg', 'rssi_std'])

        data = {k: data[k] for k in  keys_to_send.intersection(data.keys())}

        print(f"timestamp for cloud data: {timestamp}")

        formatted = {
            'data': [
                {
                'time': timestamp,
                'value': data
                }
            ]
        }
        return formatted

cloud_service = CloudService()