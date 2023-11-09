from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from . import config_generation
import json
from jsonschema import validate, ValidationError

setup_bp = Blueprint('setup', __name__)

_generator = config_generation.ConfigGenerator()

with open('app/setup/schemas.json', 'r') as schemas_file:
    _schemas = json.load(schemas_file)

@setup_bp.route('/')
def setup():
    return render_template('settings.html')

@setup_bp.route('/', methods=['POST'])
def set_config_data():
    print("received post request")
    print(request.get_data())
    data = request.get_json()

    try:
        validate(data, _schemas.get('full_settings'))
        validate(data['internet'], _schemas.get('internet'))
        validate(data['zigbee'], _schemas.get('zigbee'))
    except ValidationError as e:
        print("Error validating data")
        print(e)
        return "Invalid format", 400
    print(data)

    zigbee = data['zigbee']
    internet = data['internet']

    _generator.reset()
    _generator.set_ids(data['ids'])
    _generator.set_internet_data(internet)
    _generator.set_zigbee_config(zigbee)

    _generator.generate()

    return redirect('/setup/status')

@setup_bp.route('/completed_<int:id>')
def setup_completed_callback(id: int):
    _generator.set_status_ok(id)
    return "updated"

@setup_bp.route('/status', methods=['GET'])
def status_page():
    data = {}

    items = [{'id': did, 'status': dstatus} for did, dstatus in _generator.get_device_status_all().items()]
    data['data'] = items

    print(f"status: {items}")

    return render_template('setup_status.html', data=data)

@setup_bp.route('/status_item_table', methods=['GET'])
def get_item_table():

    items = [{'id': did, 'status': dstatus} for did, dstatus in _generator.get_device_status_all().items()]
    print(f"status: {items}")
    data= {'data':items}
    return render_template('setup_item_table.html', data=data)

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
        text = text.replace("$DEVICE_ID", str(id))

        return text