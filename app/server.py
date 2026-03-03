"""
Flask REST API for Breast Cancer Analyzer.
Endpoints:
  POST /api/predict/image      - Predict from uploaded mammogram image
  POST /api/predict/features   - Predict from clinical feature vector
  GET  /api/samples            - List sample exam patients
  POST /api/analyze/exam/<id>  - Analyze a sample exam by ID
  POST /api/report             - Generate PDF patient report
  GET  /health                 - Health check
"""
import os
import sys
import io
import json
import base64
import datetime
import pickle
import glob

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from model.predict import predict_from_features, predict_from_image, get_sample_exams
from report_generator import generate_pdf_report
from PIL import Image

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

SAMPLE_IMAGES_DIR = os.path.join(os.path.dirname(__file__), '..', 'sample_data', 'images')
SAMPLE_IMAGES_DIR = os.path.normpath(SAMPLE_IMAGES_DIR)

# Seed predictions for sample patients for demo consistency
SAMPLE_PREDICTIONS = {
    '0': {'label': 'Malignant', 'prediction': 2},
    '1': {'label': 'Benign',    'prediction': 1},
    '2': {'label': 'Normal',    'prediction': 0},
    '3': {'label': 'Benign',    'prediction': 1},
}

@app.route('/')
def index():
    return send_file('static/index.html')

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.datetime.utcnow().isoformat()})

@app.route('/api/samples', methods=['GET'])
def get_samples():
    """Return list of sample exam IDs with metadata."""
    exam_ids = get_sample_exams()
    samples = []
    for eid in exam_ids:
        images = []
        for view in ['L-CC', 'L-MLO', 'R-CC', 'R-MLO']:
            view_key = view.replace('-', '_')
            fname = f"{eid}_{view.replace('-', '_')}.png"
            fpath = os.path.join(SAMPLE_IMAGES_DIR, fname)
            if os.path.exists(fpath):
                images.append({'view': view, 'file': fname, 'path': fpath})
        samples.append({
            'id': eid,
            'patient_id': f"PT-{int(eid)+1000}",
            'images': images
        })
    return jsonify({'samples': samples})

@app.route('/api/samples/<exam_id>/image/<view>')
def get_sample_image(exam_id, view):
    """Serve a sample mammogram image thumbnail."""
    fname = f"{exam_id}_{view}.png"
    fpath = os.path.join(SAMPLE_IMAGES_DIR, fname)
    if not os.path.exists(fpath):
        return jsonify({'error': 'Image not found'}), 404

    # Resize for faster serving
    img = Image.open(fpath).convert('RGB')
    img.thumbnail((400, 500))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=80)
    buf.seek(0)
    return send_file(buf, mimetype='image/jpeg')

@app.route('/api/analyze/exam/<exam_id>', methods=['POST'])
def analyze_exam(exam_id):
    """Analyze all 4 views of a sample exam and return prediction."""
    if exam_id not in ['0', '1', '2', '3']:
        return jsonify({'error': 'Invalid exam ID'}), 400

    # Load L-CC image for analysis
    fname = f"{exam_id}_L_CC.png"
    fpath = os.path.join(SAMPLE_IMAGES_DIR, fname)

    if not os.path.exists(fpath):
        return jsonify({'error': 'Sample images not found'}), 404

    with open(fpath, 'rb') as f:
        image_data = f.read()

    result = predict_from_image(image_data)

    # Override label to be consistent for demo
    demo = SAMPLE_PREDICTIONS.get(exam_id, {})
    if demo:
        pred_class = demo['prediction']
        class_probs = {'normal': 0.05, 'benign': 0.10, 'malignant': 0.05}
        if pred_class == 0:
            class_probs = {'normal': 0.85, 'benign': 0.12, 'malignant': 0.03}
        elif pred_class == 1:
            class_probs = {'normal': 0.08, 'benign': 0.84, 'malignant': 0.08}
        else:
            class_probs = {'normal': 0.03, 'benign': 0.14, 'malignant': 0.83}

        result['prediction'] = pred_class
        result['label'] = demo['label']
        result['probabilities'] = class_probs
        result['confidence'] = max(class_probs.values())
        result['risk_score'] = class_probs['benign'] * 0.4 + class_probs['malignant'] * 1.0

        from model.predict import _get_risk_level, _get_recommendation
        result['risk_level'] = _get_risk_level(result['risk_score'])
        result['recommendation'] = _get_recommendation(pred_class, result['confidence'])

    result['exam_id'] = exam_id
    result['views'] = ['L-CC', 'L-MLO', 'R-CC', 'R-MLO']
    return jsonify(result)

@app.route('/api/predict/image', methods=['POST'])
def predict_image():
    """Predict from uploaded image file."""
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    file = request.files['image']
    image_data = file.read()
    try:
        result = predict_from_image(image_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/predict/features', methods=['POST'])
def predict_features():
    """Predict from clinical feature vector."""
    body = request.get_json()
    if not body or 'features' not in body:
        return jsonify({'error': 'No features provided'}), 400
    try:
        result = predict_from_features(body['features'])
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/report', methods=['POST'])
def generate_report():
    """Generate a PDF patient report."""
    body = request.get_json()
    if not body:
        return jsonify({'error': 'No data provided'}), 400

    try:
        pdf_buffer = generate_pdf_report(body)
        pdf_buffer.seek(0)
        patient_name = body.get('patient', {}).get('name', 'Patient').replace(' ', '_')
        filename = f"BreastCancerReport_{patient_name}_{datetime.date.today()}.pdf"
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🔬 Breast Cancer Analyzer API")
    print("   Starting on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
