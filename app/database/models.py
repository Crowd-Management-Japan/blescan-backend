from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from typing import Dict

from .database import db

class CountEntry(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, primary_key=True)

    count: Mapped[int] = mapped_column(Integer)
    close: Mapped[int] = mapped_column(Integer)
    rssi_avg: Mapped[float] = mapped_column(Float)
    rssi_std: Mapped[float] = mapped_column(Float)
    rssi_min: Mapped[int] = mapped_column(Integer)
    rssi_max: Mapped[int] = mapped_column(Integer)

    @staticmethod
    def of_dict(data: Dict):
        entry = CountEntry()
        entry.id = data.get('id', None)
        entry.timestamp = data.get('timestamp', None)

        entry.count = data.get('count', 0)
        entry.close = data.get('close', 0)
        entry.rssi_avg = data.get('rssi_avg', 0)
        entry.rssi_std = data.get('rssi_std', 0)
        entry.rssi_min = data.get('rssi_min', 0)
        entry.rssi_max = data.get('rssi_max', 0)

        return entry



    def __repr__(self):
        return 'Entry %r' % self.last_updated
