from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response
import json
from jsonschema import validate, ValidationError
import logging
from ..data import DataReceiver
import sqlalchemy
from sqlalchemy import func
import app.util as util
import pandas as pd
from flask_login import login_required
import datetime

from app.config import Configs

config_bp = Blueprint('config', __name__)


with open('app/config/schemas.json', 'r') as schemas_file:
    _schemas = json.load(schemas_file)

#################
#
# Data Endpoints
# v  v  v  v  v  v
# 
################

@config_bp.route('/cloud/update', methods=['POST'])
def update_config():
    data = request.get_json()
    logging.debug(data)

    try:
        validate(data, _schemas.get('cloud_config'))
    except ValidationError as e:
        logging.debug("validation error: ")
        logging.debug(e)
        return "Invalid format", 400

    if data.get('device_filter', None):
        data['device_filter'] = util.compact_string_to_int_list(data['device_filter'])

    cfg = Configs.CloudConfig

    logging.debug("device_filter".upper())

    data = {k.upper(): v for k, v in data.items()}
    cfg._from_dict(data)
    cfg.save()


    return "OK", 200


#################
#
# Template Endpoints
# v  v  v  v  v  v
# 
################

@config_bp.route('/')
def index():
    logging.debug(f"live: {Configs.CloudConfig}: {Configs.CloudConfig.DEVICE_FILTER}")

    return render_template('config/main_page.html')

@config_bp.route('/cloud')
def cloud():
    cfg = Configs.CloudConfig
    data = {
        'is_enabled': cfg.IS_ENABLED,
        'current_filter': "no filter" if not cfg.DEVICE_FILTER else util.compact_int_list_string(cfg.DEVICE_FILTER)
    }
    return render_template('config/cloud.html', data=data)