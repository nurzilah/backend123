from flask import request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
import datetime, random, os, pytz
from app.model.user import User
from app.model.login_history import LoginHistory
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from dotenv import load_dotenv

load_dotenv()

def get_wib_time():
    return datetime.datetime.now(pytz.timezone("Asia/Jakarta"))

class AuthController:
    @staticmethod
    def register():
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not email or not password or not username:
            return jsonify({'message': 'Username, email, and password are required'}), 400

        if User.objects(email=email).first():
            return jsonify({'message': 'User already exists'}), 409

        hashed_password = generate_password_hash(password)
        otp = str(random.randint(1000, 9999))
        expiry = get_wib_time() + datetime.timedelta(minutes=10)

        User(
            username=username,
            email=email,
            password=hashed_password,
            created_at=get_wib_time(),
            otp=otp,
            otp_expiry=expiry,
            verified=False
        ).save()

        AuthController.send_otp_email(email, otp)
        return jsonify({'message': 'User registered. Check email for OTP.'}), 201

    @staticmethod
    def verify_otp():
        data = request.get_json()
        email = data.get('email')
        otp = data.get('otp')
        user = User.objects(email=email).first()

        if not user:
            return jsonify({'message': 'User not found'}), 404
        if user.verified:
            return jsonify({'message': 'User already verified'}), 400
        if user.otp != otp:
            return jsonify({'message': 'Invalid OTP'}), 400
        if get_wib_time() > user.otp_expiry:
            return jsonify({'message': 'OTP expired'}), 400

        user.update(verified=True, otp=None, otp_expiry=None)
        return jsonify({'message': 'Account verified successfully'}), 200

    @staticmethod
    def login():
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        device = data.get("device") or request.headers.get('User-Agent', 'Unknown Device')

        user = User.objects(email=email).first()

        if not user:
            return jsonify({'message': 'Invalid email or password'}), 401
        if not user.verified:
            return jsonify({'message': 'Account not verified'}), 403

        # ⛔️ Penting: cek jika password kosong
        if not user.password or user.password.strip() == "":
            return jsonify({'message': 'Akun ini tidak memiliki password. Silakan login dengan Google'}), 403

        if not check_password_hash(user.password, password):
            return jsonify({'message': 'Invalid email or password'}), 401

        now = get_wib_time()
        token = create_access_token(identity=str(user.id), expires_delta=datetime.timedelta(hours=1))
        user.update(updated_at=now)
        LoginHistory(user_id=str(user.id), device=device, login_time=now).save()

        return jsonify({
            'access_token': token,
            'data': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email
            },
            'message': 'Login successful'
        }), 200

    @staticmethod
    def google_login():
        data = request.get_json()
        token = data.get("token")
        device = data.get("device") or request.headers.get('User-Agent', 'Unknown Device')

        if not token:
            return jsonify({"message": "Token tidak ditemukan"}), 400

        try:
            client_id = os.getenv("GOOGLE_CLIENT_ID")
            info = id_token.verify_oauth2_token(token, google_requests.Request(), client_id)
            email = info["email"]
            username = info.get("name", email.split("@")[0])

            user = User.objects(email=email).first()
            if not user:
                user = User(
                    username=username,
                    email=email,
                    password="",
                    created_at=get_wib_time(),
                    verified=True
                ).save()

            now = get_wib_time()
            access_token = create_access_token(identity=str(user.id), expires_delta=datetime.timedelta(hours=1))
            user.update(updated_at=now)
            LoginHistory(user_id=str(user.id), device=device, login_time=now).save()

            return jsonify({
                "access_token": access_token,
                "data": {
                    "id": str(user.id),
                    "username": user.username,
                    "email": user.email
                },
                "message": "Login via Google berhasil"
            }), 200

        except ValueError:
            return jsonify({"message": "Token tidak valid"}), 400

    @staticmethod
    def send_otp_email(to_email, otp):
        from_email = os.getenv("MAIL_USERNAME")
        subject = "TheraPalsy Email Verification Code"
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"TheraPalsy <{from_email}>"
        msg["To"] = to_email

        text = f"Your OTP code is: {otp}\nThis code will expire in 10 minutes."
        html = f"""
        <html><body>
        <p><strong>TheraPalsy Verification</strong></p>
        <p>Your OTP code is: <strong>{otp}</strong></p>
        </body></html>"""

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(os.getenv("MAIL_SERVER"), int(os.getenv("MAIL_PORT"))) as server:
            server.starttls()
            server.login(from_email, os.getenv("MAIL_PASSWORD"))
            server.send_message(msg)
