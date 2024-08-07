from datetime import datetime, timedelta, timezone
from typing import List, Tuple

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine, and_, or_

from app.database.database import db
from app.database.models import TransitEntry, TemporaryTransitEntry

def calculate_travel_time(combinations: List[Tuple[int, int]], max_exploration_time: int = 60) -> List[TransitEntry]:
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=max_exploration_time)

    """
    mac_addresses = TransitMacAddress.query.filter(
        TransitMacAddress.last_updated.between(start_time, end_time)
    ).all()

    transit_entries = []

    for mac in mac_addresses:
        for start_device_id, end_device_id in combinations:
            transit_data = find_transit_data(mac.mac_address, start_time, end_time, start_device_id, end_device_id)

            for start, end in transit_data:
                transit_time = (end.timestamp - start.timestamp).total_seconds()
                transit_entry = TransitEntry(
                    start=start.device_id,
                    end=end.device_id,
                    timestamp=start.timestamp,
                    transit_time=transit_time
                )
                transit_entries.append(transit_entry)

    with db.session.begin():
        db.session.add_all(transit_entries)
        db.session.commit()

    return transit_entries

def find_transit_data(mac_address: str, start_time: datetime, end_time: datetime, start_device_id: int, end_device_id: int) -> List[Tuple]:
    data_points = TemporaryTransitEntry.query.filter(
        and_(
            TemporaryTransitEntry.mac_address == mac_address,
            TemporaryTransitEntry.timestamp.between(start_time, end_time),
            or_(
                TemporaryTransitEntry.device_id == start_device_id,
                TemporaryTransitEntry.device_id == end_device_id
            )
        )
    ).order_by(TemporaryTransitEntry.timestamp).all()

    transit_data = []
    current_sequence = []

    for point in data_points:
        if not current_sequence:
            current_sequence.append(point)
        elif point.device_id != current_sequence[-1].device_id:
            if len(current_sequence) > 1:
                transit_data.append((current_sequence[0], current_sequence[-1]))
            current_sequence = [point]
        else:
            current_sequence.append(point)

    if len(current_sequence) > 1:
        transit_data.append((current_sequence[0], current_sequence[-1]))

    return transit_data
    """

# 設定値
# この時間未満の移動時間はノイズとして保存しない(エリアが隣接するとき、その境界を行き来する場合。または、別のエリアのMACアドレスが偶然一致した場合。)
MIN_MOVEMENT_TIME = timedelta(seconds=0)
# この時間以上同じMACの検出がなければ、移動したとみなす(MACが変わった場合や、エリアから出たが他のエリアに行かなかった場合)
NO_DETECTION_THRESHOLD = timedelta(minutes=5)
# この時間以上同じ場所に滞在していたら、移動後の時間とみなす(同じ場所に長時間滞在した場合)
SAME_PLACE_THRESHOLD = timedelta(minutes=3)
# 検索する時間の範囲
TIME_WINDOW = timedelta(minutes=15)

Base = declarative_base()

def create_db_session():
    engine = create_engine('sqlite:///instance/database.db')
    Session = sessionmaker(bind=engine)
    return Session()

def calculate_transit(routes: List[List[int]]) -> None:
    session = create_db_session()
    try:
        # ルートを両方向で設定
        full_routes = set((a, b) for route in routes for a, b in [route, route[::-1]])

        # 検索範囲の時刻を設定
        current_time = datetime.now(timezone(timedelta(hours=9)))
        start_time = current_time - TIME_WINDOW

        # データベースからデータを取得
        query = session.query(TemporaryTransitEntry).filter(
            TemporaryTransitEntry.timestamp >= start_time
        ).order_by(TemporaryTransitEntry.mac_address, TemporaryTransitEntry.timestamp)

        current_mac = None
        records = []
        movements = []

        # クエリの結果を1つずつ処理
        for record in query:
            # 別のmacになったら
            if current_mac != record.mac_address:
                # (1つ前のmacの)レコードがある場合
                if records:
                    process_mac_records(records, full_routes, movements)
                    delete_old_data(session, current_mac, records)
                # 新しいmacのための準備
                current_mac = record.mac_address
                records = []
            # 同じmacのデータをためる
            records.append(record)

        # 最後のmacを処理
        if records:
            process_mac_records(records, full_routes, movements)
            delete_old_data(session, current_mac, records)

        # 移動時間の出力とデータベースへの保存
        transit_entries = []
        for move in movements:
            print(f"Movement: {move['from']} -> {move['to']}, "
                  f"Start: {move['start']}, End: {move['end']}, "
                  f"Duration: {move['duration']}")

            transit_entry = TransitEntry(
                start=move['from'],
                end=move['to'],
                timestamp=move['start'],
                transit_time=move['duration'].total_seconds()
            )
            transit_entries.append(transit_entry)

        session.add_all(transit_entries)
        session.commit()

    except Exception as e:
        print(f"Error in calculate_transit: {e}")
        session.rollback()
    finally:
        session.close()

# MACアドレス1つ分の処理
def process_mac_records(records, full_routes, movements):
    if not records:
        return

    current_time = datetime.now()

    def record_movement(start_id, end_id, start_time, end_time):
        movement_time = end_time - start_time
        if movement_time >= MIN_MOVEMENT_TIME and (start_id, end_id) in full_routes:
            movements.append({
                'from': start_id,
                'to': end_id,
                'start': start_time,
                'end': end_time,
                'duration': movement_time
            })

    # first record
    start_id   = record[0].device_id
    start_time = record[0].timestamp
    current_id = start_id
    current_start_time = start_time
    last_record_time = start_time

    for record in records[1:]:
        # 現在のIDが直前のIDと異なる
        if record.device_id != current_id:
            # 直前のIDがスタート位置と異なる (スタート位置から直前のIDへの移動が完了した)
            if current_id != start_id:
                record_movement(start_id, current_id, start_time, last_record_time)

                # 直前のIDを新しいスタート位置とする
                start_id = current_id
                start_time = current_start_time

            current_id = record.device_id
            current_start_time = record.timestamp

        # IDの変化がなく、同じIDに一定時間とどまっているとき
        elif record.timestamp - current_start_time >= SAME_PLACE_THRESHOLD:
            if current_id != start_id:
                record_movement(start_id, current_id, start_time, record.timestamp)
                start_id = current_id
                start_time = current_start_time
            current_start_time = record.timestamp

        last_record_time = record.timestamp

    # 最終レコードが一定時間更新されていなければ、移動が完了したとみなす
    if current_time - last_record_time > NO_DETECTION_THRESHOLD:
        record_movement(start_id, current_id, start_time, last_record_time)


def delete_old_data(session: Session, mac_address: str, records: List[TemporaryTransitEntry]):
    latest_device = records[-1].device_id
    delete_before = None
    for record in reversed(records):
        if record.device_id != latest_device:
            delete_before = record.timestamp
            break

    if delete_before:
        print(f"For MAC {mac_address}: Delete data before {delete_before}")
        session.query(TemporaryTransitEntry).filter(
            TemporaryTransitEntry.mac_address == mac_address,
            TemporaryTransitEntry.timestamp < delete_before
        ).delete(synchronize_session=False)
    else:
        print(f"For MAC {mac_address}: No data to delete")