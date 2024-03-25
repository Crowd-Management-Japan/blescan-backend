from flask import Blueprint, request
import logging
from config import Config
import os
from werkzeug.utils import secure_filename

log_bp = Blueprint('log', __name__)

@log_bp.route('upload_<int:id>/<string:filename>', methods=['POST'])
def upload_logfile(id, filename):
    logging.debug(f"file {filename} uploaded by {id}")

    folder = Config.RASPI_LOG_FOLDER

    file = request.files.get(filename, None)

    if not file:
        return "no file uploaded", 400
    else:

        filename = secure_filename(file.filename)
        folder = os.path.join(folder, f"{id}")
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        file.save(os.path.join(folder, filename))

        return "ok"
    