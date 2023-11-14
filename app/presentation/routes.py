from flask import Blueprint, request, jsonify, render_template, redirect, url_for
import json
from jsonschema import validate, ValidationError
import logging

from ..util import compact_int_list_string

presentation_bp = Blueprint('presentation', __name__)

@presentation_bp.route('/')
def get_presentation():
    return "hello"