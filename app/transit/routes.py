import json
from datetime import datetime
from typing import Dict

from app.database.database import db
from app.database.models import TemporaryTransitEntry
from flask import Blueprint, request, jsonify

transit_bp = Blueprint('transit', __name__)

def load_schema(schema_name: str) -> Dict:
    with open('app/transit/schemas.json', 'r') as schema_file:
        schemas = json.load(schema_file)
    return schemas.get(schema_name, {})

@transit_bp.route('update', methods=['GET'])
def get_transit():
    return "ok", 200

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
        db.sessino.rollback()
        return jsonify({"error": str(e)}), 500
