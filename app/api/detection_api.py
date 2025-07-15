from flask import Blueprint, request, jsonify
import threading, os, cv2, mediapipe as mp
import numpy as np, pandas as pd, pickle, base64
from datetime import datetime
import json
from app.model.detection_result import DetectionResult  

detection_api = Blueprint('detection_api', __name__)  

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

@detection_api.route('/save', methods=['POST'])
def save_detection_result():
    """Endpoint untuk menyimpan hasil deteksi ke MongoDB"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        # ✅ VALIDASI: Pastikan field wajib ada
        user_id = data.get('user_id')
        confidence = data.get('confidence', 0.0)

        if not user_id:
            return jsonify({
                'success': False,
                'error': 'Missing required field: user_id'
            }), 400

        # ✅ VALIDASI: Jangan simpan kalau confidence kosong atau 0
        if confidence is None or float(confidence) == 0.0:
            return jsonify({
                'success': False,
                'error': 'Invalid detection result (confidence = 0, not saving)'
            }), 400

        # Siapkan data untuk disimpan
        input_data = []
        if 'frames' in data:
            input_data.append({
                'type': 'frames',
                'count': len(data['frames']),
                'timestamp': datetime.now().isoformat()
            })

        result_data = {
            'prediction': data.get('prediction', ''),
            'is_positive': data.get('is_positive', False),
            'confidence': confidence,
            'confidence_level': data.get('confidence_level', ''),
            'percentage': data.get('percentage', 0.0),
            'total_frames': data.get('total_frames', 0),
            'bellspalsy_frames': data.get('bellspalsy_frames', 0),
            'normal_frames': data.get('normal_frames', 0),
            'probabilities': data.get('probabilities', {}),
            'additional_notes': data.get('notes', ''),
            'processed_at': datetime.now().isoformat()
        }

        # ✅ SIMPAN hanya jika confidence valid
        detection_result = DetectionResult(
            user_id=user_id,
            input_data=input_data,
            result=result_data
        )

        detection_result.save()

        return jsonify({
            'success': True,
            'message': 'Detection result saved successfully to MongoDB',
            'document_id': str(detection_result.id),
            'user_id': detection_result.user_id,
            'detected_at': detection_result.detected_at.isoformat(),
            'collection': 'deteksi_history'
        })

    except Exception as e:
        print(f"❌ Error saving detection result to MongoDB: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to save to database: {str(e)}'
        }), 500


@detection_api.route('/detection_health', methods=['GET'])
def detection_health():
    return jsonify({
        'status': 'healthy' if all([model, scaler, face_mesh]) else 'unhealthy',
        'model_loaded': model is not None,
        'scaler_loaded': scaler is not None,
        'mediapipe_initialized': face_mesh is not None
    })

# Endpoint untuk melihat history hasil deteksi dari MongoDB
@detection_api.route('/results', methods=['GET'])
def get_detection_results():
    """Endpoint untuk mengambil history hasil deteksi dari MongoDB"""
    try:
        # Parameter query untuk filtering
        user_id = request.args.get('user_id')
        limit = int(request.args.get('limit', 50))  # Default 50 records
        page = int(request.args.get('page', 1))     # Default page 1
        
        # Build query
        query = {}
        if user_id:
            query['user_id'] = user_id
        
        # Hitung offset untuk pagination
        offset = (page - 1) * limit
        
        # Query ke MongoDB
        detection_results = DetectionResult.objects(**query).order_by('-detected_at').skip(offset).limit(limit)
        total_count = DetectionResult.objects(**query).count()
        
        # Convert ke dictionary
        results = []
        for detection in detection_results:
            result_dict = detection.to_dict()
            result_dict['id'] = str(detection.id)
            
            # Parse JSON result jika memungkinkan
            try:
                if detection.result:
                    parsed_result = json.loads(detection.result)
                    result_dict['parsed_result'] = parsed_result
            except json.JSONDecodeError:
                result_dict['parsed_result'] = None
            
            results.append(result_dict)
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results),
            'total_count': total_count,
            'page': page,
            'limit': limit,
            'total_pages': (total_count + limit - 1) // limit,
            'has_next': offset + limit < total_count,
            'has_prev': page > 1
        })
        
    except Exception as e:
        print(f"❌ Error getting detection results from MongoDB: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get results from database: {str(e)}'
        }), 500

# Endpoint untuk mendapatkan detail satu hasil deteksi
@detection_api.route('/results/<result_id>', methods=['GET'])
def get_detection_result_detail(result_id):
    """Endpoint untuk mengambil detail satu hasil deteksi berdasarkan ID"""
    try:
        detection_result = DetectionResult.objects(id=result_id).first()
        
        if not detection_result:
            return jsonify({
                'success': False,
                'error': 'Detection result not found'
            }), 404
        
        result_dict = detection_result.to_dict()
        result_dict['id'] = str(detection_result.id)
        
        # Parse JSON result
        try:
            if detection_result.result:
                parsed_result = json.loads(detection_result.result)
                result_dict['parsed_result'] = parsed_result
        except json.JSONDecodeError:
            result_dict['parsed_result'] = None
        
        return jsonify({
            'success': True,
            'result': result_dict
        })
        
    except Exception as e:
        print(f"❌ Error getting detection result detail: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get result detail: {str(e)}'
        }), 500

# Endpoint untuk menghapus hasil deteksi
@detection_api.route('/results/<result_id>', methods=['DELETE'])
def delete_detection_result(result_id):
    """Endpoint untuk menghapus hasil deteksi berdasarkan ID"""
    try:
        detection_result = DetectionResult.objects(id=result_id).first()
        
        if not detection_result:
            return jsonify({
                'success': False,
                'error': 'Detection result not found'
            }), 404
        
        detection_result.delete()
        
        return jsonify({
            'success': True,
            'message': 'Detection result deleted successfully',
            'deleted_id': result_id
        })
        
    except Exception as e:
        print(f"❌ Error deleting detection result: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to delete result: {str(e)}'
        }), 500
    
@detection_api.route('/history/last/<user_id>', methods=['GET'])
def get_latest_detection_result(user_id):
    try:
        result = DetectionResult.objects(user_id=user_id).order_by('-detected_at').first()
        if result:
            result_dict = result.to_dict()
            result_dict['id'] = str(result.id)

            try:
                if result.result:
                    parsed_result = json.loads(result.result)
                    result_dict['parsed_result'] = parsed_result
            except json.JSONDecodeError:
                result_dict['parsed_result'] = None

            return jsonify({
                'success': True,
                'result': result_dict
            }), 200

        return jsonify({'success': True, 'result': None}), 200

    except Exception as e:
        print(f"❌ Error getting latest detection result: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to get latest result: {str(e)}'
        }), 500


load_model()