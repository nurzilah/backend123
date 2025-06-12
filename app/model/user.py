from mongoengine import Document, StringField, DateTimeField, BooleanField
from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

class User(Document):
    meta = {'collection': 'users'}

    id = StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    username = StringField(required=True, unique=True, max_length=50)
    email = StringField(required=True, unique=True, max_length=120)
    password = StringField(required=True, max_length=256)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField()
    
    otp = StringField()
    otp_expiry = DateTimeField()
    verified = BooleanField(default=False)
    profile_image = StringField()

    def __str__(self):
        return f'<User {self.username}>'

    # ✅ Fungsi hash password
    @staticmethod
    def generate_password(raw_password):
        return generate_password_hash(raw_password)

    # ✅ Fungsi verifikasi password (opsional untuk login)
    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)
