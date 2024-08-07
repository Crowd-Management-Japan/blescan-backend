from datetime import timedelta

class TransitConfig:
    # CONSTANT
    # 移動時間計算を行う間隔
    INTERVAL_SEC = 60
    # この時間未満の移動時間はノイズとして保存しない(エリアが隣接するとき、その境界を行き来する場合。または、別のエリアのMACアドレスが偶然一致した場合。)
    MIN_MOVEMENT_TIME = timedelta(seconds=0)
    # この時間以上同じMACの検出がなければ、移動したとみなす(MACが変わった場合や、エリアから出たが他のエリアに行かなかった場合)
    NO_DETECTION_THRESHOLD = timedelta(minutes=5)
    # この時間以上同じ場所に滞在していたら、移動後の時間とみなす(同じ場所に長時間滞在した場合)
    SAME_PLACE_THRESHOLD = timedelta(minutes=3)
    # 検索する時間の範囲
    TIME_WINDOW = timedelta(minutes=15)

    # variable
    combinations = []