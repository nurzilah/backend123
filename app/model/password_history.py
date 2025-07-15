from mongoengine import Document, StringField, DateTimeField
from datetime import datetime

class PasswordHistory(Document):
    user_id = StringField(required=True)
    old_password = StringField(required=True)
    new_password = StringField(required=True)
    changed_at = DateTimeField(default=datetime.utcnow)
