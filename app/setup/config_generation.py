import datetime
import time

from typing import Dict, List
from flask import current_app
from collections import defaultdict
import app.util as util
import json
import logging

def get_empty_config():
    return {
        'ids': [],
        'locations': defaultdict(lambda: "0"),
        'internet': {
            'enable': True,
            'ids': [],
            'url': ''
        },
        'zigbee': {
            'enable': False,
            'coordinator': -1,
            'internet': [],
            'ids': [],
            'pan': 1
        },
        'counting': {
            'rssi_threshold': -100,
            'rssi_close_threshold': -75,
            'delta': 10,
            'static_ratio': 0.7
        },
        'beacon': {
            'target_id': '1233aacc0dc140a78085303a6d64ddb5',
            'shutdown_id': '',
            'scans': 8,
            'threshold': 3
        }
    }

_DEFAULT_CONFIG = get_empty_config()

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
        self._config = get_empty_config()
        util.dict_strict_deep_update(self._config, self.load_config())

    def set_default(self):
        self.set_config(get_empty_config())

    def generate(self):
        now = int(time.time())
        for id in self._config['ids']:
            self._device_updates[id] = now

        self.prepared = self.basic_config.replace('$LAST_UPDATED', f'{now}')

        self.prepare_internet()
        self.prepare_zigbee()
        self.prepare_counting()
        self.prepare_beacon()
        self.save_config(self._config)

        logging.info(f"Generated new config at {now}")

    def set_config(self, config: Dict):
        self.set_ids(config.get('ids', []))
        self.set_zigbee_config(config.get('zigbee', {}))
        self.set_internet_data(config.get('internet', {}))
        self.set_counting_config(config.get('counting', {}))
        self.set_beacon_config(config.get('beacon', {}))
        self.set_locations(config.get('locations', {}))

    def set_zigbee_config(self, zigbee: Dict):
        zig = self._config['zigbee']

        zig['ids'] = zigbee.get('ids', _DEFAULT_CONFIG['zigbee']['ids'])
        zig['internet'] = zigbee.get('internet', _DEFAULT_CONFIG['zigbee']['internet'])
        zig['coordinator'] = zigbee.get('coordinator', _DEFAULT_CONFIG['zigbee']['coordinator'])
        zig['enable'] = zigbee.get('enable', _DEFAULT_CONFIG['zigbee']['enable'])

        # default pan should not be 0 because 0 is a special zigbee id for automatically searching free network
        zig['pan'] = zigbee.get('pan', 1)

        if not zig['enable']:
            zig['ids'] = []

    def set_internet_data(self, data: Dict):
        net = self._config['internet']

        net['ids'] = data.get('ids', _DEFAULT_CONFIG['internet']['url'])
        net['url'] = data.get('url', _DEFAULT_CONFIG['internet']['url'])
        net['enable'] = data.get('enable', _DEFAULT_CONFIG['internet']['enable'])

        if not net['enable']:
            net['ids'] = []

    def set_counting_config(self, data: Dict):
        count = self._config['counting']
        default = _DEFAULT_CONFIG['counting']

        keys = ['rssi_threshold', 'rssi_close_threshold', 'delta', 'static_ratio']

        for key in keys:
            count[key] = data.get(key, default[key])

    def set_beacon_config(self, data: Dict):
        beacon = self._config['beacon']
        default = _DEFAULT_CONFIG['beacon']
        keys = ['target_id', 'scans', 'threshold', 'shutdown_id']
        for key in keys:
            beacon[key] = data.get(key, default[key])

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
    
    def get_locations(self):
        # thread safe deep copy
        return json.loads(json.dumps(self._config['locations']))

    def prepare_zigbee(self):
        logging.debug("preparing zigbee data")
        config = self.prepared
        config = config.replace('$ZIGBEE_INTERNET', ','.join([str(_) for _ in self._config['zigbee']['internet']]))
        self.prepared = config

    def prepare_internet(self):
        config = self.prepared
        config = config.replace('$INTERNET_URL', self._config['internet']['url'])

        self.prepared = config

    def prepare_counting(self):
        config = self.prepared
        
        config = config.replace('$RSSI_THRESHOLD', str(self._config['counting']['rssi_threshold']))
        config = config.replace('$RSSI_CLOSE_THRESHOLD', str(self._config['counting']['rssi_close_threshold']))
        config = config.replace('$DELTA', str(self._config['counting']['delta']))
        config = config.replace('$STATIC_RATIO', str(self._config['counting']['static_ratio']))

        self.prepared = config

    def prepare_beacon(self):
        config = self.prepared
        
        config = config.replace('$TARGET_ID', self._config['beacon']['target_id'])
        config = config.replace('$BEACON_SHUTDOWN', self._config['beacon']['shutdown_id'])
        config = config.replace('$SCANS', str(self._config['beacon']['scans']))
        config = config.replace('$BEACON_THRESHOLD', str(self._config['beacon']['threshold']))

        self.prepared = config


    def get_config_for_id(self, id: int) -> str:
        if self.prepared == '':
            logging.debug("prepared string is empty")
            return 'error: data was not perpared', 500

        if id not in self._config['ids']:
            logging.debug("given ID not present in used devices")
            return 'given ID not present in used devices', 400

        config = self.prepared.replace('$ID', str(id))

        config = config.replace('$USE_ZIGBEE', f"{1 if self._config['zigbee']['enable'] else 0}")
        config = config.replace('$ZIGBEE_COORDINATOR', f"{1 if id == self._config['zigbee']['coordinator'] else 0}")
        config = config.replace('$PAN', str(self._config['zigbee']['pan']))

        config = config.replace('$LOCATION', self._config['locations'].get(str(id), "0"))

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
                return last
        except json.JSONDecodeError: 
            pass
        conf = get_empty_config()
        self.save_config(conf)
        return conf
    
    def set_locations(self, locations: Dict):
        self._config['locations'] = {str(k): v for k, v in locations.items()}

    def set_location_str(self, id, location: str):
        self._config['locations'][str(id)] = location
    
    def set_location(self, id, latitude: float, longitude: float):
        self.set_location_str(id, f"{latitude}, {longitude}")
