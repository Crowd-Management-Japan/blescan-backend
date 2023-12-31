from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

import app.database.models as models
import numpy as np
import pandas as pd
import datetime
import logging

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