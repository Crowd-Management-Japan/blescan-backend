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

def get_graph_data(before_date: datetime.datetime = None, after_date:datetime.datetime = None, limit: int = None) -> List[Dict[str, Any]]:
    CountEntry = models.CountEntry

    query = db.session.query(CountEntry.id, CountEntry.timestamp, CountEntry.count).order_by(CountEntry.timestamp.desc());

    if before_date:
        query = query.filter(CountEntry.timestamp < before_date)
    if after_date:
        query = query.filter(CountEntry.timestamp > after_date)
    if limit:
        query = query.limit(limit)

    df = pd.read_sql(query.statement, db.engine)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    windowed = df.groupby('id').apply(lambda x: x.set_index('timestamp').rolling('5min')['count'].mean())

    result = windowed.sum(axis=0).reset_index()

    result.columns = ['timestamp', 'rolling_mean']

    json = result.to_json(orient='records')
    return json

    