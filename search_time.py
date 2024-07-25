from datetime import datetime, timedelta
from dateutil import parser
import time
from sqlalchemy import create_engine, Table, MetaData, select
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///instance/database.db')
metadata = MetaData()

temporary_transit_data = Table('temporary_transit_data', metadata, autoload_with=engine)

def search_time():
    print('--------------------------------------------------------------------------- ')
    print('start searching transit time ')

    n = 1 # transit_time

    transit_end = datetime.now()
    transit_start = transit_end - timedelta(minutes=n)
    print(f"探索終了時間", transit_end)
    print(f"探索開始時間", transit_start)

    query = select(temporary_transit_data).where(
        (temporary_transit_data.c.timestamp >= transit_start) &
        (temporary_transit_data.c.timestamp <= transit_end)
    )

    Session = sessionmaker(bind=engine)
    session = Session()
    results = session.execute(query).fetchall()
    session.close()

    # data_list = [
    #     {
    #         "id": row[0],
    #         "mac_number": row[1],
    #         "device_id": row[2],
    #         "timestamp": row[3]
    #     } for row in results
    # ]

    # test_data
    data_list = [
        {"id": 21633, "mac_number": "1554406469942", "device_id": 2, "timestamp": "2024-07-24 17:53:05"},
        {"id": 21636, "mac_number": "1431015412121514815", "device_id": 3, "timestamp": "2024-07-24 17:53:05"},
        {"id": 21627, "mac_number": "569114950851110", "device_id": 3, "timestamp": "2024-07-24 17:54:05"},
        {"id": 21634, "mac_number": "14811975421413815", "device_id": 3, "timestamp": "2024-07-24 17:54:05"},
        {"id": 21622, "mac_number": "4911014110541206", "device_id": 2, "timestamp": "2024-07-24 17:55:05"},
        {"id": 21624, "mac_number": "423615111212112414", "device_id": 3, "timestamp": "2024-07-24 17:55:05"},
        {"id": 21626, "mac_number": "7131363214121250", "device_id": 1, "timestamp": "2024-07-24 17:55:05"},
        {"id": 21623, "mac_number": "7113609812111129", "device_id": 2, "timestamp": "2024-07-24 17:56:05"},
        {"id": 21631, "mac_number": "13751435671310514", "device_id": 1, "timestamp": "2024-07-24 17:57:05"},
        {"id": 21637, "mac_number": "1350813111151241414", "device_id": 2, "timestamp": "2024-07-24 17:57:05"},
        {"id": 21632, "mac_number": "7133430141266100", "device_id": 3, "timestamp": "2024-07-24 17:58:05"},
        {"id": 21628, "mac_number": "1501011545939118", "device_id": 2, "timestamp": "2024-07-24 17:59:05"},
        {"id": 21630, "mac_number": "43101570154651313", "device_id": 1, "timestamp": "2024-07-24 17:59:05"},
        {"id": 21629, "mac_number": "6707211461051311", "device_id": 1, "timestamp": "2024-07-24 18:00:05"},
        {"id": 21619, "mac_number": "6247149115515137", "device_id": 2, "timestamp": "2024-07-24 18:01:05"},
        {"id": 21620, "mac_number": "15612138111272713", "device_id": 3, "timestamp": "2024-07-24 18:01:05"},
        {"id": 21621, "mac_number": "74623215512457", "device_id": 3, "timestamp": "2024-07-24 18:02:05"},
        {"id": 21625, "mac_number": "15688813278495", "device_id": 1, "timestamp": "2024-07-24 18:03:05"},
        {"id": 21635, "mac_number": "713701181478972", "device_id": 3, "timestamp": "2024-07-24 18:03:05"}
    ]

    # timestampをdatetimeオブジェクトに変換(test_data用なので本番では削除)
    for record in data_list:
        record['timestamp'] = parser.parse(record['timestamp'])

    start = 1 # start_point(device_id)
    end = 2   # end_point(device_id)
    print("Start Point:", start)
    print("End Point:", end)

    start_record = max(
        (record for record in data_list if record["device_id"] == start),
        key=lambda x: x["timestamp"],
        default=None
    )

    end_record = min(
        (record for record in data_list if record["device_id"] == end),
        key=lambda x: x["timestamp"],
        default=None
    )

    print("Start Record:", start_record)
    print("End Record:", end_record)

    # 秒単位で計算
    if start_record and end_record:
        diff_time = int((start_record['timestamp'] - end_record['timestamp']).total_seconds())
        print("Time Difference in seconds:", diff_time)
        print('--------------------------------------------------------------------------- ')
    else:
        print("One or both records are missing, cannot calculate time difference.")
        print('--------------------------------------------------------------------------- ')

    return start_record, end_record, diff_time if 'diff_time' in locals() else None
