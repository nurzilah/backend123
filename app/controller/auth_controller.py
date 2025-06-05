from flask import request, jsonify
from app import mongo, bcrypt
from flask_jwt_extended import create_access_token
import datetime
from app.model.user import User
import random
import smtplib
from email.mime.text import MIMEText
import os
from email.mime.multipart import MIMEMultipart
from google.oauth2 import id_token
from google.auth.transport import requests


class AuthController:
    @staticmethod
    def register():
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not email or not password or not username:
            return jsonify({'message': 'Username, email, and password are required'}), 400

        # Cek apakah email sudah terdaftar
        existing_user = User.objects(email=email).first()
        if existing_user:
            return jsonify({'message': 'User already exists'}), 409

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Generate OTP 4 angka
        otp = str(random.randint(1000, 9999))
        otp_expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)

        # Simpan user
        user = User(
            username=username,
            email=email,
            password=hashed_password,
            created_at=datetime.datetime.utcnow(),
            otp=otp,
            otp_expiry=otp_expiry,
            verified=False
        )
        user.save()

        # Kirim email OTP
        AuthController.send_otp_email(email, otp)

        return jsonify({'message': 'User registered. Please check your email for the OTP code.'}), 201

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

        if datetime.datetime.utcnow() > user.otp_expiry:
            return jsonify({'message': 'OTP expired'}), 400

        user.verified = True
        user.otp = None
        user.otp_expiry = None
        user.save()

        return jsonify({'message': 'Account verified successfully'}), 200

    @staticmethod
    def login():
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'message': 'Email and password are required'}), 400

        user = User.objects(email=email).first()
        if not user:
            return jsonify({'message': 'Invalid email or password'}), 401

        if not user.verified:
            return jsonify({'message': 'Account not verified. Please verify OTP first.'}), 403

        if not bcrypt.check_password_hash(user.password, password):
            return jsonify({'message': 'Invalid email or password'}), 401

        expires = datetime.timedelta(hours=1)
        access_token = create_access_token(identity=str(user.id), expires_delta=expires)

        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

        return jsonify({
            'access_token': access_token,
            'data': user_data,
            'message': 'Login successful'
        }), 200

    @staticmethod
    def send_otp_email(to_email, otp):
        subject = "TheraPalsy Email Verification Code"
        from_email = os.getenv("MAIL_USERNAME")

        # Buat objek email multipart
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"TheraPalsy <{from_email}>"
        msg["To"] = to_email
        msg["Reply-To"] = from_email

        # Format isi email dalam plain text dan HTML
        text = f"Your OTP code is: {otp}\nThis code will expire in 10 minutes.\nDo not share this code with anyone."

        html = f"""
        <html>
        <body>
            <p><strong>TheraPalsy Email Verification</strong></p>
            <p>Your OTP code is: <strong>{otp}</strong></p>
            <p>This code will expire in 10 minutes.<br>
            Do not share this code with anyone.</p>
        </body>
        </html>
        """

        # Tambahkan isi ke dalam email
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        msg.attach(part1)
        msg.attach(part2)

        # Kirim email
        with smtplib.SMTP(os.getenv("MAIL_SERVER"), int(os.getenv("MAIL_PORT"))) as server:
            server.starttls()
            server.login(from_email, os.getenv("MAIL_PASSWORD"))
            server.send_message(msg)
            
            
    @staticmethod
    def google_login():
        data = request.get_json()
        token = data.get("token")

        try:
            # Verifikasi token dengan Google
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), os.getenv("GOOGLE_CLIENT_ID"))
            email = idinfo["email"]
            username = idinfo.get("name", email.split('@')[0])

            # Cari user
            user = User.objects(email=email).first()

            if not user:
                user = User(
                    username=username,
                    email=email,
                    password="",  # Kosongkan karena pakai Google
                    created_at=datetime.datetime.utcnow(),
                    verified=True
                )
                user.save()

            access_token = create_access_token(identity=str(user.id), expires_delta=datetime.timedelta(hours=1))

            return jsonify({
                "access_token": access_token,
                "data": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                },
                "message": "Login via Google successful"
            }), 200

        except ValueError:
            return jsonify({"message": "Invalid token"}), 400
        
    @staticmethod
    def forgot_password():
        data = request.get_json()
        email = data.get('email')

        user = User.objects(email=email).first()
        if not user:
            return jsonify({'message': 'Email not found'}), 404

        # Buat OTP baru dan expiry
        otp = str(random.randint(1000, 9999))
        otp_expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)

        user.otp = otp
        user.otp_expiry = otp_expiry
        user.save()

        AuthController.send_otp_email(email, otp)

        return jsonify({'message': 'OTP has been sent to your email.'}), 200
    
    @staticmethod
    def reset_password():
        data = request.get_json()
        email = data.get('email')
        otp = data.get('otp')
        new_password = data.get('new_password')

        user = User.objects(email=email).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404

        if user.otp != otp:
            return jsonify({'message': 'Invalid OTP'}), 400

        if datetime.datetime.utcnow() > user.otp_expiry:
            return jsonify({'message': 'OTP expired'}), 400

        # Update password
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password = hashed_password
        user.otp = None
        user.otp_expiry = None
        user.save()

        return jsonify({'message': 'Password has been reset successfully'}), 200

    @staticmethod
    def verify_reset_otp():
        data = request.get_json()
        email = data.get('email')
        otp = data.get('otp')

        user = User.objects(email=email).first()
        if not user:
            return jsonify({'message': 'User not found'}), 404

        if user.otp != otp:
            return jsonify({'message': 'Invalid OTP'}), 400

        if datetime.datetime.utcnow() > user.otp_expiry:
            return jsonify({'message': 'OTP expired'}), 400

        return jsonify({'message': 'OTP verified. Proceed to reset password.'}), 200



