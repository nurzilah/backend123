from flask import Blueprint
from app.controller.ml_controller import MLController

ml = Blueprint('ml', __name__)

@ml.route('/predict', methods=['POST'])
def predict():
    return MLController.predict()

@ml.route('/history', methods=['GET'])
def get_history():
    return MLController.get_history()
