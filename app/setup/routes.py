from flask import Blueprint, request, jsonify, render_template
from . import config_generation
import json
from jsonschema import validate

setup_bp = Blueprint('setup', __name__)

_generator = config_generation.ConfigGenerator()

with open('app/setup/schemas.json', 'r') as schemas_file:
    _schemas = json.load(schemas_file)

@setup_bp.route('/')
def setup():
    return "Hallo"

@setup_bp.route('/', methods=['POST'])
def set_config_data():
    data = request.get_json(force=True)

    zigbee = data['zigbee']
    internet = data['internet']
    counting = data['counting']
    beacon = data['beacon']

@setup_bp.route('/zigbee', methods=['POST'])
def define_zigbee():
    data = request.get_json()

    schema = _schemas.get('zigbee')

    validate(instance=data, schema=schema)

    print(data)

    _generator.set_zigbee_config(data)
    return "ok"

@setup_bp.route('/zigbee', methods=['GET'])
def get_zigbee_config():
    filename = 'res/zigbee_sample.txt'
    with open(filename) as file:
        data = json.load(file)
        return data

@setup_bp.route('/last_updated/<int:id>')
def last_changed(id: int):
    return jsonify(last_changed = _generator.last_updated(id))

@setup_bp.route('/config_<int:id>')
def get_config(id: int):
    id = int(id)
    return _generator.get_config_for_id(id)

@setup_bp.route('/install_<int:id>')
def get_installation_script(id: int):
    if type(id) != int:
        return "id must be integer", 400
    
    filename = "res/install_script.txt"
    with open(filename) as file:
        text = file.read()
        text = text.replace("$DEVICE_ID", id)

        return text