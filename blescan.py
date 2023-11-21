import logging
logging.basicConfig(level=logging.DEBUG, 
                    format=('%(levelname)s %(filename)s: %(lineno)d:\t%(message)s'))
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from app.setup.routes import setup_bp
from app.status.routes import status_bp
from app.presentation.routes import presentation_bp
import babel.dates as bdates
from datetime import datetime

from app.database.database import init_db, db

app = Flask('blescan', template_folder='app/templates', static_folder='app/static')
app.logger.setLevel('DEBUG')


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

init_db(app)

with app.app_context():
    db.create_all()
    logging.debug(db.get_engine().url)

@app.route('/')
def index():
    return render_template('index.html', data={'name':'To'})


app.register_blueprint(setup_bp, url_prefix='/setup')
app.register_blueprint(status_bp, url_prefix='/status')
app.register_blueprint(presentation_bp, url_prefix='/data')

@app.template_filter()
def format_datetime(value, format='medium'):
    if value < datetime(2000, 1, 1):
        return "-"
    if format == 'full':
        format="EEEE, d. MMMM y 'at' HH:mm"
    elif format == 'medium':
        format="EE dd.MM.y HH:mm"
    elif format == 'delta':
        return bdates.format_timedelta(datetime.now() - value, locale='en')
    
    return bdates.format_datetime(value, format, locale='en')

if __name__ == "__main__":
    app.run(debug=True, host='192.168.1.100', port=5000)