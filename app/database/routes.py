from flask import Blueprint, request, jsonify, render_template, make_response
import logging
from sqlalchemy import func
import app.util as util
import pandas as pd
import datetime
from app.database.models import CountEntry
from app.database.database import db
import app.database.database as dbFunc

database_bp = Blueprint('database', __name__)

# I know this is not safe at all, but since this backend will never be a 'public' one
# and will not contain series data, we use this solution.
# It is just to prevent accidentally deleting data
PASSWORD = "admin"

DATE_FILTER_FORMAT = "%Y-%m-%d %H:%M:%S"

@database_bp.route('/delete', methods=['POST'])
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

@database_bp.route('/data')
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
    limit_val = 1
    if limit:
        try:
            limit_val = max(1, int(limit))
        except ValueError:
            logging.warning("invalid limit value. Ignoring")
            limit_val = 1

    id_from = request.args.get('id-from', None)
    id_from_val = 1
    if id_from:
        try:
            id_from_val = max(1, int(id_from))
        except ValueError:
            logging.warning("invalid ID from value. Ignoring")
            id_from_val = 1

    id_to = request.args.get('id-to', None)
    id_to_val = 1
    if id_to:
        try:
            id_to_val = max(1, int(id_to))
        except ValueError:
            logging.warning("invalid ID to value. Ignoring")
            id_to_val = 100

    return dbFunc.get_graph_data(limit_val, id_from_val, id_to_val, date_format)


@database_bp.route('/data/dates')
def get_end_dates():
    query = db.session.query(func.min(CountEntry.timestamp), func.max(CountEntry.timestamp)).all()

    first = query[0][0] or datetime.datetime.now()
    last = query[0][1] or datetime.datetime.now()

    return jsonify({'first': first.strftime(DATE_FILTER_FORMAT), 'last': last.strftime(DATE_FILTER_FORMAT)})


@database_bp.route('/export_data', methods=['GET'])
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
    query = CountEntry.query.order_by(CountEntry.timestamp.desc())

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

    query = query.order_by(None).order_by(CountEntry.timestamp.asc())

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

@database_bp.route('export', methods=['GET'])
def get_export_page():
    return render_template('database/export.html')