import datetime
import time

from typing import Dict, List
from flask import current_app
import json
import logging

def get_empty_config():
    return {
        'ids': [],
        'internet': {
            'enable': False,
            'ids': [],
            'url': ''
        },
        'zigbee': {
            'enable': False,
            'coordinator': -1,
            'internet': [],
            'ids': [],
            'pan': 1
        }
    }



class ConfigGenerator:

    _device_updates = {}
    _device_status = {}

    def __init__(self):
        self.last_config_path = 'res/last_config.json'
        self.basic_config_path = 'res/default_config.ini'
        self.reset()
        self.generate()

    def reset(self):
        with open(self.basic_config_path) as file:
            self.basic_config = file.read()
        self.prepared = ''
        self._config = self.load_config()

    def generate(self):
        now = int(time.time())
        for id in self._config['ids']:
            self._device_updates[id] = now

        self.prepared = self.basic_config.replace('$LAST_UPDATED', f'{now}')

        self.prepare_internet()
        self.prepare_zigbee()
        self.save_config(self._config)

        logging.info(f"Generated new config at {now}")

    def set_config(self, config: Dict):
        self.set_ids(config.get('ids', []))
        self.set_zigbee_config(config.get('zigbee', {}))
        self.set_internet_data(config.get('internet', {}))

    def set_zigbee_config(self, zigbee: Dict):
        zig = self._config['zigbee']

        zig['ids'] = zigbee.get('ids', [])
        zig['internet'] = zigbee.get('internet', [])
        zig['coordinator'] = zigbee.get('coordinator', -1)
        zig['enable'] = zigbee.get('enable', False)

        # default pan should not be 0 because 0 is a special zigbee id for automatically searching free network
        zig['pan'] = zigbee.get('pan', 1)

        if not zig['enable']:
            zig['ids'] = []

    def set_internet_data(self, data: Dict):
        net = self._config['internet']

        net['ids'] = data.get('ids', [])
        net['url'] = data.get('url', '')
        net['enable'] = data.get('enable', False)

        if not net['enable']:
            net['ids'] = []

    def set_ids(self, ids: List[int]):
        self._config['ids'] = ids
        self._device_status = {id: 'waiting' for id in ids}

    def get_zigbee_data(self):
        # thread safe deep copy
        return json.loads(json.dumps(self._config['zigbee']))
    
    def get_internet_data(self):
        # thread safe deep copy
        return json.loads(json.dumps(self._config['internet']))
    
    def get_config(self):
        # thread safe deep copy
        return json.loads(json.dumps(self._config))

    def prepare_zigbee(self):
        logging.debug("preparing zigbee data")
        config = self.prepared
        config = config.replace('$ZIGBEE_INTERNET', ','.join([str(_) for _ in self._config['zigbee']['internet']]))
        self.prepared = config

    def prepare_internet(self):
        config = self.prepared
        config = config.replace('$INTERNET_URL', self._config['internet']['url'])

        self.prepared = config

    def get_config_for_id(self, id: int) -> str:
        if self.prepared == '':
            logging.debug("prepared string is empty")
            return 'error: data was not perpared', 500

        if id not in self._config['ids']:
            logging.debug("given ID not present in used devices")
            return 'given ID not present in used devices', 400

        config = self.prepared.replace('$ID', str(id))

        config = config.replace('$USE_ZIGBEE', f"{1 if id in self._config['zigbee']['ids'] else 0}")
        config = config.replace('$ZIGBEE_COORDINATOR', f"{1 if id == self._config['zigbee']['coordinator'] else 0}")
        config = config.replace('$PAN', str(self._config['zigbee']['pan']))

        config = config.replace('$USE_INTERNET', f"{1 if id in self._config['internet']['ids'] else 0}")

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
    
    def last_updated(self, id: int) -> int:
        if id in self._device_updates.keys():
            return self._device_updates[id]
        else:
            return 0
        
    def save_config(self, config):
        #logging.debug("saving config {}", config)
        with open(self.last_config_path, 'w') as file:
            json.dump(config, file, indent=2)
        
    def load_config(self):
        try:
            with open(self.last_config_path, 'a+') as file:
                file.seek(0)
                last = json.load(file)
                logging.debug("last config found: {last}")
                return last
        except json.JSONDecodeError: 
            pass
        conf = get_empty_config()
        self.save_config(conf)
        return conf
    