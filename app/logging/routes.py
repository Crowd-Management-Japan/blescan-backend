from flask import Blueprint, request
import logging
from config import Config
import os
from werkzeug.utils import secure_filename
from datetime import datetime

log_bp = Blueprint('log', __name__)

@log_bp.route('upload_<int:id>', methods=['POST'])
def upload_logfile(id):
    logging.debug(f"file uploaded by {id}")

    folder = Config.RASPI_LOG_FOLDER
    name = "log"
    file = request.files.get(name, None)

    if not file:
        return "no file uploaded", 400
    else:
        filename = secure_filename(file.filename)
        now = datetime.now()
        filename = f"log_{now.year:02}{now.month:02}{now.day:02}_{now.hour:02}{now.minute:02}{now.second:02}.txt"
        folder = os.path.join(folder, f"{id}")
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        file.save(os.path.join(folder, filename))

        logging.debug(f"file saved as {filename}")

        return "ok"
    