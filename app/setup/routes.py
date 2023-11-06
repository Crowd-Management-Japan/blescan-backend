from flask import Blueprint, request

setup_bp = Blueprint('setup', __name__)


@setup_bp.route('/')
def setup():
    return "hallo"

@setup_bp.route('/config_<id>')
def get_config(id: int):
    return f"config {id}"