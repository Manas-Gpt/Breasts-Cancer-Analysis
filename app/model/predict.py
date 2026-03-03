"""
Breast cancer prediction module.
Loads model and generates predictions with detailed analysis.
"""
import os
import pickle
import numpy as np
import joblib
from PIL import Image
import io
import base64

# Load model once at module level
_MODEL = None
_META = None

def _load_model():
    global _MODEL, _META
    if _MODEL is None:
        model_path = os.path.join(os.path.dirname(__file__), 'breast_cancer_model.pkl')
        meta_path = os.path.join(os.path.dirname(__file__), 'model_meta.pkl')
        _MODEL = joblib.load(model_path)
        _META = joblib.load(meta_path)
    return _MODEL, _META

def analyze_image(image_data: bytes) -> dict:
    """
    Analyze a mammogram image and extract pseudo-features for classification.
    Returns feature vector derived from image statistics.
    """
    img = Image.open(io.BytesIO(image_data)).convert('L')  # grayscale
    img_resized = img.resize((128, 128))
    arr = np.array(img_resized, dtype=np.float64)

    # Extract statistical features that approximate WDBC features
    # These are texture/intensity features analogous to cell nucleus measurements
    features = []

    # Mean intensity (radius mean proxy)
    features.append(arr.mean() / 255.0 * 28)                 # radius_mean range ~6-28

    # Texture: std of intensities
    features.append(arr.std() / 255.0 * 39)                  # texture_mean range ~9-39

    # Perimeter mean proxy (edge detection)
    from scipy.ndimage import sobel
    sx = sobel(arr, axis=0)
    sy = sobel(arr, axis=1)
    edge_mag = np.hypot(sx, sy)
    features.append(edge_mag.mean() / 255.0 * 188)           # perimeter_mean

    # Area mean proxy
    nonzero_frac = np.count_nonzero(arr > arr.mean()) / arr.size
    features.append(nonzero_frac * 2501)                      # area_mean

    # Smoothness = local variation
    local_var = np.var(arr[::4, ::4])
    features.append(local_var / (255**2) * 0.163)            # smoothness_mean

    # Compactness
    features.append(edge_mag.std() / 255.0 * 0.345)

    # Concavity
    features.append((arr > arr.mean() + arr.std()).mean() * 0.427)

    # Concave points
    features.append(features[6] * 0.201)

    # Symmetry
    left_half = arr[:, :64]
    right_half = np.fliplr(arr[:, 64:])
    symmetry = 1.0 - abs(left_half.mean() - right_half.mean()) / 255.0
    features.append(symmetry * 0.304)

    # Fractal dimension
    features.append((1.0 - nonzero_frac) * 0.0974)

    # SE versions (scale features by ~0.3)
    for i in range(10):
        features.append(features[i] * 0.3 * (1 + np.random.RandomState(i).uniform(-0.1, 0.1)))

    # Worst versions (scale features by ~2.5)
    for i in range(10):
        features.append(features[i] * 2.5 * (1 + np.random.RandomState(i+10).uniform(-0.1, 0.1)))

    return np.array(features[:30])

def predict_from_features(features: list) -> dict:
    """Predict from raw feature vector."""
    model, meta = _load_model()
    features_arr = np.array(features).reshape(1, -1)

    proba = model.predict_proba(features_arr)[0]
    pred_class = int(np.argmax(proba))
    class_names = meta['class_names']  # ['Normal', 'Benign', 'Malignant']

    # Risk score: weighted by class index
    risk_score = float(proba[1] * 0.4 + proba[2] * 1.0)

    # Confidence
    confidence = float(max(proba))

    return {
        'prediction': pred_class,
        'label': class_names[pred_class],
        'probabilities': {
            'normal': float(proba[0]),
            'benign': float(proba[1]),
            'malignant': float(proba[2])
        },
        'risk_score': min(risk_score, 1.0),
        'confidence': confidence,
        'feature_names': meta['feature_names'],
        'risk_level': _get_risk_level(risk_score),
        'recommendation': _get_recommendation(pred_class, confidence)
    }

def predict_from_image(image_data: bytes) -> dict:
    """Predict from mammogram image."""
    features = analyze_image(image_data)
    result = predict_from_features(features.tolist())
    result['analysis_method'] = 'image'
    return result

def _get_risk_level(risk_score: float) -> str:
    if risk_score < 0.2:
        return 'Low'
    elif risk_score < 0.5:
        return 'Moderate'
    elif risk_score < 0.75:
        return 'High'
    else:
        return 'Very High'

def _get_recommendation(pred_class: int, confidence: float) -> str:
    recommendations = {
        0: "Results indicate normal findings. Continue with routine annual mammography screening as recommended by your physician.",
        1: "Benign findings detected. Recommend follow-up imaging in 6 months and consultation with a breast specialist for further evaluation.",
        2: "Malignant findings detected. Immediate consultation with an oncologist is strongly recommended. Additional diagnostic tests (biopsy, MRI) should be performed urgently."
    }
    return recommendations[pred_class]

def get_sample_exams():
    """Return list of sample exam IDs from sample_data."""
    import glob
    import os
    images_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'sample_data', 'images')
    images_dir = os.path.normpath(images_dir)
    exam_ids = set()
    for f in glob.glob(os.path.join(images_dir, '*.png')):
        exam_id = os.path.basename(f).split('_')[0]
        exam_ids.add(exam_id)
    return sorted(list(exam_ids))
