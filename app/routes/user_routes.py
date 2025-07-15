from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from app.model.user import User
from app.model.login_history import LoginHistory
from app.model.password_history import PasswordHistory
from app.model.detection_result import DetectionResult


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

    # ✅ Simpan riwayat ke koleksi password_history
    PasswordHistory(
        user_id=str(user.id),
        old_password=user.password,
        new_password=hashed_new_password
    ).save()

    # ✅ Update password user
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

@users.route('/password-history/<user_id>', methods=['GET'])
def get_password_history(user_id):
    history = PasswordHistory.objects(user_id=user_id).order_by('-changed_at')[:5]
    return jsonify({
        'status': 'success',
        'data': [
            {
                'changed_at': h.changed_at.isoformat()
                # Jangan tampilkan password hash di frontend demi keamanan
            } for h in history
        ]
    })

@users.route('/detection-history', methods=['GET'])
@jwt_required()
def get_detection_history():
    user_id = get_jwt_identity()
    detections = DetectionResult.objects(user_id=user_id).order_by('-detected_at')

    data = []
    for det in detections:
        data.append({
            "user_id": det.user_id,
            "result": det.result,  # langsung dictionary, no json.loads
            "detected_at": det.detected_at.isoformat()
        })

    return jsonify({"status": "success", "data": data}), 200

@users.route('/detect', methods=['POST'])
@jwt_required()
def detect_and_save():
    user_id = get_jwt_identity()

    # 1️⃣ Ambil file upload dari Flutter
    file = request.files.get('file')
    if not file:
        return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400

    # 2️⃣ Simpan file sementara
    filename = secure_filename(file.filename)
    upload_dir = os.path.join('static/uploads/detections')
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    # 3️⃣ Jalankan model ML
    try:
        prediction_result = run_model(filepath)  # ✅ panggil fungsi prediksi sesuai model ML kamu
    except Exception as e:
        print(f"[ERROR] Model prediction failed: {e}")
        return jsonify({'status': 'error', 'message': 'Model prediction failed'}), 500

    # 4️⃣ Simpan ke MongoDB
    detection = DetectionResult(
        user_id=user_id,
        input_data=[filename],   # bisa simpan nama file kalau mau
        result=prediction_result,
        detected_at=datetime.now(pytz.timezone("Asia/Jakarta"))
    )
    detection.save()

    return jsonify({
        "status": "success",
        "message": "Detection completed successfully",
        "data": prediction_result
    }), 200

@users.route('/delete-data', methods=['DELETE'])
@jwt_required()
def delete_user_data():
    current_user = get_jwt_identity()
    
    # Hapus semua riwayat deteksi & terapi user
    db.DetectionHistory.delete_many({"user_id": current_user})
    db.TherapyHistory.delete_many({"user_id": current_user})
    
    return jsonify({"message": "Data pengguna berhasil dihapus"}), 200

@users.route('/delete-account', methods=['DELETE'])
@jwt_required()
def delete_account():
    current_user = get_jwt_identity()
    
    # Hapus semua riwayat
    db.DetectionHistory.delete_many({"user_id": current_user})
    db.TherapyHistory.delete_many({"user_id": current_user})
    
    # Hapus user itu sendiri
    db.User.delete_one({"_id": current_user})
    
    return jsonify({"message": "Akun dan semua data berhasil dihapus"}), 200

