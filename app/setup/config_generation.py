import logging
import datetime
import time

from typing import Dict, List
import logging

class ConfigGenerator:

    _device_updates = {}
    _device_status = {}

    def __init__(self):
        self.basic_config_path = 'res/default_config.ini'
        self.reset()

    def generate(self):
        now = int(time.time())
        for id in self.ids:
            self._device_updates[id] = now

        self.prepared = self.prepared.replace('$LAST_UPDATED', f'{now}')

        self.prepare_internet()
        self.prepare_zigbee()

        print(f"Generated new config at {now}")


    def set_zigbee_config(self, zigbee: Dict):
        self.zigbee_data = zigbee
        if not zigbee['use_zigbee']:
            self.zigbee_data['ids'] = []

    def set_internet_data(self, data: Dict):
        self.internet_data = data
        if not data['use_internet']:
            self.internet_data['ids'] = []

    def set_ids(self, ids: List[int]):
        self.ids = ids
        self._device_status = {id: 'waiting' for id in ids}

    def reset(self):
        with open(self.basic_config_path) as file:
            self.basic_config = file.read()
        self.zigbee_data = {'use_zigbee': False,'coordinator': 0, 'internet': [], 'ids': []}
        self.internet_data = {'use_internet': False, 'url': '', 'ids': []}
        self.ids = []
        self.prepared = self.basic_config

    def prepare_zigbee(self):
        config = self.prepared

        config = config.replace('$ZIGBEE_INTERNET', ','.join([str(_) for _ in self.zigbee_data['internet']]))
        self.prepared = config

    def prepare_internet(self):
        config = self.prepared
        config = config.replace('$INTERNET_URL', self.internet_data['url'])

        self.prepared = config

    def get_config_for_id(self, id: int) -> str:
        
        config = self.basic_config.replace('$ID', str(id))

        config = config.replace('$USE_ZIGBEE', f"{1 if self.zigbee_data['use_zigbee'] else 0}")
        config = config.replace('$ZIGBEE_COORDINATOR', f"{1 if id == self.zigbee_data['coordinator'] else 0}")

        config = config.replace('$USE_INTERNET', f"{1 if id in self.internet_data['ids'] else 0}")

        self._device_status[id] = 'requested'

        return config

    def set_status_ok(self, id: int):
        self._device_status[id] = 'ok'

    def get_device_status(self, id: int) -> str:
        if id not in self._device_status.keys():
            return None
        return self._device_status[id]
    
    def get_device_status_all(self):
        return self._device_status
    
    def last_updated(self, id: int) -> datetime.datetime:
        if id in self._device_updates.keys():
            return self._device_updates[id]
        else:
            return 0