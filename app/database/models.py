from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from flask_login import UserMixin

from typing import Dict

from .database import db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    superuser = db.Column(db.Boolean, nullable=False, default=True)

    @property
    def is_superuser(self):
        # override UserMixin property which always returns true
        # return the value of the superuser column instead
        return self.superuser

class CountEntry(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    scans: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    scantime: Mapped[float] = mapped_column(Float, nullable=True, default=None)

    tot_all: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    tot_close: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    inst_all: Mapped[float] = mapped_column(Float, nullable=True, default=None)
    inst_close: Mapped[float] = mapped_column(Float, nullable=True, default=None)
    stat_all: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    stat_close: Mapped[int] = mapped_column(Integer, nullable=True, default=None)

    rssi_avg: Mapped[float] = mapped_column(Float, nullable=True, default=None)
    rssi_std: Mapped[float] = mapped_column(Float, nullable=True, default=None)
    rssi_min: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    rssi_max: Mapped[int] = mapped_column(Integer, nullable=True, default=None)

    rssi_thresh: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    static_ratio: Mapped[float] = mapped_column(Float, nullable=True, default=None)
    latitude: Mapped[float] = mapped_column(Float, nullable=True, default=None)
    longitude: Mapped[float] = mapped_column(Float, nullable=True, default=None)

    @staticmethod
    def of_dict(data: Dict):
        entry = CountEntry()
        entry.id = data.get('id', None)
        entry.timestamp = data.get('timestamp', None)
        entry.scans = data.get('scans', 0)
        entry.scantime = data.get('scantime', 0)       

        entry.tot_all = data.get('tot_all', 0)
        entry.tot_close = data.get('tot_close', 0)
        entry.inst_all = data.get('inst_all', 0)
        entry.inst_close = data.get('inst_close', 0)
        entry.stat_all = data.get('stat_all', 0)
        entry.stat_close = data.get('stat_close', 0)

        entry.rssi_avg = data.get('rssi_avg', None)
        entry.rssi_std = data.get('rssi_std', None)
        entry.rssi_min = data.get('rssi_min', None)
        entry.rssi_max = data.get('rssi_max', None)

        entry.rssi_thresh = data.get('rssi_thresh', None)
        entry.static_ratio = data.get('static_ratio', None)
        entry.latitude = data.get('latitude', None)
        entry.longitude = data.get('longitude', None)

        return entry

    def to_dict(self, datetime_format="%Y-%m-%d %H:%M:%S"):
        data = {
            'id': self.id,
            'timestamp': self.timestamp.strftime(datetime_format),
            'scans': self.scans,
            'scantime': self.scantime,           
            'tot_all': self.tot_all,
            'tot_close': self.tot_close,
            'inst_all':self.inst_all,
            'inst_close':self.inst_close,
            'stat_all':self.stat_all,
            'stat_close':self.stat_close,
            'rssi_avg': self.rssi_avg,
            'rssi_std': self.rssi_std,
            'rssi_min': self.rssi_min,
            'rssi_max': self.rssi_max,
            'rssi_thresh': self.rssi_thresh,
            'static_ratio': self.static_ratio,           
            'latitude': self.latitude,
            'longitude': self.longitude

        }
        return data

class TemporaryTransitEntry(db.Model):
    __tablename__ = 'temporary_transit_data'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mac_number: Mapped[str] = mapped_column(String, nullable=False)
    device_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, primary_key=True, nullable=False)

    def of_dict(data: Dict):
        entry = TemporaryTransitEntry()
        entry.mac_number = data.get('mac_number', None)
        entry.device_id = data.get('ID', None)
        entry.timestamp = data.get('timestamp', None)

        return entry

class TransitEntry(db.Model):
    __tablename__ = 'transit_data'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    start: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    end: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=True, default=None)
    transit_time: Mapped[int] = mapped_column(Integer, nullable=True, default=None)