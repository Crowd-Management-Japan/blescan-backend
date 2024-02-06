from datetime import datetime, timedelta
from typing import Dict, List
import logging

_instance = None

class DataReceiver:

    _data = {}

    @staticmethod
    def get_instance():
        global _instance
        if _instance == None:
            _instance = DataReceiver()
        return _instance

    def __init__(self):
        self._data = {_: _get_empty_field(_) for _ in range(50)}

    def set_data(self, data: Dict):
        id = int(data['id'])
        
        data.update({'last_updated': datetime.now(), 'is_online': True})

        self._data[id] = data


    def get_last_updated(self, id: int) -> datetime:
        return self._data.get(id, {'last_updated': datetime.min})['last_updated']

    def get_data(self):
        return self._data

    def get_data_by_id(self, id: int) -> Dict:
        return self._data.get(id, {'id': id, 'last_updated': self.get_last_updated(id)})
    
    def get_data_as_list(self):
        return [_ for _ in self._data.values()]
    
    def get_data_online_first(self) -> List:
        online = [d for d in self._data.values() if d['is_online']]
        offline = [d for d in self._data.values() if not d['is_online']]

        return online + offline
    
    def get_total_count(self):
        sum = 0
        for device in self._data.values():
            sum += device.get('count', 0)
        return sum


def _get_empty_field(id: int):
    """
    Create an empty entry that contains at least all fields required for used jinja templates
    """
    return {
        'id': id,
        'timestamp': datetime.min,
        'last_updated': datetime.min, # last updated is the local time of the server
        'is_online': False,
        'count': 0,
        'avgRSSI': 0
    }
