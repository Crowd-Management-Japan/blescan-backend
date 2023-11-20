from flask import Blueprint, request, jsonify, render_template, redirect, url_for
import json
from jsonschema import validate, ValidationError
import logging
from ..data import DataReceiver

status_bp = Blueprint('status', __name__)

_dataReceiver = DataReceiver.get_instance()

@status_bp.route('/')
def getStatus():
    data = {}
    return render_template('status/status.html')

@status_bp.route('update', methods= ['GET'])
def get_status():
    return "ok", 200

@status_bp.route('/update', methods = ['POST'])
def update_status():
    logging.debug("received post request")
    data = request.get_json()

    logging.debug(data)

    _dataReceiver.set_data(data)
    return "ok", 200

@status_bp.route('/status_last_updated_table')
def get_status_table():
    data = {'data': _dataReceiver.get_data_online_first()}
    return render_template('status/status_table.html', data=data)