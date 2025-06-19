from mongoengine import Document, StringField, DateTimeField

class Article(Document):
    title = StringField(required=True)
    definisi = StringField()
    image = StringField()
    url = StringField()
    timestamp = DateTimeField()
