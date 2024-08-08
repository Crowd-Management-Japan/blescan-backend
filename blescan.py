import logging
import multiprocessing as mp
import time

import click
from flask import Flask, render_template, request, flash, url_for, redirect
from flask.cli import with_appcontext
from flask_login import LoginManager, login_user, logout_user
from flask_login import login_required
from flask_migrate import Migrate
from werkzeug.security import check_password_hash, generate_password_hash

import app.config as backConf
from config import Config
# from app.cloud.routes import cloud_bp
from app.config.routes import config_bp
from app.database.database import init_db, db
from app.database.models import User
from app.database.routes import db_bp
from app.presentation.routes import presentation_bp
from app.setup.routes import setup_bp
from app.status.routes import status_bp
from app.template_filters import setup_template_filters
from app.transit.routes import transit_bp
from app.transit.transit_config import TransitConfig
from app.transit.transit_time import calculate_travel_time, calculate_transit

logging.basicConfig(level=logging.DEBUG,
                    format=('%(levelname)s %(filename)s: %(lineno)d:\t%(message)s'))

backConf.init_config()

app = Flask('blescan', template_folder='app/templates', static_folder='app/static')
app.secret_key = 'no_secret_key' # change with yours although this is a low level security setting
app.logger.setLevel('DEBUG')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {'timeout': 30, 'check_same_thread': False},
    'pool_pre_ping': True
}
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a secure secret key

migrate = Migrate(app, db)

init_db(app)
setup_template_filters(app)

with app.app_context():
    db.create_all()

login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Set the login view

@app.route('/')
@app.route('/home')
def home():
    return render_template('index.html', data={'name':'To'})
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

app.register_blueprint(setup_bp, url_prefix='/setup')
app.register_blueprint(status_bp, url_prefix='/status')
app.register_blueprint(transit_bp, url_prefix='/status/update')
app.register_blueprint(presentation_bp, url_prefix='/data')
app.register_blueprint(db_bp, url_prefix='/database')
app.register_blueprint(config_bp, url_prefix='/config')
# app.register_blueprint(cloud_bp, url_prefix='/cloud')

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

def calculate_transit_periodically():
    while True:
        combinations = TransitConfig.combinations
        combinations = [[1,2]]
        if combinations:
            # calculate_travel_time(combinations)
            calculate_transit(combinations)
        time.sleep(TransitConfig.INTERVAL_SEC)

if __name__ == "__main__":
    # start backend process(calclate transit)
    process = mp.Process(target=calculate_transit_periodically)
    process.start()

    # main process (flask)
    app.run(debug=True, use_reloader=False, host=Config.HOSTNAME, port=Config.PORT)
