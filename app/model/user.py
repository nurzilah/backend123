from mongoengine import Document, StringField, DateTimeField, BooleanField
from datetime import datetime
import uuid

class User(Document):
    meta = {'collection': 'users'}

    id = StringField(primary_key=True, default=lambda: str(uuid.uuid4()))
    username = StringField(required=True, unique=True, max_length=50)
    email = StringField(required=True, unique=True, max_length=120)
    password = StringField(required=True, max_length=128)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField()
    
    # Tambahan
    otp = StringField()
    otp_expiry = DateTimeField()
    verified = BooleanField(default=False)

    def __str__(self):
        return f'<User {self.username}>'
