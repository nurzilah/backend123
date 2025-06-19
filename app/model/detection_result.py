from mongoengine import Document, StringField, DateTimeField, ListField
from datetime import datetime
import pytz

class DetectionResult(Document):
    user_id = StringField(required=True)
    input_data = ListField()
    result = StringField()
    detected_at = DateTimeField(default=lambda: datetime.now(pytz.timezone("Asia/Jakarta")))

    meta = {
        'collection': 'deteksi_history'
    }

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "input_data": self.input_data,
            "result": self.result,
            "detected_at": self.detected_at.isoformat()
        }
