import logging
logging.basicConfig(level=logging.DEBUG, 
                    format=('%(levelname)s %(filename)s: %(lineno)d:\t%(message)s'))
from flask import Flask, render_template
from app.setup.routes import setup_bp
from app.status.routes import status_bp
from app.presentation.routes import presentation_bp

app = Flask('blescan', template_folder='app/templates', static_folder='app/static')
app.logger.setLevel('DEBUG')

@app.route('/')
def index():
    return render_template('index.html', data={'name':'To'})


app.register_blueprint(setup_bp, url_prefix='/setup')
app.register_blueprint(status_bp, url_prefix='/status')
app.register_blueprint(presentation_bp, url_prefix='/data')


if __name__ == "__main__":
    app.run(debug=True, host='192.168.1.100', port=5000)