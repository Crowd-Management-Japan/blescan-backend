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
    # 移動時間計算を行う間隔(秒)
    INTERVAL_SEC = 20
    # この時間未満の移動時間はノイズとして保存しない(エリアが隣接するとき、その境界を行き来する場合。または、別のエリアのMACアドレスが偶然一致した場合。)
    # 0に設定すれば、実質無効化
    MIN_MOVEMENT_TIME = timedelta(seconds=0)
    # この時間以上同じMACの検出がなければ、移動したとみなす(MACが変わった場合や、エリアから出たが他のエリアに行かなかった場合)
    # 大きな値にすれば、実質無効化
    NO_DETECTION_THRESHOLD = timedelta(minutes=1)
    # この時間以上同じ場所に滞在していたら、移動後の時間とみなす(同じ場所に長時間滞在した場合)
    # 大きな値にすれば、実質無効化
    SAME_PLACE_THRESHOLD = timedelta(seconds=20)
    # 検索する時間の範囲
    TIME_WINDOW = timedelta(minutes=15)
    # モード 1 or 2
    MODE = 2

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
        # 検索範囲の時刻を設定
        # current_time = datetime.now(TIMEZONE)
        current_time = datetime.now()
        start_time = current_time - self.TIME_WINDOW
        self.current_routes = self.routes[:]

        with self.session_scope() as session:
            # データベースからデータを取得し、Macアドレス順の時系列順にソート
            query = session.query(TemporaryTransitEntry).filter(
                TemporaryTransitEntry.timestamp >= start_time
            ).order_by(TemporaryTransitEntry.mac_address, TemporaryTransitEntry.timestamp)

            current_mac = None
            records = []

            # クエリの結果を1つずつ処理
            for record in query.all():
                # 別のmacになったら
                if current_mac != record.mac_address:
                    # (1つ前のmacの)レコードがある場合
                    if records:
                        delete_time = self.process_mac_records(current_time, records)
                        self.delete_old_data(current_mac, delete_time)
                    # 新しいmacのための準備
                    current_mac = record.mac_address
                    records = []
                # 同じmacのデータをためる
                records.append(record)

            # 最後のmacを処理
            if records:
                delete_time = self.process_mac_records(current_time, records)
                self.delete_old_data(current_mac, delete_time)

            # 移動時間の出力とデータベースへの保存
            transit_entries = []
            print(self.movements)
            for move in self.movements:
                transit_entry = TransitEntry(
                    start=move['from'],
                    end=move['to'],
                    timestamp=move['start'],
                    transit_time=move['duration'].total_seconds(),
                    aggregation_time=current_time
                )
                transit_entries.append(transit_entry)

            session.add_all(transit_entries)

        # except Exception as e:
        #     print(f"Error in calculate_transit: {e}")
        #     session.rollback()
        # finally:
        #     session.close()
        self.movements.clear()

    # MACアドレス1つ分の処理
    def process_mac_records_mode1(self, current_time: datetime, records: List[TemporaryTransitEntry]) -> Optional[datetime]:
        if not records:
            return None

        prev_start = records[0]
        current_start = prev_start
        prev_data = prev_start

        for record in records[1:]:
            # 現在のdevice_idが直前のdevice_idと異なる
            if record.device_id != prev_data.device_id:
                # 直前のIDがスタート位置と異なる (スタート位置から直前のIDへの移動が完了した)
                if prev_data.device_id != prev_start.device_id:
                    self.record_movement(prev_start, prev_data)

                    # スタート位置を更新する
                    prev_start = current_start
                # 現在のdevice_idのstartデータを更新する
                current_start = record

            # IDの変化がなく、同じIDに一定時間とどまっているとき
            elif record.timestamp - current_start.timestamp >= self.SAME_PLACE_THRESHOLD:
                if record.device_id != prev_start.device_id:
                    self.record_movement(prev_start, record)
                    prev_start = current_start

            prev_data = record

        # 最終レコードが一定時間更新されていなければ、移動が完了したとみなす
        if (current_time - records[-1].timestamp > self.NO_DETECTION_THRESHOLD) and (records[-1].device_id != prev_start.device_id):
            self.record_movement(prev_start, records[-1])
            prev_start = current_start

        return prev_start.timestamp

    def process_mac_records_mode2(self, _: datetime, records: List[TemporaryTransitEntry]) -> Optional[datetime]:
        if not records:
            return None

        prev_data = records[0]

        for record in records[1:]:
            # 現在のIDが直前のIDと異なる
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
