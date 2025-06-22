from flask import Blueprint, request, jsonify
import threading
import os
import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import pickle
import base64

detection_api = Blueprint('detection_api', __name__)

# Global variables untuk model dan MediaPipe
model = None
scaler = None
mp_face_mesh = None
face_mesh = None
lock = threading.Lock()

# Kolom fitur sesuai dengan training
FEATURE_COLUMNS = ['eyebrow_dist', 'eye_asymmetry', 'mar', 'mouth_asymmetry', 'pucker_asymmetry']

def load_model():
    """Load model dan scaler saat blueprint diimport"""
    global model, scaler, mp_face_mesh, face_mesh

    try:
        model_path = os.path.join('app', 'ml', 'model_mlp.pkl')
        scaler_path = os.path.join('app', 'ml', 'scaler.pkl')

        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)

        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )

        print("✅ Bell's Palsy detection model loaded successfully!")
        return True
    except Exception as e:
        print(f"❌ Error loading Bell's Palsy model: {e}")
        return False

def euclidean(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def decode_base64_image(image_data):
    """Decode base64 string ke image OpenCV"""
    try:
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        # Tambahkan padding jika kurang
        missing_padding = len(image_data) % 4
        if missing_padding:
            image_data += '=' * (4 - missing_padding)

        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Decoding to OpenCV image failed")
        return image
    except Exception as e:
        print(f"❌ Error decoding image: {e}")
        return None

def extract_features_from_landmarks(landmarks):
    try:
        def get_point(i):
            return (landmarks.landmark[i].x, landmarks.landmark[i].y)

        left_eyebrow = get_point(55)
        right_eyebrow = get_point(285)
        eyebrow_dist = euclidean(left_eyebrow, right_eyebrow)

        left_eye_top = get_point(159)
        left_eye_bottom = get_point(145)
        left_eye_left = get_point(33)
        left_eye_right = get_point(133)
        left_ear = euclidean(left_eye_top, left_eye_bottom) / (euclidean(left_eye_left, left_eye_right) + 1e-8)

        right_eye_top = get_point(386)
        right_eye_bottom = get_point(374)
        right_eye_left = get_point(362)
        right_eye_right = get_point(263)
        right_ear = euclidean(right_eye_top, right_eye_bottom) / (euclidean(right_eye_left, right_eye_right) + 1e-8)

        eye_asymmetry = abs(left_ear - right_ear)

        top_lip = get_point(13)
        bottom_lip = get_point(14)
        left_mouth = get_point(61)
        right_mouth = get_point(291)
        mar = euclidean(top_lip, bottom_lip) / (euclidean(left_mouth, right_mouth) + 1e-8)

        mouth_asymmetry = abs(left_mouth[1] - right_mouth[1])

        left_pucker = get_point(78)
        right_pucker = get_point(308)
        pucker_asymmetry = abs(left_pucker[0] - right_pucker[0])

        features = {
            'eyebrow_dist': eyebrow_dist,
            'eye_asymmetry': eye_asymmetry,
            'mar': mar,
            'mouth_asymmetry': mouth_asymmetry,
            'pucker_asymmetry': pucker_asymmetry
        }

        return pd.DataFrame([features], columns=FEATURE_COLUMNS)
    except Exception as e:
        print(f"❌ Error extracting features: {e}")
        return None

@detection_api.route('/predict_bellspalsy', methods=['POST'])
def predict_bellspalsy():
    global model, scaler, face_mesh

    if not all([model, scaler, face_mesh]):
        return jsonify({'success': False, 'error': 'Model not loaded'}), 503

    try:
        data = request.json
        frames = data.get('frames', [])

        if not frames:
            return jsonify({'success': False, 'error': 'No frames provided'}), 400

        print(f"📸 Processing {len(frames)} frames for Bell's Palsy detection")

        with lock:
            features_list = []
            for i, frame_data in enumerate(frames):
                image = decode_base64_image(frame_data)
                if image is None:
                    print(f"⚠️ Skipping frame {i+1}: decode failed")
                    continue

                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(rgb)

                if results.multi_face_landmarks:
                    for landmarks in results.multi_face_landmarks:
                        df = extract_features_from_landmarks(landmarks)
                        if df is not None:
                            features_list.append(df)

            if not features_list:
                return jsonify({'success': False, 'error': 'No valid face landmarks detected'}), 400

            all_features = pd.concat(features_list, ignore_index=True)
            scaled = scaler.transform(all_features)

            preds = model.predict(scaled)
            probs = model.predict_proba(scaled)[:, 1]

            avg_prob = float(probs.mean())
            is_positive = avg_prob >= 0.5
            confidence_level = "Tinggi" if avg_prob > 0.7 or avg_prob < 0.3 else "Sedang"

            result = {
                'success': True,
                'is_positive': is_positive,
                'prediction': "Bell's Palsy" if is_positive else "Normal",
                'confidence': avg_prob,
                'confidence_level': confidence_level,
                'percentage': round(avg_prob * 100, 1),
                'total_frames': len(preds),
                'bellspalsy_frames': int((preds == 1).sum()),
                'normal_frames': int((preds == 0).sum()),
                'probabilities': {
                    'normal': float(1 - avg_prob),
                    'bells_palsy': avg_prob
                }
            }

            print(f"🎯 Prediction: {result['prediction']} with {result['percentage']}% confidence")
            return jsonify(result)

    except Exception as e:
        print(f"❌ Error in prediction: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@detection_api.route('/detection_health', methods=['GET'])
def detection_health():
    return jsonify({
        'status': 'healthy' if all([model, scaler, face_mesh]) else 'unhealthy',
        'message': 'Bell\'s Palsy Detection API',
        'model_loaded': model is not None,
        'scaler_loaded': scaler is not None,
        'mediapipe_initialized': face_mesh is not None
    })

# Jalankan saat import
load_model()
