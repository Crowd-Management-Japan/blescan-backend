from flask import Blueprint, request, jsonify, render_template, redirect, url_for
import json
from jsonschema import validate, ValidationError
import logging
from ..data import DataReceiver
import sqlalchemy
import datetime
from app.database.models import CountEntry
from app.database.database import db
import app.util as util
from app.cloud.cloud_service import cloud_service

status_bp = Blueprint('status', __name__)

_dataReceiver = DataReceiver.get_instance()

with open('app/status/schemas.json', 'r') as schemas_file:
    _schemas = json.load(schemas_file)

@status_bp.route('update', methods= ['GET'])
def get_status():
    return "ok", 200

@status_bp.route('/update', methods = ['POST'])
def update_status():
    data = request.get_json()
    logging.debug("received post request from %d (ip: %s)", data['id'], request.remote_addr)

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
        cloud_service.send_to_cloud(data)
    return "ok", 200