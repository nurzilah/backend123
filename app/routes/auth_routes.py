from flask import Blueprint
from app.controller.auth_controller import AuthController

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    return AuthController.register()

@auth.route('/verify-otp', methods=['POST'])
def verify_otp():
    return AuthController.verify_otp()

@auth.route('/login', methods=['POST'])
def login():
    return AuthController.login()

@auth.route('/forgot-password', methods=['POST'])
def forgot_password():
    return AuthController.forgot_password()

@auth.route('/verify-reset-otp', methods=['POST'])
def verify_reset_otp():
    return AuthController.verify_reset_otp()

@auth.route('/reset-password', methods=['POST'])
def reset_password():
    return AuthController.reset_password()

@auth.route('/google', methods=['POST'])
def google_login():
    return AuthController.google_login()

