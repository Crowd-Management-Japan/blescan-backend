from datetime import datetime
from typing import Dict

_instance = None

class DataReceiver:

    _data = {}

    @staticmethod
    def get_instance():
        global _instance
        if _instance == None:
            _instance = DataReceiver()
        return _instance

    def reset(self):
        self._data = {}

    def set_data(self, data: Dict):
        id = data['id']
        time = datetime.now()
        
        data.update({'last_updated': time})

        self._data[id] = data


    def get_last_updated(self, id: int) -> datetime:
        return self._data.get(id, {'last_updated': datetime.min})['last_updated']

    def get_data(self, id: int) -> Dict:
        return self._data.get(id, self.get_last_updated(id))


