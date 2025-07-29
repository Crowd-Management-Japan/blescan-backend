import datetime
import json
import logging
from flask import Blueprint, request
from jsonschema import validate, ValidationError
from app.database.models import CountEntry
from app.database.database import db
from ..data import DataReceiver
import app.util as util

count_bp = Blueprint('count', __name__)

_dataReceiver = DataReceiver.get_instance()

with open('app/count/schemas.json', 'r') as schemas_file:
    _schemas = json.load(schemas_file)

@count_bp.route('update', methods= ['GET'])
def get_count():
    return "ok", 200

@count_bp.route('/update', methods = ['POST'])
def update_count():
    data = request.get_json()
    #logging.debug("count post request from %d (ip: %s)", data['id'], request.remote_addr)

    try:
        validate(data, _schemas.get('countentry'))
        data['timestamp'] = datetime.datetime.strptime(data.get('timestamp', ''), '%Y-%m-%d %H:%M:%S')
        data['latitude'] = util.float_or_None(data.get('latitude', None))
        data['longitude'] = util.float_or_None(data.get('longitude', None))

    except ValidationError as e:
        logging.error("Validation error validating update")
        logging.error(e)
        return "Validation error", 400
    except ValueError:
        logging.error("Validation error when parsing date")
        return "Validation error - check date format %Y-%m-%d %H:%M:%S", 400

    entry = CountEntry.of_dict(data)
    existingEntry = db.session.query(CountEntry).filter_by(id=entry.id, timestamp=entry.timestamp).first()
    if not existingEntry:
        db.session.add(entry)
        db.session.commit()
        _dataReceiver.set_data(data)
    return "ok", 200