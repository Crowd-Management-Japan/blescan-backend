from flask import Blueprint, request, render_template
import json
from jsonschema import validate, ValidationError
import logging
import app.util as util
from flask_login import login_required

from app.config import Configs

cloud_bp = Blueprint('cloud', __name__)


with open('app/cloud/schemas.json', 'r') as schemas_file:
    _schemas = json.load(schemas_file)

#################
#
# Data Endpoints
# v  v  v  v  v  v
# 
################
@cloud_bp.route('/update_config', methods=['POST'])
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


@login_required
@cloud_bp.route('/config')
def cloud():
    cfg = Configs.CloudConfig
    data = {
        'is_enabled': cfg.IS_ENABLED,
        'current_filter': "no filter" if not cfg.DEVICE_FILTER else util.compact_int_list_string(cfg.DEVICE_FILTER)
    }
    return render_template('cloud/cloud_config.html', data=data)