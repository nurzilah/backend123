from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os

load_dotenv()
api = Blueprint('api', __name__, url_prefix='/api')

client = MongoClient(os.getenv('MONGO_URI'))
db = client['capstone']

@api.route('/google-login', methods=['POST'])
def login_with_google():
    try:
        data = request.get_json()
        token = data.get('id_token')
        if not token:
            return jsonify({'error': 'Missing id_token'}), 400

        id_info = id_token.verify_oauth2_token(token, google_requests.Request())

        email = id_info.get('email')
        name = id_info.get('name') or email.split('@')[0]

        if not email:
            return jsonify({'error': 'Email tidak ditemukan dari token Google'}), 400

        user = db.users.find_one({'email': email})

        if not user:
            user_data = {
                'username': name,
                'email': email,
                'password': None,
                'created_at': datetime.utcnow(),
                'is_verified': True,
                'login_with_google': True
            }
            inserted = db.users.insert_one(user_data)
            user = db.users.find_one({'_id': inserted.inserted_id})

        access_token = create_access_token(
            identity=str(user['_id']),
            expires_delta=timedelta(days=1)
        )

        return jsonify({
            'token': access_token,
            'user': {
                'id': str(user['_id']),
                'username': user['username'],
                'email': user['email'],
                'has_password': bool(user.get('password'))
            }
        }), 200

    except ValueError:
        return jsonify({'error': 'Token Google tidak valid'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500
