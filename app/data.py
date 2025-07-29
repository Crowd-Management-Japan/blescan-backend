from datetime import datetime
from typing import Dict, List

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

        if data['rssi_avg'] is not None:
            data['rssi_avg'] = (data.get('rssi_avg', 0) * 1000 // 1) / 1000
        else:
            data['rssi_avg'] = 0

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

        online_sorted = sorted(online, key=lambda d: d['id'])

        return online_sorted + offline

def _get_empty_field(id: int):
    """
    Create an empty entry that contains at least all fields required for use jinja templates
    """
    return {
        'id': id,
        'timestamp': datetime.min,
        'last_updated': datetime.min,
        'is_online': False,
        'scans': -1,
        'scantime': -1,
        'tot_all': -1,
        'tot_close': -1,
        'inst_all': -1,
        'inst_close': -1,
        'stat_all': -1,
        'stat_close': -1,
        'rssi_avg': -1,
        'rssi_thresh': -1,
        'static_ratio': -1
    }
