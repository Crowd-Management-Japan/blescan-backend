from flask import Blueprint, request, jsonify, render_template, redirect, url_for
import json
from jsonschema import validate, ValidationError
import logging
from ..data import DataReceiver
import sqlalchemy
import datetime
from app.database.models import CountEntry
from app.database.database import db
import app.util as util
# from app.cloud.cloud_service import cloud_service

transit_bp = Blueprint('transit', __name__)

_dataReceiver = DataReceiver.get_instance()

transit_data = None

with open('app/status/schemas.json', 'r') as schemas_file:
    _schemas = json.load(schemas_file)

@transit_bp.route('transit', methods= ['GET'])
def get_transit():
    global transit_data
    data = {
        "example_key": "example_value"
    }
    return render_template('presentation/transit_data.html', data=transit_data)

@transit_bp.route('/transit', methods = ['POST'])
def update_transit():
    global transit_data
    transit_data = request.get_json()
    # print(data)
    return render_template('presentation/transit_data.html', data=transit_data)