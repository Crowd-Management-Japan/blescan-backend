from flask import Blueprint, request, jsonify, render_template, redirect, url_for
import json
from jsonschema import validate, ValidationError
import logging
from ..data import DataReceiver
import sqlalchemy

import datetime
from app.database.models import CountEntry
from app.database.database import db

db_bp = Blueprint('database', __name__)

# I know this is not safe at all, but since this backend will never be a 'public' one
# and will not contain series data, we use this solution.
# It is just to prevent accidentally deleting data
PASSWORD = "admin"

@db_bp.route('/delete', methods=['POST'])
def reset_database():
    """
    Use with care.
    This method will detele all entries in the entire database.
    """
    logging.debug(request.get_data())
    data = request.get_json(force=True)
    if not data:
        logging.debug("no body")
        data = {}
    logging.debug(data)
    if data.get('password', '') == PASSWORD:

        db.drop_all()
        db.create_all()

        return "deleted data", 200
    


    return "forbidden", 403