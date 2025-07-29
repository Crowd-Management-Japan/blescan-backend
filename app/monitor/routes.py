from flask import Blueprint, request, jsonify, render_template, session
from app.database.models import TransitEntry, TemporaryTransitEntry
from datetime import datetime
from contextlib import contextmanager
from app.database.database import db
from app.data import DataReceiver
import pytz

@contextmanager
def session_scope():
    session = db.session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

monitor_bp = Blueprint('monitor', __name__)
_data = DataReceiver.get_instance()

@monitor_bp.route('/update_checkbox', methods=['POST'])
def update_checkbox():
    data = request.get_json()
    online_only = data.get('online_only', False)
    session['online_only'] = online_only
    return jsonify({"message": "Checkbox state updated", "online_only": online_only})

@monitor_bp.route('/count_latest')
def get_count_latest():
    return render_template('monitor/count_page.html')

@monitor_bp.route('/count_table', methods=['GET'])
def get_count_data():
    local_timezone = pytz.timezone('Asia/Tokyo')
    online_only = session.get('online_only', False)
    data = {'online_only': online_only, 'update_time': datetime.now(local_timezone).strftime("%Y-%m-%d %H:%M:%S"), 'data': _data.get_data_online_first()}
    return render_template('monitor/count_table.html', data=data)

@monitor_bp.route('/count_graph')
def get_count_graph():
    return render_template('monitor/count_graph.html')

@monitor_bp.route('/transit_latest')
def get_transit_latest():
    return render_template('monitor/transit_data_page.html')

@monitor_bp.route('/transit_data_table', methods=['GET'])
def get_transit_data():
    with session_scope() as session:
        data_newest = session.query(TemporaryTransitEntry).order_by(
            TemporaryTransitEntry.timestamp.desc()
        ).limit(30).all()
        data_oldest = session.query(TemporaryTransitEntry).order_by(
            TemporaryTransitEntry.timestamp.asc()
        ).limit(30).all()
        data_oldest.reverse()

        data_rows = [{'id': result.device_id, 'timestamp': result.timestamp, 'close_list': result.close_code} for result in data_newest]
        data_rows.append({'id': '...', 'timestamp': '...', 'close_list': '...'})
        data_rows.extend([{'id': result.device_id, 'timestamp': result.timestamp, 'close_list': result.close_code} for result in data_oldest])

    local_timezone = pytz.timezone('Asia/Tokyo')
    data = {'update_time': datetime.now(local_timezone).strftime("%Y-%m-%d %H:%M:%S"), 'data': data_rows}
    return render_template('monitor/transit_data_table.html', data=data)

@monitor_bp.route('/transit_events')
def get_transit_results():
    return render_template('monitor/transit_event_page.html')

@monitor_bp.route('/transit_event_table', methods=['GET'])
def get_transit_times():
    latest_data = TransitEntry.query.order_by(
        TransitEntry.timestamp.desc()
    ).limit(50).all()

    result = []
    for data in latest_data:
        result.append({
            'from': data.scanner_from,
            'to': data.scanner_to,
            'code': data.code,
            'start': data.time_start,
            'end': data.time_end,
            'travel_time': data.travel_time,
            'timestamp': data.timestamp
        })

    result = sorted(result, key=lambda x: x['timestamp'], reverse=True)

    local_timezone = pytz.timezone('Asia/Tokyo')
    data = {'update_time': datetime.now(local_timezone).strftime("%Y-%m-%d %H:%M:%S"), 'data': result}
        
    return render_template('monitor/transit_event_table.html', data=data)
