import multiprocessing as mp
from datetime import datetime, timedelta
from typing import List, Optional
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pytz import timezone

from app.database.models import TransitEntry, TemporaryTransitEntry

TIMEZONE = timezone('Asia/Tokyo')

# Variables for setting routes in interprocess communication
manager = mp.Manager()
shared_routes = manager.list([])

class TransitCalculator:
    Base = declarative_base()

    # Interval for calculateing transit time (in seconds)
    INTERVAL_SEC = 20

    # Transit times shorter than this will not be saved as they are considered noise data
    # (e.g., when areas are adjacent and there's back-and-forth movement at the boundary,
    # or when a MAC address from a different area accidentally mathces)
    # Set to 0 to effectively disable this filter
    MIN_MOVEMENT_TIME = timedelta(seconds=0)

    # If no detection of the same MAC address occurs for this duration or longer,
    # it's considered that movement has occured
    # (e.g., when the MAC address is changed or when left one area and not go to another)
    # Set to a large value to effectively disable this feature
    NO_DETECTION_THRESHOLD = timedelta(minutes=1)

    # If staying in the same place for this duration or longer,
    # it's condisered as time after movement
    # (e.g., long stays in the same location)
    # Set to a large value to effecctively disable this feature
    SAME_PLACE_THRESHOLD = timedelta(seconds=20)

    # Time range for searching
    TIME_WINDOW = timedelta(minutes=15)

    # Mode: 1 or 2
    # Mode 1: Calculates transit time using "the oldest data from the previous location"
    #         and "the newest data from new location"
    # Mode 2: Calculates transit time using "the newest data from the previous location"
    #         and "the oldest data from new location"
    MODE = 1

    def __init__(self, _):
        # create db session
        engine = create_engine('sqlite:///instance/database.db')
        self.Session = sessionmaker(bind=engine)

        self.routes = shared_routes
        self.current_routes = []

        self.movements = []

        if self.MODE == 1:
            self.process_mac_records = self.process_mac_records_mode1
        if self.MODE == 2:
            self.process_mac_records = self.process_mac_records_mode2

    @contextmanager
    def session_scope(self):
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def calculate_transit(self) -> None:
        # Calculate search time range
        current_time = datetime.now()
        start_time = current_time - self.TIME_WINDOW

        # Load route combination settings
        self.current_routes = self.routes[:]

        # Open Database session
        with self.session_scope() as session:
            # Retrieve data from database and sort chronologically by Mac address
            query = session.query(TemporaryTransitEntry).filter(
                TemporaryTransitEntry.timestamp >= start_time
            ).order_by(TemporaryTransitEntry.mac_address, TemporaryTransitEntry.timestamp)

            current_mac = None
            records = []

            # Process records one by one and summarize data by mac address
            for record in query.all():
                if current_mac != record.mac_address:
                    if records:
                        # Determine if it is moving per MAC address
                        # If it is moving, calculate transit time
                        delete_time = self.process_mac_records(current_time, records)
                        self.delete_old_data(current_mac, delete_time)
                    current_mac = record.mac_address
                    records = []
                records.append(record)

            # Process last MAC address
            if records:
                delete_time = self.process_mac_records(current_time, records)
                self.delete_old_data(current_mac, delete_time)

            # "transit_entries" (array of TransitEntry type data) is the data for each single transit.
            # If multiple people are traveling the same route at the same time,
            # they are recorded as separate data.
            transit_entries = []
            # print(self.movements)
            for move in self.movements:
                transit_entry = TransitEntry(
                    start=move['from'],
                    end=move['to'],
                    timestamp=move['start'],
                    transit_time=move['duration'].total_seconds(),
                    aggregation_time=current_time
                )
                transit_entries.append(transit_entry)

            # Example of how to get statistics
            # Take data from transit_data for each route (specify start and end)
            # and calculate the average and minimum.
            # Save the calculated data to TransitEntry (fields need to be changed) or new table.
            session.add_all(transit_entries)

        self.movements.clear()

    # Calculate transit time (Mode 1)
    def process_mac_records_mode1(self, current_time: datetime, records: List[TemporaryTransitEntry]) -> Optional[datetime]:
        if not records:
            return None

        # Oldest data detected in the
        prev_start = records[0]
        # Oldest data detected in the latest area before the most recent one
        current_start = prev_start
        # Data before one of the latest
        prev_data = prev_start

        for record in records[1:]:
            if record.device_id != prev_data.device_id:
                # Movement completed from prev_start to prev_data
                if prev_data.device_id != prev_start.device_id:
                    self.record_movement(prev_start, prev_data)

                    prev_start = current_start
                current_start = record

            # Check if stayed in the same area for a threshold time
            elif record.timestamp - current_start.timestamp >= self.SAME_PLACE_THRESHOLD:
                if record.device_id != prev_start.device_id:
                    self.record_movement(prev_start, record)
                    prev_start = current_start

            prev_data = record

        # Consider movement complete if no updates for a threshold time
        if (current_time - records[-1].timestamp > self.NO_DETECTION_THRESHOLD) and (records[-1].device_id != prev_start.device_id):
            self.record_movement(prev_start, records[-1])
            prev_start = current_start

        return prev_start.timestamp

    # Calculate transit time (Mode 2)
    def process_mac_records_mode2(self, _: datetime, records: List[TemporaryTransitEntry]) -> Optional[datetime]:
        if not records:
            return None

        prev_data = records[0]

        for record in records[1:]:
            if record.device_id != prev_data.device_id:
                self.record_movement(prev_data, record)

            prev_data = record

        return prev_data.timestamp

    def record_movement(self, _from: TemporaryTransitEntry, _to: TemporaryTransitEntry) -> None:
        movement_time = _to.timestamp - _from.timestamp
        if movement_time >= self.MIN_MOVEMENT_TIME and [_from.device_id, _to.device_id] in self.current_routes:
            self.movements.append({
                'from'  : _from.device_id,
                'to'    : _to.device_id,
                'start' : _from.timestamp,
                'end'   : _to.timestamp,
                'duration': movement_time
            })

    def delete_old_data(self, mac_address: str, start_time: datetime):
        with self.session_scope() as session:
            count = session.query(TemporaryTransitEntry).filter(
                TemporaryTransitEntry.mac_address == mac_address,
                TemporaryTransitEntry.timestamp < start_time
            ).delete(synchronize_session=False)
            print(f'Delete {count} records for MAC {mac_address} before {start_time}')
