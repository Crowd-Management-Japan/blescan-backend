import logging
from datetime import datetime, timedelta
from typing import List
from contextlib import contextmanager
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pytz import timezone
from collections import defaultdict

from app.database.models import TransitDetection, TransitEntry, TravelTime

CONFIG_PATH = 'res/last_transit_config.json'
TIMEZONE = timezone('Asia/Tokyo')

class TransitCalculator:
    # mode: 1, 2, or 3
    # mode 1: Calculates transit time using "the oldest data from the previous location"
    #         and "the newest data from new location"
    # mode 2: Calculates transit time using "the newest data from the previous location"
    #         and "the oldest data from new location"

    # If no detection of the same code occurs for this duration or longer, it's considered that movement has occured
    # (e.g., when the code is changed or when left one area and not go to another) (0 to disable)
    NO_DETECTION_THRESHOLD = timedelta(minutes=0)

    # If staying in the same place for this duration or longer, it's condisered as time after movement
    # (e.g., long stays in the same location) (large value to disable)
    SAME_PLACE_THRESHOLD = timedelta(seconds=1000)

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
        with open(self.config_path, 'r') as file:
            config = json.load(file)
        return config

    def apply_config(self, config: dict):
        self.interval_sec = config.get("refresh_time", 20)
        self.min_travel_time = timedelta(seconds=config.get("min_transit_time", 30))
        self.max_travel_time = timedelta(minutes=config.get("max_transit_time", 15))
        self.moving_avg = timedelta(minutes=config.get("moving_avg", 5))
        self.storage_time = timedelta(minutes=config.get("storage_time", 60))
        self.mode = config.get("calculation_mode", 1)
        self.combinations = config.get('combinations', [])
        #self.combinations = [data[:2] for data in self.combinations]

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
        current_time = datetime.now(self.timezone).replace(tzinfo=None, microsecond=0)

        #logging.debug(f"Calculating transit data from {start_time} to {current_time}")  

        # delete old data to keep searching light and fast
        self.delete_old_data(current_time, self.max_travel_time, self.storage_time)

        # open database session
        with self.session_scope() as session:
            # retrieve data from database and sort chronologically by code
            query = session.query(TransitDetection).order_by(
                TransitDetection.close_code, TransitDetection.timestamp)

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

                existing_entry = session.query(TransitEntry).filter_by(
                    code=move['code'],
                    scanner_from=move['from'],
                    scanner_to=move['to']
                ).first()

                if existing_entry:
                    existing_entry.time_start=move['start']
                    existing_entry.time_end=move['end']
                    existing_entry.travel_time=move['travel_time'].total_seconds()
                    existing_entry.timestamp=current_time
                else:
                    transit_entry = TransitEntry(
                        code=move['code'],
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
    def process_code_records_mode1(self, current_time: datetime, records: List[TransitDetection]) -> None:
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
    def process_code_records_mode2(self, _: datetime, records: List[TransitDetection]) -> None:
        prev_data = records[0]

        for record in records[1:]:
            if record.device_id != prev_data.device_id:
                self.record_movement(prev_data, record)

            prev_data = record
    
    # Calculate transit time (mode 3)
    def process_code_records_mode2(self, _: datetime, records: List[TransitDetection]) -> None:
        prev_data = records[0]

        for record in records[1:]:
            if record.device_id != prev_data.device_id:
                self.record_movement(prev_data, record)

            prev_data = record

    def record_movement(self, _from: TransitDetection, _to: TransitDetection) -> None:
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

    def compute_avg_travel_times(self):
        config = self.load_config()
        self.apply_config(config)

        now = datetime.now(self.timezone).replace(tzinfo=None, microsecond=0)
        time_window = now - self.moving_avg
        valid_routes = [data[:2] for data in self.combinations]
        travel_times_by_route = defaultdict(list)

        # retrieve recent entries for provided combinations
        with self.session_scope() as session:
            recent_entries = session.query(TransitEntry).filter(
                TransitEntry.timestamp >= time_window
            ).all()

            for entry in recent_entries:
                key = (entry.scanner_from, entry.scanner_to)
                for valid_route in valid_routes:
                    if entry.scanner_from == valid_route[0] and entry.scanner_to == valid_route[1]:       
                        travel_times_by_route[key].append(entry.travel_time)

        # calculate average travel times for each route
        avg_travel_times = {
            key: sum(times) / len(times)
            for key, times in travel_times_by_route.items() if times
        }

        # add entries to the database
        with self.session_scope() as session:
            for (scanner_from, scanner_to), avg_time in avg_travel_times.items():
                entry = TravelTime(
                    scanner_from=scanner_from,
                    scanner_to=scanner_to,
                    travel_time=int(avg_time),
                    timestamp=now
                )
                session.add(entry)
        #logging.debug(f"Average travel times: {avg_travel_times}")

    def delete_old_data(self, current_time: datetime, max_travel_time: datetime, storage_time: datetime):
        with self.session_scope() as session:
            session.query(TransitDetection).filter(
                TransitDetection.timestamp < current_time - max_travel_time
            ).delete(synchronize_session=False)

        with self.session_scope() as session:
            session.query(TransitEntry).filter(
                TransitEntry.timestamp < current_time - storage_time
            ).delete(synchronize_session=False)