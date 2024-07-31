from datetime import datetime, timedelta
from sqlalchemy import create_engine, Table, MetaData, select, and_, or_, distinct, delete, exists
from sqlalchemy.orm import sessionmaker, aliased
from app.database.models import TemporaryTransitEntry

# データベース接続の設定
engine = create_engine('sqlite:///instance/database.db')
metadata = MetaData()

# テーブルの定義を読み込み
temporary_transit_data = Table('temporary_transit_data', metadata, autoload_with=engine)
transit_data = Table('transit_data', metadata, autoload_with=engine)

Current = aliased(TemporaryTransitEntry)
Next = aliased(TemporaryTransitEntry)

def search_time(combinations):
    # 処理の開始を表示
    print('--------------------------------------------------------------------------- ')
    print('Start searching transit time ')

    # 検索条件の設定
    # 過去n分間のデータを探索する設定
    max_exploration_time = 150000
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=max_exploration_time)
    print(f"探索終了時間: {end_time}")
    print(f"探索開始時間: {start_time}")

    print("ルート:", combinations)

    # セッションの作成
    Session = sessionmaker(bind=engine)
    session = Session()

    for start_device_id, end_device_id in combinations:
        print("Start Point:", start_device_id)
        print("End Point:", end_device_id)

        # 特定の時間範囲内でユニークなMACアドレスを取得
        unique_mac_query = (
            select(distinct(temporary_transit_data.c.mac_number))
            .where(temporary_transit_data.c.timestamp.between(start_time, end_time))
        )
        mac_list = [result[0] for result in session.execute(unique_mac_query)]
        print("MACリスト：", mac_list)

        for mac in mac_list:
            last_end_timestamp = None

            query = session.query(
                Current.mac_number,
                Current.timestamp.label('transit_start'),
                Next.timestamp.label('transit_end'),
                Current.device_id.label('from_device'),
                Next.device_id.label('to_device')
            ).join(
                Next,
                and_(
                    Current.mac_number == Next.mac_number,
                    Current.timestamp < Next.timestamp,
                    ~exists().where(
                        and_(
                            TemporaryTransitEntry.mac_number == Current.mac_number,
                            TemporaryTransitEntry.timestamp > Current.timestamp,
                            TemporaryTransitEntry.timestamp < Next.timestamp
                        )
                    )
                )
            ).filter(
                Current.mac_number == mac,
                Current.timestamp.between(start_time, end_time),
                Next.timestamp.between(start_time, end_time),
                or_(
                    and_(Current.device_id == start_device_id, Next.device_id == end_device_id),
                    and_(Current.device_id == end_device_id, Next.device_id == start_device_id)
                )
            ).order_by(
                Current.timestamp
            )

            transitions = query.all()

            new_records = [
                {
                    'start': transition.from_device,
                    'end': transition.to_device,
                    'timestamp': transition.transit_end,
                    'transit_time': (transition.transit_end - transition.transit_start).total_seconds()
                }
                for transition in transitions
            ]

            if new_records:
                session.execute(transit_data.insert(), new_records)  # 実行してデータを挿入
                session.commit()
                print("データがデータベースに保存されました。", len(new_records), "行が追加されました。")


            continue

            while True:
                # スタートデバイスの最前のレコードを取得
                start_record = session.execute(
                    select(temporary_transit_data)
                    .where(
                        and_(
                            temporary_transit_data.c.mac_number == mac,
                            temporary_transit_data.c.device_id == start_device_id,
                            temporary_transit_data.c.timestamp.between(start_time, end_time)
                        )
                    )
                    .order_by(temporary_transit_data.c.timestamp.asc())
                    .limit(1)
                ).fetchone()
                print(start_record)

                # リストの次のMACにスキップする
                if not start_record:
                    print(f"No records found for MAC {mac} at start device {start_device_id}.")
                    break

                # エンドデバイスの最前のレコードを取得(前のループの一つ後を選択)
                end_condition = and_(
                    temporary_transit_data.c.mac_number == mac,
                    temporary_transit_data.c.device_id == end_device_id,
                    temporary_transit_data.c.timestamp.between(start_time, end_time)
                )
                if last_end_timestamp:
                    end_condition = and_(end_condition, temporary_transit_data.c.timestamp > last_end_timestamp)

                end_record = session.execute(
                    select(temporary_transit_data)
                    .where(end_condition)
                    .order_by(temporary_transit_data.c.timestamp.asc())
                    .limit(1)
                ).fetchone()
                print(end_record)

                # リストの次のMACにスキップする
                if not end_record:
                    print(f"No more records found for MAC {mac} at end device {end_device_id}.")
                    break

                # 時間差を計算
                diff_time = (end_record.timestamp - start_record.timestamp).total_seconds()
                print(diff_time)
                if diff_time > 0:
                    # 正の時間差の場合、データベースに保存
                    new_record=transit_data.insert().values(
                        start=start_device_id,
                        end=end_device_id,
                        timestamp=end_time,
                        transit_time=diff_time
                    )
                    result = session.execute(new_record)  # 実行してデータを挿入
                    session.commit()
                    print("データがデータベースに保存されました。", result.rowcount, "行が追加されました。")

                    # スタートレコードより前のデータを削除
                    delete_query = delete(temporary_transit_data).where(
                        and_(
                            temporary_transit_data.c.mac_number == mac,
                            temporary_transit_data.c.device_id == start_device_id,
                            temporary_transit_data.c.timestamp < start_record.timestamp
                        )
                    )
                    session.execute(delete_query)
                    session.commit()
                    break
                else:
                    # 負の時間差の場合、次のエンドレコードのtimestampを設定
                    last_end_timestamp = end_record.timestamp

    # すべての処理が完了したらセッションをコミットして閉じる
    session.commit()
    print('--------------------------------------------------------------------------- ')
    session.close()