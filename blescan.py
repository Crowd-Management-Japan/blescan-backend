from datetime import datetime
from logging.handlers import TimedRotatingFileHandler as BaseTimedRotatingFileHandler
import logging
import multiprocessing as mp
import os
import time

import click
import psutil
from flask import Flask, render_template, request, flash, url_for, redirect, jsonify
from flask.cli import with_appcontext
from flask_login import LoginManager, login_user, logout_user
from flask_login import login_required
from flask_migrate import Migrate
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config

from app.database.models import User
from app.database.database import init_db, db
from app.template_filters import setup_template_filters
from app.transit.transit_time import TransitCalculator

from app.database.routes import database_bp
from app.monitor.routes import monitor_bp
from app.scanner.routes import scanner_bp
from app.count.routes import count_bp
from app.transit.routes import transit_bp

app = Flask('blescan', template_folder='app/templates', static_folder='app/static')
app.secret_key = 'no_secret_key' # change with yours although this is a low level security setting

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {'timeout': 30, 'check_same_thread': False},
    'pool_pre_ping': True
}
app.config['SECRET_KEY'] = 'your_secret_key'  # change this to a secure secret key

migrate = Migrate(app, db)
CORS(app, resources={r"/database/*": {"origins": "*"}})

init_db(app)
setup_template_filters(app)

with app.app_context():
    db.create_all()

login_manager = LoginManager(app)
login_manager.login_view = 'login'  # set the login view

@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html', name='To')

@app.route('/metrics')
def metrics():
    cpu_usage = psutil.cpu_percent(interval=0.2)
    memory_usage = psutil.virtual_memory().percent
    return jsonify({
        'cpu_usage': cpu_usage,
        'memory_usage': memory_usage
    })

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        # import pdb; pdb.set_trace()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login failed. Check your username and password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

app.register_blueprint(count_bp, url_prefix='/count')
app.register_blueprint(transit_bp, url_prefix='/transit')
app.register_blueprint(monitor_bp, url_prefix='/monitor')
app.register_blueprint(scanner_bp, url_prefix='/scanner')
app.register_blueprint(database_bp, url_prefix='/database')

# create command function
@click.command(name='createadmin')
@with_appcontext
def create():
    new_user = User(
        username=input("enter username: "),
        password=generate_password_hash(input("enter password: "))
    )
    db.session.add(new_user)
    db.session.commit()
# add command function to cli commands
app.cli.add_command(create)

# create a custom logging handler to rotate logs daily
class TimedRotatingFileHandler(BaseTimedRotatingFileHandler):
    def __init__(self, log_dir, backupCount=30):
        os.makedirs(log_dir, exist_ok=True)
        filename = os.path.join(log_dir, "log.txt")
        super().__init__(
            filename=filename,
            when='midnight',
            interval=1,
            backupCount=backupCount,
            encoding='utf-8',
            utc=False
        )
        self.log_dir = log_dir
        self.suffix = "%Y-%m-%d"

    def doRollover(self):
        super().doRollover()

        # find the most recently rotated file using existing logic
        date_str = datetime.now().strftime(self.suffix)
        rotated_filename = self.baseFilename + "." + date_str

        if os.path.exists(rotated_filename):
            mmdd = datetime.now().strftime("%m%d")
            new_name = os.path.join(self.log_dir, f"log_{mmdd}.txt")
            try:
                os.rename(rotated_filename, new_name)
            except Exception as e:
                logging.debug(f"Failed to rename log file: {e}")

def setup_logger():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s")
    file_handler = TimedRotatingFileHandler(log_dir='logs', backupCount=30)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # disable werkzeug logging (set at false if you need verbose logging)
    logging.getLogger('werkzeug').disabled = True

def calculate_transit_periodically(self):
    transit_calculator = TransitCalculator(self)
    interval = 10
    while True:
        try:
            interval = transit_calculator.calculate_transit()
        except Exception as e:
            logging.error(f"Error calculating transit: {e}")
        try:
            transit_calculator.compute_avg_travel_times ()
        except Exception as e:
            logging.error(f"Error computing average travel times: {e}")
        
        time.sleep(interval)

if __name__ == "__main__":
    setup_logger()

    # start backend process (calclate transit)
    process = mp.Process(target=calculate_transit_periodically, args=('',))
    process.start()

    # main process (flask)
    app.run(debug=True, use_reloader=False, host=Config.HOSTNAME, port=Config.PORT)
