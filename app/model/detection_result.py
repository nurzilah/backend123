from mongoengine import Document, StringField, DateTimeField, ListField
from datetime import datetime
import pytz

class DetectionResult(Document):
    user_id = StringField(required=True)
    input_data = ListField()
    result = StringField()
    detected_at = DateTimeField(default=lambda: datetime.now(pytz.timezone("Asia/Jakarta")))

    meta = {
        'collection': 'capstone',
        'db_alias': 'deteksi_history'
    }