from flask import Blueprint, request, render_template
import json
from jsonschema import validate, ValidationError
import logging
import app.util as util
from flask_login import login_required

from app.config import Configs

config_bp = Blueprint('config', __name__)

#################
#
# Template Endpoints
# v  v  v  v  v  v
# 
################


@login_required
@config_bp.route('/')
def index():
    logging.debug(f"live: {Configs.CloudConfig}: {Configs.CloudConfig.DEVICE_FILTER}")

    return render_template('config/main_page.html')