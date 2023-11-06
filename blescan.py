from flask import Flask

from app.setup.routes import setup_bp

app = Flask(__name__)


@app.route('/')
def index():
    return "Hello World"


app.register_blueprint(setup_bp, url_prefix='/setup')

if __name__ == "__main__":
    app.run(debug=True, host='192.168.1.100', port=5000)