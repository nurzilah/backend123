from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from app.routes.auth_routes import auth
from app.routes.user_routes import users
from app.api import api 

app = Flask(__name__)
CORS(app)

# ✅ JWT Configuration
app.config['JWT_SECRET_KEY'] = 'rahasia-capstone-therapalsy'
jwt = JWTManager(app)

# ✅ Register blueprints
app.register_blueprint(auth, url_prefix='/api/auth')
app.register_blueprint(users, url_prefix='/api/user')
app.register_blueprint(api)


@app.route('/')
def index():
    return "API Running"
