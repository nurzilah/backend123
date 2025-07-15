from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os

# Import semua blueprint
from app.routes.auth_routes import auth
from app.routes.user_routes import users
from app.api.api import api
from app.routes.chart_routes import chart
from app.routes.scrape import scrape_bp
from app.api.detection_api import detection_api
from app.api.video_api import video_api

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
CORS(app)

# Konfigurasi
app.config['JWT_SECRET_KEY'] = 'rahasia-capstone-therapalsy'
app.config['MONGO_URI'] = os.getenv("MONGO_URI")

# Inisialisasi ekstensi
mongo = PyMongo(app)
jwt = JWTManager(app)

# Register semua blueprint
app.register_blueprint(auth, url_prefix='/api/auth')
app.register_blueprint(users, url_prefix='/api/user')
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(chart, url_prefix='/api/chart')
app.register_blueprint(scrape_bp, url_prefix='/api/scrape')
app.register_blueprint(detection_api, url_prefix='/api/detection')
app.register_blueprint(video_api, url_prefix='/api/video')




@app.route('/')
def index():
    return "API Running"

if __name__ == "__main__":
    app.run(debug=True)
