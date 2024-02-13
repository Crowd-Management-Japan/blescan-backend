from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

import app.database.models as models
import numpy as np
import pandas as pd
import datetime
import logging
from typing import List, Dict, Any
from flask import jsonify

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

def get_graph_data(limit: int = None, date_format: str = "%Y-%m-%d %H:%M:%S") -> List[Dict[str, Any]]:
    CountEntry = models.CountEntry

    query = db.session.query(CountEntry).order_by(CountEntry.timestamp.desc());

    if limit:
        limit = max(1, limit)
        subquery = db.session.query(CountEntry.timestamp).distinct(CountEntry.timestamp).order_by(CountEntry.timestamp.desc()).limit(1).offset(limit - 1)
        first = subquery.first()
        if len(first) > 0:
            first_ts = first[0]
            query = query.filter(CountEntry.timestamp >= first_ts)

    df = pd.read_sql(query.statement, db.engine)

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    result = pd.DataFrame()

    grouped = df.groupby('timestamp')

    result['device_count'] = grouped['id'].count()

    rolling = df.set_index('timestamp').groupby('id')['count'].rolling(window='5min').mean()
    result['rolling_avg_sum'] = rolling.reset_index().groupby('timestamp').sum()['count']
    result.reset_index(inplace=True)
    result['timestamp'] = result['timestamp'].map(lambda date: date.strftime(date_format))

    json = result.to_json(orient='records')
    return json

    