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

@auth.route('/google-login', methods=['POST'])
def google_login():
    return AuthController.google_login()

@auth.route('/google/login/callback')
def google_login_callback():
    token = oauth.google.authorize_access_token()
    resp = oauth.google.get('userinfo')
    user_info = resp.json()

    email = user_info.get('email')
    username = user_info.get('given_name')

    if not email:
        flash('Gagal mengambil email dari Google.', 'danger')
        return redirect(url_for('auth.login'))

    existing_user = user_model.find_by_email(email)

    if existing_user:
        session['user_id'] = str(existing_user['_id'])
        session['username'] = existing_user.get('username', username)

        # **SIMPAN RIWAYAT LOGIN DI SINI**
        device = request.headers.get('User-Agent', 'Unknown Device')
        save_login_history(str(existing_user['_id']), device)

        flash(f'Selamat datang kembali, {session["username"]}!', 'success')
        return redirect(url_for('main.index'))
    else:
        user_model.create_user(
            username=username,
            email=email,
            password=None,
            otp=None,
            otp_expired=None,
            is_verified=True
        )
        new_user = user_model.find_by_email(email)
        session['user_id'] = str(new_user['_id'])
        session['username'] = username

        # **SIMPAN RIWAYAT LOGIN DI SINI**
        device = request.headers.get('User-Agent', 'Unknown Device')
        save_login_history(str(new_user['_id']), device)

        flash('Registrasi dan login berhasil menggunakan Google.', 'success')
        return redirect(url_for('main.index'))

