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

with open('app/status/schemas.json', 'r') as schemas_file:
    _schemas = json.load(schemas_file)

@transit_bp.route('transit', methods= ['GET'])
def get_transit():
    return "ok", 200

@transit_bp.route('/transit', methods = ['POST'])
def update_transit():
    return "ok", 200