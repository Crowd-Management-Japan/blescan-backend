from flask import Blueprint, request, jsonify, render_template, redirect, url_for
import json
from jsonschema import validate, ValidationError
import logging
from ..data import DataReceiver
import sqlalchemy
import datetime
from app.database.models import TemporaryTransitEntry
from app.database.database import db
from flask import make_response
import app.util as util
# from app.cloud.cloud_service import cloud_service

transit_bp = Blueprint('transit', __name__)

_dataReceiver = DataReceiver.get_instance()

transit_data = None

with open('app/status/schemas.json', 'r') as schemas_file:
    _schemas = json.load(schemas_file)

@transit_bp.route('transit', methods= ['GET'])
def get_transit():
    return "ok", 200

@transit_bp.route('/transit', methods = ['POST'])
def update_transit():
    transit_data = request.get_json()
    logging.debug("received post request from %d (ip: %s)", transit_data['id'], request.remote_addr)

    try:
        validate(transit_data, _schemas.get('TemporaryTransit'))
        transit_data['timestamp'] = datetime.datetime.strptime(transit_data.get('TIME', ''), '%Y-%m-%dT%H:%M:%S')

    except ValidationError as e:
        logging.error("Validation error validating update")
        logging.error(e)
        return "Validation error", 400
    except ValueError:
        logging.error("Validation error when parsing date")
        return "Validation error - check date format %Y-%m-%dT%H:%M:%S", 400

    temporary_transit_entry = TemporaryTransitEntry.of_dict(transit_data)
    existingEntry = db.session.query(TemporaryTransitEntry).filter_by(id=temporary_transit_entry.id, timestamp=temporary_transit_entry.timestamp).first()
    if not existingEntry:
        db.session.add(temporary_transit_entry)
        db.session.commit()
        # _dataReceiver.set_data(transit_data)
        # cloud_service.send_to_cloud(transit_data)
    return "ok", 200
