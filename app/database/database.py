import datetime
import logging
from typing import List, Dict, Any

import pandas as pd
import pytz
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

import app.database.models as models

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)

def get_time_dataframe(request, DATE_FILTER_FORMAT):
    CountEntry = models.CountEntry

    query = db.session.query(CountEntry.timestamp, func.avg(CountEntry.count), func.count(CountEntry.id)).group_by(CountEntry.timestamp).order_by(CountEntry.timestamp.desc())

    date_format = request.args.get('format')
    if not date_format:
        date_format = DATE_FILTER_FORMAT

    before = request.args.get('before')
    if before:
        before = datetime.datetime.strptime(before, date_format)
        logging.debug("filtering before: %s", before)
        query = query.filter(CountEntry.timestamp < before)

    after = request.args.get('after')
    if after:
        after = datetime.datetime.strptime(after, date_format)
        logging.debug("filtering after: %s", after)
        query = query.filter(CountEntry.timestamp > after)

    limit = request.args.get('limit')
    if limit:
        try:
            query = query.limit(int(limit))
        except:
            pass

    devices = query.all()

    return [{
        'timestamp': device[0].strftime(date_format),
        'count_avg': device[1],
        'dev_count': device[2]
    } for device in devices]

def get_graph_data(limit: int = None, id_from: int = None, id_to: int = None, date_format: str = "%Y-%m-%d %H:%M:%S") -> List[Dict[str, Any]]:
    CountEntry = models.CountEntry
    jst = pytz.timezone('Asia/Tokyo')

    query = db.session.query(CountEntry).order_by(CountEntry.timestamp.desc());
    past_dt = datetime.datetime.now(jst) - datetime.timedelta(seconds=30)

    if limit:
        limit = max(1, limit)
        subquery = db.session.query(CountEntry.timestamp).distinct(CountEntry.timestamp).order_by(CountEntry.timestamp.desc()).limit(1).offset(limit - 1)
        first = subquery.first()
        if len(first) > 0:
            first_ts = first[0]
            query = query.filter(CountEntry.timestamp >= first_ts)
            query = query.filter(CountEntry.timestamp < past_dt)

    df = pd.read_sql(query.statement, db.engine)
    df = df[df['id'].isin(list(range(id_from, id_to + 1)))]

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    result = pd.DataFrame()

    grouped = df.groupby('timestamp')

    result['device_count'] = grouped['id'].count()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    rolling = df.set_index('timestamp').groupby('id')['tot_all'].apply(lambda x: x.ewm(span=60, adjust=False).mean())

    result['rolling_avg_sum'] = rolling.reset_index().groupby('timestamp').sum()['tot_all']
    result.reset_index(inplace=True)
    result['timestamp'] = result['timestamp'].map(lambda date: date.strftime(date_format))

    json = result.to_json(orient='records')
    return json
