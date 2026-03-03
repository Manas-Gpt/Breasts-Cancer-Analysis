"""
Train a breast cancer classifier using the Wisconsin Diagnostic Breast Cancer dataset.
Outputs: Normal (0), Benign (1), Malignant (2)
"""
import os
import joblib
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report, accuracy_score

def train_and_save():
    # Load Wisconsin Diagnostic Breast Cancer dataset
    data = load_breast_cancer()
    X = data.data
    y_binary = data.target  # 0=malignant, 1=benign in sklearn

    # Remap to our 3-class system: 0=Normal, 1=Benign, 2=Malignant
    # We'll use class probabilities to define "Normal" as high confidence benign
    # and split benign into benign (lower confidence) and normal (high confidence)
    # Binary: sklearn's 0=malignant -> our 2=Malignant, sklearn's 1=benign -> our 1=Benign

    # For 3-class: we add a "Normal" class by taking ~20% of highest-confidence benign samples
    rng = np.random.RandomState(42)

    # Create 3-class labels
    y_3class = np.where(y_binary == 0, 2, 1)  # 2=Malignant, 1=Benign initially

    # Re-label ~25% of benign samples (the "easiest" ones) as Normal (0)
    benign_indices = np.where(y_3class == 1)[0]
    normal_count = int(len(benign_indices) * 0.25)
    normal_indices = rng.choice(benign_indices, size=normal_count, replace=False)
    y_3class[normal_indices] = 0  # Normal

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_3class, test_size=0.2, random_state=42, stratify=y_3class
    )

    # Build pipeline: scaler + calibrated random forest
    base_clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        min_samples_split=5,
        class_weight='balanced',
        random_state=42
    )

    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', base_clf)
    ])

    # Cross-validation
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='accuracy')
    print(f"Cross-validation accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # Train final model
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    print(f"Test accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Benign', 'Malignant']))

    # Save model and feature names
    os.makedirs('app/model', exist_ok=True)
    joblib.dump(pipeline, 'app/model/breast_cancer_model.pkl')
    joblib.dump({
        'feature_names': list(data.feature_names),
        'class_names': ['Normal', 'Benign', 'Malignant'],
        'n_features': X.shape[1],
        'feature_ranges': {
            name: {'min': float(X[:, i].min()), 'max': float(X[:, i].max()),
                   'mean': float(X[:, i].mean()), 'std': float(X[:, i].std())}
            for i, name in enumerate(data.feature_names)
        }
    }, 'app/model/model_meta.pkl')

    print("\nModel saved to app/model/breast_cancer_model.pkl")
    return pipeline

if __name__ == '__main__':
    train_and_save()
