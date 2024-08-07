from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from . import config_generation
import json
from jsonschema import validate, ValidationError
import logging
from flask_login import login_required

from ..util import compact_int_list_string
import app.util as util
from config import Config

from transit.transit_config import TransitConfig

setup_bp = Blueprint('setup', __name__)

_generator = config_generation.ConfigGenerator()

transit_data_store = {
    'delta': 1,
    'combinations': []
}

with open('app/setup/schemas.json', 'r') as schemas_file:
    _schemas = json.load(schemas_file)

##########################################
#
#   Data endpoints
#   v   v   v   v
##########################################

@setup_bp.route('/', methods=['POST'])
@login_required
def set_config_data():
    print("received post request")
    print(request.get_data())
    data = request.get_json()

    try:
        validate(data, _schemas.get('full_settings'))

    except ValidationError as e:
        print("Error validating data")
        print(e)
        return "Invalid format", 400
    print(data)

    TransitConfig.combinations = data['transit'].get('combinations', [])

    _generator.reset()
    _generator.set_config(data)
    _generator.generate()

    return redirect('/setup/status')

@setup_bp.route('/completed_<int:id>', methods=['POST'])
def setup_completed_callback(id: int):
    _generator.set_status_ok(id)
    return "updated"

@setup_bp.route('/last_updated/<int:id>')
def last_changed(id: int):
    return jsonify(last_changed = _generator.last_updated(id))

@setup_bp.route('/current')
def get_current_config():
    return _generator.get_config()

@setup_bp.route('/config_<int:id>')
def get_config(id: int):
    id = int(id)
    return _generator.get_config_for_id(id)

##########################################
#
#   Template render endpoints
#   v   v   v   v   v   v   v
##########################################

@setup_bp.route('/')
@login_required
def setup():
    last_config = _generator.get_config()
    # format data for template
    last_config['ids'] = compact_int_list_string(last_config['ids'])
    last_config['zigbee']['internet'] = compact_int_list_string(last_config['zigbee']['internet'])

    last_config['locations'] = util.location_dict_to_string(last_config['locations'])
    last_config['transit']['combinations'] = util.combination_array_to_string(last_config['transit']['combinations'])

    return render_template('setup/settings.html', config=last_config)

@setup_bp.route('/status', methods=['GET'])
def status_page():
    data = {}

    items = [{'id': did, 'status': dstatus} for did, dstatus in _generator.get_device_status_all().items()]
    data['data'] = items

    print(f"status: {items}")

    return render_template('setup/setup_status.html', data=data)

@setup_bp.route('/status_item_table', methods=['GET'])
def get_item_table():

    items = [{'id': did, 'status': dstatus} for did, dstatus in _generator.get_device_status_all().items()]
    print(f"status: {items}")
    data= {'data':items}
    return render_template('setup/setup_item_table.html', data=data)

@setup_bp.route('/install_<int:id>')
def get_installation_script(id: int):
    if type(id) != int:
        return "id must be integer", 400

    filename = "res/install_script.txt"
    with open(filename) as file:
        text = file.read()
        text = text.replace("$DEVICE_ID", str(id))
        text = text.replace("$SERVER_URL", f"{Config.SERVER_IP}:{Config.PORT}")

        return text

@setup_bp.route('/install_ip')
def get_installation_script_via_ip():
    """
    Returns the correct installation script based on the request id.
    Since the raspberry pi's in the tokyo lab use the last 2 digits as id, we can use it for making a single command installation.
    """
    ip = request.remote_addr
    id = int(ip[-2:])
    logging.debug("getting install script for request of ip %s -> ip: %d", ip, id)
    return get_installation_script(id)