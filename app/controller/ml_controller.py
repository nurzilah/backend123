import os
import joblib
import numpy as np
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.model.detection_result import DetectionResult

MODEL_PATH = os.path.join("app", "ml", "model_mlp.pkl")
model = joblib.load(MODEL_PATH)

class MLController:
    @staticmethod
    @jwt_required()
    def predict():
        try:
            data = request.get_json()
            input_data = data.get("input")

            if not input_data or not isinstance(input_data, list):
                return jsonify({"message": "Input harus berupa list."}), 400

            input_array = np.array(input_data).reshape(1, -1)
            prediction = model.predict(input_array)[0]
            user_id = get_jwt_identity()

            DetectionResult(
                user_id=user_id,
                input_data=input_data,
                result=str(prediction)
            ).save()

            return jsonify({
                "result": str(prediction),
                "user_id": user_id
            }), 200

        except Exception as e:
            return jsonify({"message": f"Prediksi gagal: {str(e)}"}), 500

    @staticmethod
    @jwt_required()
    def get_history():
        try:
            user_id = get_jwt_identity()
            results = DetectionResult.objects(user_id=user_id).order_by('-detected_at')
            return jsonify({
                "status": "success",
                "data": [
                    {
                        "input": r.input_data,
                        "result": r.result,
                        "detected_at": r.detected_at.isoformat()
                    } for r in results
                ]
            }), 200
        except Exception as e:
            return jsonify({"message": f"Gagal ambil riwayat: {str(e)}"}), 500