import multiprocessing as mp
import logging
from datetime import datetime, timedelta
from typing import List
from contextlib import contextmanager
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pytz import timezone

from app.database.models import TransitEntry, TemporaryTransitEntry

CONFIG_PATH = 'res/last_transit_config.json'
TIMEZONE = timezone('Asia/Tokyo')

# Variables for setting routes in interprocess communication

class TransitCalculator:

    # Interval for calculateing transit time (in seconds)
    # This is the interval for updating the data and the page, short intervals 
    # may result in high CPU and memory use
    #interval_sec = 20

    # Transit times shorter than this will not be saved as they are considered noise data
    # (e.g., when areas are adjacent and there's back-and-forth movement at the boundary,
    # or when a code from a different area accidentally mathces)
    # Set to 0 to effectively disable this filter
    #min_travel_time = timedelta(seconds=0)

    # This is the maximum time for searching for corresponsing codes, this also correponds 
    # to the maximum time for movement (e.g., when someone appears in a new area but the time
    # is longer than this, it will not be computed as movement)
    # Large values allow to capture even slow motion, but may result in higher CPU and memory use
    #max_travel_time = timedelta(minutes=15)

    # mode: 1 or 2
    # mode 1: Calculates transit time using "the oldest data from the previous location"
    #         and "the newest data from new location"
    # mode 2: Calculates transit time using "the newest data from the previous location"
    #         and "the oldest data from new location"

    #mode = 1


    # If no detection of the same code occurs for this duration or longer,
    # it's considered that movement has occured
    # (e.g., when the code is changed or when left one area and not go to another)
    # Set to a large value to effectively disable this feature
    NO_DETECTION_THRESHOLD = timedelta(minutes=1)

    # If staying in the same place for this duration or longer,
    # it's condisered as time after movement
    # (e.g., long stays in the same location)
    # Set to a large value to effecctively disable this feature
    SAME_PLACE_THRESHOLD = timedelta(seconds=20)


    def __init__(self, _):
        self.config_path = CONFIG_PATH
        self.timezone = TIMEZONE
        self.movements = []

        # create db session
        engine = create_engine('sqlite:///instance/database.db')
        self.Session = sessionmaker(bind=engine)

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

    def load_config(self):
        with open(self.config_path, 'r') as f:
            config = json.load(f)
        return config

    def apply_config(self, config: dict):
        self.interval_sec = config.get("refresh_time", 20)
        self.min_travel_time = timedelta(minutes=config.get("min_transit_time", 15))
        self.max_travel_time = timedelta(minutes=config.get("max_transit_time", 15))
        self.moving_avg = config.get("moving_avg", 5)
        self.reset_time = config.get("reset_time", "02:00")
        self.mode = config.get("calculation_mode", 1)
        self.combinations = config.get('combinations', [])
        self.combinations = [data[:2] for data in self.combinations]

    def calculate_transit(self) -> None:
        config = self.load_config()
        self.apply_config(config)

        if self.mode == 1:
            self.process_code_records = self.process_code_records_mode1
        elif self.mode == 2:
            self.process_code_records = self.process_code_records_mode2
        elif self.mode == 3:
            self.process_code_records = self.process_code_records_mode3    

        # calculate search time range
        current_time = datetime.now(self.timezone).replace(tzinfo=None)
        start_time = current_time - self.max_travel_time

        logging.debug(f"Calculating transit data from {start_time} to {current_time}")  

        # delete old data to keep searching light and fast
        self.delete_old_data(start_time)

        # open database session
        with self.session_scope() as session:
            # retrieve data from database and sort chronologically by code
            query = session.query(TemporaryTransitEntry).order_by(
                TemporaryTransitEntry.close_code, TemporaryTransitEntry.timestamp)

            current_code = None
            records = []

            # process records one by one and summarize data by transit code
            for record in query.all():
                if current_code != record.close_code:
                    if records:
                        # Determine if it is moving per transit code
                        # If it is moving, calculate transit time
                        self.process_code_records(current_time, records)
                    current_code = record.close_code
                    records = []
                records.append(record)

            # Process last transit code
            if records:
                self.process_code_records(current_time, records)
                #self.delete_old_data(current_code, delete_time)

            # "transit_entries" (array of TransitEntry type data) is the data for each single transit.
            # If multiple people are traveling the same route at the same time,
            # they are recorded as separate data.
            transit_entries = []
            # logging.debug(self.movements)
            for move in self.movements:
                transit_entry = TransitEntry(
                    scanner_from=move['from'],
                    scanner_to=move['to'],
                    time_start=move['start'],
                    time_end=move['end'],
                    travel_time=move['travel_time'].total_seconds(),
                    timestamp=current_time
                )
                transit_entries.append(transit_entry)

            # Example of how to get statistics
            # Take data from transit_data for each route (specify start and end)
            # and calculate the average and minimum.
            # Save the calculated data to TransitEntry (fields need to be changed) or new table.
            session.add_all(transit_entries)

        self.movements.clear()

        return self.interval_sec

    # Calculate transit time (mode 1)
    def process_code_records_mode1(self, current_time: datetime, records: List[TemporaryTransitEntry]) -> None:
        # Oldest data detected in the latest area before the most recent one
        prev_start = records[0]
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

    # Calculate transit time (mode 2)
    def process_code_records_mode2(self, _: datetime, records: List[TemporaryTransitEntry]) -> None:
        prev_data = records[0]

        for record in records[1:]:
            if record.device_id != prev_data.device_id:
                self.record_movement(prev_data, record)

            prev_data = record
    
    # Calculate transit time (mode 3)
    def process_code_records_mode2(self, _: datetime, records: List[TemporaryTransitEntry]) -> None:
        prev_data = records[0]

        for record in records[1:]:
            if record.device_id != prev_data.device_id:
                self.record_movement(prev_data, record)

            prev_data = record

    def record_movement(self, _from: TemporaryTransitEntry, _to: TemporaryTransitEntry) -> None:
        travel_time = _to.timestamp - _from.timestamp
        if travel_time >= self.min_travel_time and [_from.device_id, _to.device_id]:
            self.movements.append({
                'code'  : _from.close_code,
                'from'  : _from.device_id,
                'to'    : _to.device_id,
                'start' : _from.timestamp,
                'end'   : _to.timestamp,
                'travel_time': travel_time
            })

    def delete_old_data(self, last_time: datetime):
        with self.session_scope() as session:
            session.query(TemporaryTransitEntry).filter(
                TemporaryTransitEntry.timestamp < last_time
            ).delete(synchronize_session=False)