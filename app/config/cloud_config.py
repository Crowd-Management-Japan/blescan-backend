from typing import Dict, Any, List, Union
import json
import logging
import os

logging.debug("loading cloudconfig")

class CloudConfig:

    # define a list of device IDs to send to the cloud
    # if `None`, all devices will be sent. If the List is empty, no data will be sent
    DEVICES_TO_SEND: Union[List[int], None] = None

    def __init__(self, path: Union[str, None]):
        self.path = path
        if path:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if self._config_present():
                logging.debug(f"Cloud service config file is {path}")
                self.load()
                self.save()
            else:
                self.save()

    def _config_present(self) -> bool:
        return os.path.exists(self.path) and os.path.isfile(self.path)

    def _validate(self) -> bool:
        return True

    def save(self):
        self._validate()
        d = self._to_dict()
        with open(self.path, 'w+') as file:
            json.dump(d, file, indent=2)

    def load(self): 
        with open(self.path, 'r') as file:
            d = json.load(file)
            self._from_dict(d)

    def _to_dict(self) -> Dict: 
        return {
            'DEVICES_TO_SEND': self.DEVICES_TO_SEND
        }

    def _from_dict(self, d: Dict) -> bool:
        self.DEVICES_TO_SEND = d.get('DEVICES_TO_SEND', _default.DEVICES_TO_SEND)

# some private instance to get the default values
_default = CloudConfig(None)