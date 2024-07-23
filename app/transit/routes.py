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

with open('app/transit/schemas.json', 'r') as schemas_file:
    _schemas = json.load(schemas_file)

@transit_bp.route('transit', methods= ['GET'])
def get_transit():
    return "ok", 200

@transit_bp.route('/transit', methods = ['POST'])
def update_transit():
    transit_data = request.get_json()
    logging.debug("received post request from %d (ip: %s)", transit_data['ID'], request.remote_addr)

    try:
        validate(transit_data, _schemas.get('TemporaryTransitEntry'))
        timestamp = datetime.datetime.strptime(transit_data.get('TIME', ''), '%Y-%m-%dT%H:%M:%S')

        # Add each MAC address to the database
        for mac in transit_data['MAC']:
            existingEntry = db.session.query(TemporaryTransitEntry).filter_by(
                device_id=transit_data['ID'],
                mac_number=str(mac),
                timestamp=timestamp
            ).first()
            if not existingEntry:
                new_entry = TemporaryTransitEntry(
                    device_id=transit_data['ID'],
                    mac_number=str(mac),
                    timestamp=timestamp
                )
                db.session.add(new_entry)
        
        db.session.commit()
        return jsonify({"message": "Data successfully saved"}), 200

    except ValidationError as e:
        logging.error("Validation error: %s", e)
        return jsonify({"error": "Validation error"}), 400
    except ValueError:
        logging.error("Date format error")
        return jsonify({"error": "Validation error - check date format %Y-%m-%dT%H:%M:%S"}), 400
    except Exception as e:
        logging.error("An error occurred: %s", str(e))
        db.session.rollback()
        return jsonify({"error": "An error occurred while processing your request"}), 500
