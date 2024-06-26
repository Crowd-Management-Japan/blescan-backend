from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
import json
from jsonschema import validate, ValidationError
import logging
from datetime import datetime
import pytz
from app.data import DataReceiver
from ..util import compact_int_list_string

presentation_bp = Blueprint('presentation', __name__)
_data = DataReceiver.get_instance()

@presentation_bp.route('/latest')
def get_presentation():
    return render_template('presentation/presentation.html')


@presentation_bp.route('/graph')
def get_graph_page():
    return render_template('presentation/graph.html')

@presentation_bp.route('/update_checkbox', methods=['POST'])
def update_checkbox():
    data = request.get_json()
    online_only = data.get('online_only', False)
    session['online_only'] = online_only
    return jsonify({"message": "Checkbox state updated", "online_only": online_only})

@presentation_bp.route('/data_table', methods=['GET'])
def get_data_table():
    local_timezone = pytz.timezone('Asia/Tokyo')
    online_only = session.get('online_only', False)
    data = {'timestamp': datetime.now(local_timezone).strftime("%Y-%m-%d %H:%M:%S"), 'data': _data.get_data_online_first()}
    if online_only:
        return render_template('presentation/data_online.html', data=data)
    else:
        return render_template('presentation/data_table.html', data=data)