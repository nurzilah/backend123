from flask import Blueprint, request, jsonify
import threading, os, cv2, mediapipe as mp
import numpy as np, pandas as pd, pickle, base64

detection_api = Blueprint('detection_api', __name__)  # ✅ Nama unik

model = scaler = mp_face_mesh = face_mesh = None
lock = threading.Lock()
FEATURE_COLUMNS = ['eyebrow_dist', 'eye_asymmetry', 'mar', 'mouth_asymmetry', 'pucker_asymmetry']

def load_model():
    global model, scaler, mp_face_mesh, face_mesh
    try:
        with open(os.path.join('app', 'ml', 'model_mlp.pkl'), 'rb') as f:
            model = pickle.load(f)
        with open(os.path.join('app', 'ml', 'scaler.pkl'), 'rb') as f:
            scaler = pickle.load(f)

        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )

        print("✅ Bell's Palsy model loaded.")
    except Exception as e:
        print(f"❌ Error loading model: {e}")

def euclidean(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

def decode_base64_image(data):
    try:
        if ',' in data: data = data.split(',')[1]
        if len(data) % 4: data += '=' * (4 - len(data) % 4)
        return cv2.imdecode(np.frombuffer(base64.b64decode(data), np.uint8), cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"❌ decode error: {e}")
        return None

def extract_features(landmarks):
    try:
        def pt(i): return (landmarks.landmark[i].x, landmarks.landmark[i].y)
        return pd.DataFrame([{
            'eyebrow_dist': euclidean(pt(55), pt(285)),
            'eye_asymmetry': abs(
                euclidean(pt(159), pt(145)) / (euclidean(pt(33), pt(133)) + 1e-8) -
                euclidean(pt(386), pt(374)) / (euclidean(pt(362), pt(263)) + 1e-8)
            ),
            'mar': euclidean(pt(13), pt(14)) / (euclidean(pt(61), pt(291)) + 1e-8),
            'mouth_asymmetry': abs(pt(61)[1] - pt(291)[1]),
            'pucker_asymmetry': abs(pt(78)[0] - pt(308)[0]),
        }], columns=FEATURE_COLUMNS)
    except Exception as e:
        print(f"❌ feature error: {e}")
        return None

@detection_api.route('/predict_bellspalsy', methods=['POST'])
def predict_bellspalsy():
    if not all([model, scaler, face_mesh]):
        return jsonify({'success': False, 'error': 'Model not loaded'}), 503

    data = request.json
    frames = data.get('frames', [])
    if not frames:
        return jsonify({'success': False, 'error': 'No frames'}), 400

    features = []
    with lock:
        for frame in frames:
            img = decode_base64_image(frame)
            if img is None: continue
            result = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            if result.multi_face_landmarks:
                for l in result.multi_face_landmarks:
                    df = extract_features(l)
                    if df is not None:
                        features.append(df)

    if not features:
        return jsonify({'success': False, 'error': 'No face landmarks'}), 400

    df = pd.concat(features, ignore_index=True)
    scaled = scaler.transform(df)
    preds = model.predict(scaled)
    probs = model.predict_proba(scaled)[:, 1]
    avg_prob = float(probs.mean())
    is_positive = avg_prob >= 0.5

    return jsonify({
        'success': True,
        'is_positive': is_positive,
        'prediction': "Bell's Palsy" if is_positive else "Normal",
        'confidence': avg_prob,
        'confidence_level': "Tinggi" if avg_prob > 0.7 or avg_prob < 0.3 else "Sedang",
        'percentage': round(avg_prob * 100, 1),
        'total_frames': len(preds),
        'bellspalsy_frames': int((preds == 1).sum()),
        'normal_frames': int((preds == 0).sum()),
        'probabilities': {
            'normal': float(1 - avg_prob),
            'bells_palsy': avg_prob
        }
    })

@detection_api.route('/detection_health', methods=['GET'])
def detection_health():
    return jsonify({
        'status': 'healthy' if all([model, scaler, face_mesh]) else 'unhealthy',
        'model_loaded': model is not None,
        'scaler_loaded': scaler is not None,
        'mediapipe_initialized': face_mesh is not None
    })

load_model()
