from flask import request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import datetime, random, os, pytz
from app.model.user import User
from app.model.login_history import LoginHistory
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
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

        if not user or user.verified or user.otp != otp:
            return jsonify({'message': 'Invalid OTP or user'}), 400

        if get_wib_time() > user.otp_expiry.replace(tzinfo=pytz.utc):
            return jsonify({'message': 'OTP expired'}), 400

        user.update(verified=True, otp=None, otp_expiry=None)
        return jsonify({'message': 'Account verified successfully'}), 200

    @staticmethod
    def login():
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        device = data.get('device') or request.headers.get('User-Agent', 'Unknown')

        user = User.objects(email=email).first()

        if not user or not user.verified or not check_password_hash(user.password, password):
            return jsonify({'message': 'Invalid email/password or not verified'}), 401

        token = create_access_token(identity=str(user.id), expires_delta=datetime.timedelta(hours=1))
        user.update(updated_at=get_wib_time())
        LoginHistory(user_id=str(user.id), device=device, login_time=get_wib_time()).save()

        return jsonify({
            'access_token': token,
            'data': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email
            }
        }), 200

    @staticmethod
    def forgot_password():
        data = request.get_json()
        email = data.get("email")
        user = User.objects(email=email).first()

        if not user:
            return jsonify({"message": "Email not registered"}), 404

        otp = str(random.randint(1000, 9999))
        user.update(otp=otp, otp_expiry=get_wib_time() + datetime.timedelta(minutes=10))
        AuthController.send_otp_email(email, otp)

        return jsonify({"message": "OTP sent to email"}), 200

    @staticmethod
    def verify_reset_otp():
        data = request.get_json()
        email = data.get("email")
        otp = data.get("otp")
        user = User.objects(email=email).first()

        if not user or user.otp != otp:
            return jsonify({"message": "Invalid OTP"}), 400

        if get_wib_time() > user.otp_expiry.replace(tzinfo=pytz.utc):
            return jsonify({"message": "OTP expired"}), 400

        return jsonify({"message": "OTP valid"}), 200

    @staticmethod
    def reset_password():
        data = request.get_json()
        email = data.get("email")
        new_password = data.get("password")
        user = User.objects(email=email).first()

        if not user:
            return jsonify({"message": "User not found"}), 404

        user.update(
            password=generate_password_hash(new_password),
            otp=None,
            otp_expiry=None,
            updated_at=get_wib_time()
        )

        return jsonify({"message": "Password reset successful"}), 200

    @staticmethod
    def google_login():
        from flask import request, jsonify
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        import os

        data = request.get_json()
        token = data.get("token")
        device = data.get("device") or request.headers.get("User-Agent", "Unknown")

        client_id = os.getenv("GOOGLE_CLIENT_ID")
        print(f"[DEBUG] Token (start): {token[:30]}...")
        print(f"[DEBUG] Client ID: {client_id}")

        try:
            # 👇 Log ini akan memberitahu detail error
            info = id_token.verify_oauth2_token(token, google_requests.Request(), client_id)
            print(f"[DEBUG] Google token info: {info}")

            email = info.get("email")
            print(f"[DEBUG] Email from token: {email}")
            return jsonify({"message": "Login berhasil"}), 200

        except ValueError as e:
            print(f"[ERROR] Token tidak valid: {e}")
            return jsonify({"message": "Token tidak valid", "detail": str(e)}), 400

        except Exception as ex:
            print(f"[FATAL ERROR] {ex}")
            return jsonify({"message": "Server error", "detail": str(ex)}), 500


    @staticmethod
    def send_otp_email(to_email, otp):
        from_email = os.getenv("MAIL_USERNAME")
        password = os.getenv("MAIL_PASSWORD")
        subject = "TheraPalsy OTP"
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"TheraPalsy <{from_email}>"
        msg["To"] = to_email

        text = f"Your OTP code is: {otp}"
        html = f"<html><body><p><strong>Your OTP code is: {otp}</strong></p></body></html>"

        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))

        try:
            with smtplib.SMTP(os.getenv("MAIL_SERVER"), int(os.getenv("MAIL_PORT"))) as server:
                server.starttls()
                server.login(from_email, password)
                server.send_message(msg)
        except Exception as e:
            print(f"Gagal kirim email: {e}")
