from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from app.model.user import User
from app.model.login_history import LoginHistory

users = Blueprint('users', __name__)

@users.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    # Gunakan default jika belum ada profile image
    image_path = user.profile_image if user.profile_image else "/static/uploads/pp.png"

    return jsonify({
        "username": user.username,
        "email": user.email,
        "profileImage": image_path,
        "last_login": user.updated_at.strftime("%b %d, %Y, %I:%M %p") if user.updated_at else ""
    }), 200


@users.route('/update', methods=['PATCH'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    data = request.get_json()
    username = data.get('username')
    email = data.get('email')

    if username:
        user.username = username
    if email:
        user.email = email

    user.updated_at = datetime.utcnow()
    user.save()

    return jsonify({'status': 'success', 'message': 'Profile updated'}), 200

@users.route('/upload', methods=['POST'])
@jwt_required()
def upload_photo():
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    file = request.files.get('file')
    if not file:
        return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join('static/uploads', filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    file.save(filepath)

    user.profile_image = f"/{filepath}"
    user.save()

    return jsonify({'status': 'success', 'message': 'Profile image updated', 'profile_image': user.profile_image}), 200

@users.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    user = User.objects(id=user_id).first()
    if not user:
        return jsonify({'status': 'error', 'message': 'User not found'}), 404

    data = request.json
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not check_password_hash(user.password, old_password):
        return jsonify({'status': 'error', 'message': 'Old password incorrect'}), 400

    hashed_new_password = generate_password_hash(new_password)
    user.password = hashed_new_password
    user.save()

    return jsonify({'status': 'success', 'message': 'Password updated'}), 200

@users.route('/history-login/<user_id>', methods=['GET'])
def get_login_history(user_id):
    history = LoginHistory.objects(user_id=user_id).order_by('-timestamp')
    return jsonify({
        'status': 'success',
        'data': [
            {
                'device': h.device,
                'timestamp': h.login_time.isoformat()  # ✅ ganti dari h.timestamp
            } for h in history
        ]
    })


