from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash
from pymongo import MongoClient
from werkzeug.security import check_password_hash
import jwt
from functools import wraps
from bson import ObjectId
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from app.model.user import User
from app.model.login_history import LoginHistory
from app.model.detection_result import DetectionResult
from app.routes.ml_routes import ml
from app.routes import generate_otp, send_otp_email


load_dotenv()  # Baca isi file .env

API_KEY = os.getenv('API_KEY')

main = Blueprint('main', __name__)
client = MongoClient('mongodb+srv://zilah:22090155@cluster0.nwenukm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['capstone']
user_model = User(db)
auth = Blueprint('auth', __name__, url_prefix='/auth')
SECRET_KEY = os.getenv('SECRET_KEY')

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/login-history/<user_id>', methods=['GET'])
def get_login_history(user_id):
    try:
        # Query login history berdasarkan user_id, urut dari terbaru
        histories = LoginHistory.query.filter_by(user_id=user_id).order_by(LoginHistory.login_time.desc()).all()

        # Ubah data ke dict/list yang bisa di-jsonify
        result = [h.to_dict() for h in histories]

        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api.route('/google-login', methods=['POST'])
def login_with_google():
    """
    Login pengguna dengan akun Google menggunakan ID token dari client.
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: google_token
        required: true
        schema:
          type: object
          properties:
            id_token:
              type: string
              description: ID token Google yang diperoleh dari client
          required:
            - id_token
    responses:
      200:
        description: Login berhasil, mengembalikan token JWT dan data pengguna
        schema:
          type: object
          properties:
            token:
              type: string
              description: JWT token untuk autentikasi
            user:
              type: object
              properties:
                username:
                  type: string
                email:
                  type: string
                id:
                  type: string
      400:
        description: Token tidak valid
      500:
        description: Kesalahan server
    """
    try:
        data = request.get_json()
        token = data.get('id_token')

        if not token:
            return jsonify({'error': 'Missing id_token'}), 400

        # Verifikasi token Google
        id_info = id_token.verify_oauth2_token(token, google_requests.Request())

        email = id_info.get('email')
        name = id_info.get('name') or email.split('@')[0]

        if not email:
            return jsonify({'error': 'Email tidak ditemukan dari token Google'}), 400

        user = db.users.find_one({'email': email})

        if not user:
            new_user = {
                'username': name,
                'email': email,
                'no_hp': None,
                'password': None,
                'created_at': datetime.utcnow(),
                'is_verified': True,
                'login_with_google': True
            }
            inserted = db.users.insert_one(new_user)
            user = db.users.find_one({'_id': inserted.inserted_id})

        payload = {
            'user_id': str(user['_id']),
            'exp': datetime.utcnow() + timedelta(days=1)
        }
        jwt_token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        return jsonify({
            'token': jwt_token,
            'user': {
                'id': str(user['_id']),
                'username': user.get('username'),
                'email': user.get('email'),
                'has_password': bool(user.get('password'))
            }
        })

    except ValueError:
        return jsonify({'error': 'Token Google tidak valid'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
api.register_blueprint(ml, url_prefix='/ml')

