from datetime import datetime, timedelta
from sqlalchemy import create_engine, Table, MetaData, select, and_, distinct, delete
from sqlalchemy.orm import sessionmaker

# データベース接続の設定
engine = create_engine('sqlite:///instance/database.db')
metadata = MetaData()

# テーブルの定義を読み込み
temporary_transit_data = Table('temporary_transit_data', metadata, autoload_with=engine)
transit_data = Table('transit_data', metadata, autoload_with=engine)

def search_time(route_pairs):
    # 処理の開始を表示
    print('--------------------------------------------------------------------------- ')
    print('Start searching transit time ')

    # 過去n分間のデータを探索する設定
    n = 150000
    transit_end = datetime.now()
    transit_start = transit_end - timedelta(minutes=n)
    print(f"探索終了時間: {transit_end}")
    print(f"探索開始時間: {transit_start}")

    # セッションの作成
    Session = sessionmaker(bind=engine)
    session = Session()

    for start_device_id, end_device_id in route_pairs:
        print("Start Point:", start_device_id)
        print("End Point:", end_device_id)

        # 特定の時間範囲内でユニークなMACアドレスを取得
        mac_query = (
            select(distinct(temporary_transit_data.c.mac_number))
            .where(temporary_transit_data.c.timestamp.between(transit_start, transit_end))
        )
        mac_list = [result[0] for result in session.execute(mac_query)]
        print("MACリスト：",mac_list)

        for mac in mac_list:
            last_end_timestamp = None
            continue_processing = True
            while continue_processing:
                # スタートデバイスの最前のレコードを取得
                start_record = session.execute(
                    select(temporary_transit_data)
                    .where(
                        and_(
                            temporary_transit_data.c.mac_number == mac,
                            temporary_transit_data.c.device_id == start_device_id,
                            temporary_transit_data.c.timestamp.between(transit_start, transit_end)
                        )
                    )
                    .order_by(temporary_transit_data.c.timestamp.asc())
                    .limit(1)
                ).fetchone()
                print(start_record)

                # エンドデバイスの最前のレコードを取得(前のループの一つ後を選択)
                end_condition = and_(
                    temporary_transit_data.c.mac_number == mac,
                    temporary_transit_data.c.device_id == end_device_id,
                    temporary_transit_data.c.timestamp.between(transit_start, transit_end)
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

                # 両レコードが存在する場合のみ処理
                if start_record and end_record:
                    # 時間差を計算
                    diff_time = (end_record.timestamp - start_record.timestamp).total_seconds()
                    print(diff_time)
                    if diff_time > 0:
                        # 正の時間差の場合、データベースに保存
                        new_record=transit_data.insert().values(
                            start=start_device_id,
                            end=end_device_id,
                            timestamp=transit_end,
                            transit_time=diff_time
                        )
                        result = session.execute(new_record)  # 実行してデータを挿入
                        session.commit()  # 変更をコミット
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
                        continue_processing = False
                    else:
                        # 負の時間差の場合、次のエンドレコードのtimestampを設定
                        last_end_timestamp = end_record.timestamp

    # すべての処理が完了したらセッションをコミットして閉じる
    session.commit()
    print('--------------------------------------------------------------------------- ')
    session.close()