from flask import Blueprint, request, jsonify, render_template, redirect, url_for
import json
from jsonschema import validate, ValidationError
import logging
from app.data import DataReceiver

from ..util import compact_int_list_string

presentation_bp = Blueprint('presentation', __name__)
_data = DataReceiver.get_instance()

@presentation_bp.route('/latest')
def get_presentation():
    data = {'total': _data.get_total_count()}
    return render_template('presentation/presentation.html', data=data)

@presentation_bp.route('/data_table', methods=['GET'])
def get_data_table():
    data = {'data': _data.get_data_online_first()}
    return render_template('presentation/data_table.html', data=data)