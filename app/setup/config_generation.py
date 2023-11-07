import logging
import datetime
import time

from typing import Dict, List

class ConfigGenerator:

    _device_updates = {}

    def __init__(self):
        self.basic_config_path = 'res/default_config.ini'
        self.reset()

    def set_zigbee_config(self, zigbee: Dict):
        self.zigbee_data = zigbee
        if zigbee['internet']:
            self.use_zigbee = True

        timestamp = int(time.time())

        for id in zigbee['ids']:
            self._device_updates[id] = timestamp

        logging.info("Updated zigbee data")
        print(self.zigbee_data)

    def set_internet_data(self, internet: List, url: str):
        self.internet_nodes = internet
        self.internet_url = url

    def reset(self):
        with open(self.basic_config_path) as file:
            self.basic_config = file.read()
        self.use_zigbee = False
        self.zigbee_data = {'coordinator': 0, 'internet': [], 'ids': []}
        self.set_internet_data([], '')

    def get_config_for_id(self, id: int) -> str:
        
        config = self.basic_config.replace('$ID', str(id))
        config = config.replace('$LAST_UPDATED', f'{self.last_updated(id)}')

        config = config.replace('$USE_ZIGBEE', f'{1 if self.use_zigbee else 0}')

        if id in self.zigbee_data['ids']:
            config = config.replace('$ZIGBEE_INTERNET', ','.join([str(_) for _ in self.zigbee_data['internet']]))
            config = config.replace('$ZIGBEE_COORDINATOR', f"{1 if id == self.zigbee_data['coordinator'] else 0}")
        else:
            print("id not in zigbee ids")

        config = config.replace('$USE_INTERNET', f"{1 if id in self.internet_nodes else 0}")
        config = config.replace('$INTERNET_URL', self.internet_url)

        return config
    
    def last_updated(self, id: int) -> datetime.datetime:
        if id in self._device_updates.keys():
            return self._device_updates[id]
        else:
            return 0