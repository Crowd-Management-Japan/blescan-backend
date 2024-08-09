import json
from datetime import datetime
from typing import Dict

from app.database.database import db
from app.database.models import TemporaryTransitEntry, TransitEntry
from flask import Blueprint, request, jsonify, render_template
from sqlalchemy import desc

transit_bp = Blueprint('transit', __name__)

def load_schema(schema_name: str) -> Dict:
    with open('app/transit/schemas.json', 'r') as schema_file:
        schemas = json.load(schema_file)
    return schemas.get(schema_name, {})

@transit_bp.route('/latest', methods=['GET'])
def get_transit():
    try:
        latest_data = TransitEntry.query.order_by(
            desc(TransitEntry.id)
        ).limit(50).all()

        result = []
        for data in latest_data:
            result.append({
                'from': data.start,
                'to': data.end,
                'arrival_time': data.timestamp,
                'aggregation_time': data.aggregation_time,
                'transit': data.transit_time
            })
        return render_template('presentation/transit_data.html', transit_data=result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@transit_bp.route('/update', methods=['POST'])
def update_transit():
    try:
        data = request.json

        if not all(key in data for key in ['ID', 'MAC', 'TIME']):
            return jsonify({"error": "Invalid data format"}), 400

        device_id =data['ID']
        mac_addr = data['MAC']
        timestamp = datetime.fromisoformat(data['TIME'])

        for mac in mac_addr:
            new_entry = TemporaryTransitEntry(
                mac_address = mac,
                device_id = device_id,
                timestamp = timestamp
            )
            db.session.add(new_entry)

        db.session.commit()

        return jsonify({"message": "Data successfully saved"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
