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

@status_bp.route('/status_last_updated_table')
def get_status_table():
    data = {}
    return render_template('status/data_table.html', data=data)