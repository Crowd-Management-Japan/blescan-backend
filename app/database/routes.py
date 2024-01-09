from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response
import json
from jsonschema import validate, ValidationError
import logging
from ..data import DataReceiver
import sqlalchemy
from sqlalchemy import func
import app.util as util
import pandas as pd
from flask_login import login_required
import datetime
from app.database.models import CountEntry
from app.database.database import db
import app.database.database as dbFunc

db_bp = Blueprint('database', __name__)

# I know this is not safe at all, but since this backend will never be a 'public' one
# and will not contain series data, we use this solution.
# It is just to prevent accidentally deleting data
PASSWORD = "admin"

DATE_FILTER_FORMAT = "%Y-%m-%d %H:%M:%S"

@db_bp.route('/delete', methods=['POST'])
def reset_database():
    """
    Use with care.
    This method will detele all entries in the entire database.
    """
    logging.debug(request.get_data())
    data = request.get_json(force=True)
    if not data:
        logging.debug("no body")
        data = {}
    logging.debug(data)
    if data.get('password', '') == PASSWORD:

        CountEntry.metadata.drop_all(db.engine)
        CountEntry.metadata.create_all(db.engine)

        return "deleted data", 200
    


    return "forbidden", 403

@db_bp.route('/data')
def get_data():

    date_format = request.args.get('format')
    if not date_format:
        date_format = DATE_FILTER_FORMAT


    before = request.args.get('before')
    if before:
        before = datetime.datetime.strptime(before, date_format)
        logging.debug("filtering before: %s", before)
        query = query.filter(CountEntry.timestamp < before)

    after = request.args.get('after')
    if after:
        after = datetime.datetime.strptime(after, date_format)
        logging.debug("filtering after: %s", after)
        query = query.filter(CountEntry.timestamp > after)

    limit = request.args.get('limit', None)

    return dbFunc.get_graph_data(before, after, limit, date_format)


    df = dbFunc.get_time_dataframe(request, DATE_FILTER_FORMAT)
    return jsonify(df)


@db_bp.route('/data/dates')
def get_end_dates():
    query = db.session.query(func.min(CountEntry.timestamp), func.max(CountEntry.timestamp)).all()

    first = query[0][0] or datetime.datetime.now()
    last = query[0][1] or datetime.datetime.now()

    return jsonify({'first': first.strftime(DATE_FILTER_FORMAT), 'last': last.strftime(DATE_FILTER_FORMAT)})



@db_bp.route('/export_data', methods=['GET'])
def get_filtered_data():
    """
    Get data of the database with possible filters.
    Query parameters are:
    id: a string list of IDs (41,42,44-50)
    before: a string timestamp of an excluding upper boundary of the timestamp
    after: a string timestamp of an excluding lower boundary of the timestamp
    format: a string defining the format of the upper two values. If none is given "%Y-%m-%d %H:%M:%S" is used
    type: either json or csv
    limit: a number limiting the amount of values
    """
    query = CountEntry.query

    ids = request.args.get('id')
    if ids:
        ids = util.compact_string_to_int_list(ids)
        logging.debug("Filtering for Ids: %s", ids)
        query = query.filter(CountEntry.id.in_(ids))

    date_format = request.args.get('format')
    if not date_format:
        date_format = DATE_FILTER_FORMAT

    logging.debug("Date format: %s", date_format)

    before = request.args.get('before')
    if before:
        before = datetime.datetime.strptime(before, date_format)
        logging.debug("filtering before: %s", before)
        query = query.filter(CountEntry.timestamp < before)

    after = request.args.get('after')
    if after:
        after = datetime.datetime.strptime(after, date_format)
        logging.debug("filtering after: %s", after)
        query = query.filter(CountEntry.timestamp > after)

    limit = request.args.get("limit")
    if limit:
        try:
            query = query.limit(int(limit))
        except:
            pass

    result = query.all()


    data = [res.to_dict() for res in result]
    

    if request.args.get('type') == 'csv':
        df = pd.DataFrame(data)
        logging.debug(df.head())
        csv = df.to_csv(index=False)
        output = make_response(csv)
        output.headers["Content-Disposition"] = "attachment; filename=export.csv"
        output.headers["Content-type"] = "text/csv"
        return output

    return jsonify(data)

@db_bp.route('export', methods=['GET'])
def get_export_page():
    return render_template('database/export.html')