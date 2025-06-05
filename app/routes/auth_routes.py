from flask import Blueprint
from app.controller.auth_controller import AuthController

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    return AuthController.register()

@auth.route('/login', methods=['POST'])
def login():
    return AuthController.login()

@auth.route('/verify-otp', methods=['POST'])
def verify_otp():
    return AuthController.verify_otp()

@auth.route('/google', methods=['POST'])
def google_login():
    return AuthController.google_login()

# Forgot password flow
auth.add_url_rule('/forgot-password', view_func=AuthController.forgot_password, methods=['POST'])
auth.add_url_rule('/verify-reset-otp', view_func=AuthController.verify_reset_otp, methods=['POST'])  # <-- Tambahkan ini
auth.add_url_rule('/reset-password', view_func=AuthController.reset_password, methods=['POST'])
