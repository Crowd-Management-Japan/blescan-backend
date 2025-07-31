import json
import os
from datetime import datetime
from jsonschema import validate, ValidationError
import logging
import app.util as util

from app.database.database import db
from app.database.models import TransitDetection
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required

transit_bp = Blueprint('transit', __name__)

def get_empty_config():
    return {
        'refresh_time': 20,
        'min_transit_time': 30,
        'max_transit_time': 15,
        'moving_avg': 15,
        'calculation_mode': 3,
        'storage_time': 60,
        'conbinations': []
    }

DEFAULT_CONFIG = get_empty_config()
CONFIG_PATH = 'res/last_transit_config.json'
MAX_LENGTH = 18 # maximum length for close_code (int is needed)

with open('app/transit/schemas.json', 'r') as schemas_file:
    _schemas = json.load(schemas_file)

@transit_bp.route('/', methods=['POST'])
@login_required
def set_config_data():
    logging.debug("received post request")
    logging.debug(request.get_data())
    data = request.get_json()

    try:
        validate(data, _schemas.get('full_settings'))
    except ValidationError as e:
        logging.debug("Error validating data")
        logging.debug(e)
        return jsonify({"error": "Invalid format"}), 400

    try:
        save_config(data)
    except Exception as e:
        logging.error(f"Failed to save config: {e}")
        return jsonify({"error": "Could not save configuration"}), 500

    return jsonify({"message": "Configuration saved"}), 200

@transit_bp.route('/update', methods=['POST'])
def update_transit():
    data = request.json
    #logging.debug("transit post request from %d (ip: %s)", data['id'], request.remote_addr)

    try:

        if not all(key in data for key in ['id', 'timestamp', 'close_ble_list']):
            return jsonify({"error": "Invalid data format"}), 400

        device_id = data['id']
        timestamp = datetime.fromisoformat(data['timestamp'])
        close_ble_list = data['close_ble_list']
        
        for code in close_ble_list:

            code = str(code)
            if len(code) > MAX_LENGTH:
                code = code[-MAX_LENGTH:]
            code = int(code)

            new_entry = TransitDetection(
                close_code = code,
                device_id = device_id,
                timestamp = timestamp  
            )
            db.session.add(new_entry)

        db.session.commit()

        return jsonify({"message": "Data successfully saved"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@transit_bp.route('/settings')
@login_required
def setup():
    last_config = load_config()
    last_config['combinations'] = util.combination_array_to_string(last_config['combinations'])

    return render_template('transit/settings.html', config=last_config)

def load_config():
    # load settings from transit config
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
    with open(CONFIG_PATH, 'r') as file:
        try:
            config = json.load(file)
            combinations = config.get('transit', {}).get('combinations', [])
            config['transit_combinations'] = combinations
        except (FileNotFoundError, json.JSONDecodeError):
            config['transit_combinations'] = []

    return config

def save_config(config):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)