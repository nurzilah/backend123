from mongoengine import Document, StringField, DateTimeField
from datetime import datetime
import pytz

def get_jakarta_time():
    return datetime.now(pytz.timezone('Asia/Jakarta'))

class LoginHistory(Document):
    user_id = StringField(required=True)
    device = StringField()
    login_time = DateTimeField(default=get_jakarta_time)

    meta = {'collection': 'login_history'}
