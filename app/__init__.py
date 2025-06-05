import os
from sqlite3 import connect
from flask import Flask, jsonify
from config import Config
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_pymongo import PyMongo
from mongoengine import connect
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)
connect(
    db=os.getenv("DB_DATABASE"), 
    host=os.getenv("MONGO_URI")
)

mongo = PyMongo(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
CORS(app)


from app import routes
from app.routes.user_routes import users
from app.routes.auth_routes import auth

@app.route('/')
def index():
    return jsonify({
        "Message": "Awesome it works 🐻"
    })

app.register_blueprint(users, url_prefix='/api')
app.register_blueprint(auth, url_prefix = '/api/auth')