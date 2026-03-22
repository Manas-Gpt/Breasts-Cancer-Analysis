"""
Breast cancer prediction module.
Loads model and generates predictions with detailed analysis.
"""
import os
import numpy as np
import joblib
from PIL import Image
import io

# Load model once at module level
_MODEL = None
_META  = None

def _load_model():
    global _MODEL, _META
    if _MODEL is None:
        model_path = os.path.join(os.path.dirname(__file__), 'breast_cancer_model.pkl')
        meta_path  = os.path.join(os.path.dirname(__file__), 'model_meta.pkl')
        _MODEL = joblib.load(model_path)
        _META  = joblib.load(meta_path)
    return _MODEL, _META


def analyze_image(image_data: bytes) -> np.ndarray:
    """
    Extract 30 pseudo-features from a mammogram image.
    Uses pure numpy (no scipy) on a small thumbnail — fast and crash-safe.
    """
    img = Image.open(io.BytesIO(image_data)).convert('L')   # grayscale
    # Aggressively downsample — we only need texture stats, not full resolution
    img = img.resize((64, 64), Image.LANCZOS)
    arr = np.array(img, dtype=np.float64)                   # 64x64 array

    mean_v  = arr.mean()
    std_v   = arr.std()
    max_v   = arr.max()
    min_v   = arr.min()
    rng_v   = max_v - min_v

    # Simple gradient via finite differences (no scipy needed)
    grad_x  = np.diff(arr, axis=1)
    grad_y  = np.diff(arr, axis=0)
    edge    = np.abs(grad_x[:63, :]).mean() + np.abs(grad_y[:, :63]).mean()

    # Foreground / background ratio
    bright  = (arr > mean_v).mean()
    dark    = 1.0 - bright

    # Quadrant asymmetry
    q1 = arr[:32, :32].mean()
    q2 = arr[:32, 32:].mean()
    q3 = arr[32:, :32].mean()
    q4 = arr[32:, 32:].mean()
    asym_h = abs(q1 + q3 - q2 - q4) / (mean_v + 1e-9)
    asym_v = abs(q1 + q2 - q3 - q4) / (mean_v + 1e-9)

    # Contrast & homogeneity (simple)
    contrast   = std_v / (mean_v + 1e-9)
    uniformity = (arr / (max_v + 1e-9)).var()

    # Pack into 30 WDBC-like features using simple scaling
    # Scale factors chosen to map into realistic WDBC ranges
    features = np.array([
        mean_v / 255.0 * 28,           # radius_mean          range ~6-28
        std_v  / 255.0 * 39,           # texture_mean         range ~9-39
        edge   / 10.0  * 188,          # perimeter_mean
        bright * 2501,                 # area_mean
        contrast * 0.16,               # smoothness_mean
        uniformity * 0.35,             # compactness_mean
        bright * 0.43,                 # concavity_mean
        bright * 0.20,                 # concave_points_mean
        asym_h * 0.30,                 # symmetry_mean
        dark   * 0.097,                # fractal_dimension_mean
        # SE (standard error) columns — ~20-30% of mean features
        mean_v / 255.0 * 28  * 0.25,
        std_v  / 255.0 * 39  * 0.28,
        edge   / 10.0  * 188 * 0.22,
        bright * 2501        * 0.20,
        contrast * 0.16      * 0.30,
        uniformity * 0.35    * 0.28,
        bright * 0.43        * 0.25,
        bright * 0.20        * 0.22,
        asym_h * 0.30        * 0.30,
        dark   * 0.097       * 0.28,
        # Worst columns — ~2-3× mean features
        mean_v / 255.0 * 28  * 2.8,
        std_v  / 255.0 * 39  * 2.5,
        edge   / 10.0  * 188 * 2.2,
        bright * 2501        * 2.3,
        contrast * 0.16      * 2.4,
        uniformity * 0.35    * 2.6,
        bright * 0.43        * 2.5,
        bright * 0.20        * 2.7,
        asym_h * 0.30        * 2.3,
        dark   * 0.097       * 2.6,
    ], dtype=np.float64)

    return features


def predict_from_features(features: list) -> dict:
    """Predict from raw 30-feature vector."""
    model, meta = _load_model()
    features_arr = np.array(features, dtype=np.float64).reshape(1, -1)

    proba      = model.predict_proba(features_arr)[0]
    pred_class = int(np.argmax(proba))
    class_names = meta['class_names']   # ['Normal', 'Benign', 'Malignant']

    risk_score = float(proba[1] * 0.4 + proba[2] * 1.0)
    confidence = float(max(proba))

    return {
        'prediction':     pred_class,
        'label':          class_names[pred_class],
        'probabilities':  {
            'normal':    float(proba[0]),
            'benign':    float(proba[1]),
            'malignant': float(proba[2]),
        },
        'risk_score':     min(risk_score, 1.0),
        'confidence':     confidence,
        'feature_names':  meta['feature_names'],
        'risk_level':     _get_risk_level(risk_score),
        'recommendation': _get_recommendation(pred_class, confidence),
    }


def predict_from_image(image_data: bytes) -> dict:
    """Predict from mammogram image bytes."""
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
    return {
        0: "Results indicate normal findings. Continue with routine annual mammography screening as recommended by your physician.",
        1: "Benign findings detected. Recommend follow-up imaging in 6 months and consultation with a breast specialist for further evaluation.",
        2: "Malignant findings detected. Immediate consultation with an oncologist is strongly recommended. Additional diagnostic tests (biopsy, MRI) should be performed urgently.",
    }[pred_class]


def get_sample_exams():
    """Return sorted list of sample exam IDs from sample_data/images."""
    import glob
    images_dir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..', 'sample_data', 'images')
    )
    exam_ids = {
        os.path.basename(f).split('_')[0]
        for f in glob.glob(os.path.join(images_dir, '*.png'))
    }
    return sorted(exam_ids)
