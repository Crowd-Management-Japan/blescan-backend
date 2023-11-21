from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

import app.database.models as models
import numpy as np
import pandas as pd

import logging

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)



def get_time_dataframe():
    CountEntry = models.CountEntry
    
    devices = db.session.query(CountEntry.timestamp, func.avg(CountEntry.count), func.count(CountEntry.id)).group_by(CountEntry.timestamp).all()

    dtypes=[('timestamp', 'M8[us]'), ('count_avg', 'float'), ('dev_count', 'i4')]
    devices = np.array([(np.datetime64(d), avg, c) for (d,avg,c) in devices], dtype=dtypes)

    logging.debug(len(devices))

    df = pd.DataFrame(devices)

    return df