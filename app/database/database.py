from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

import logging

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
