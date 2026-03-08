# 🔬 BreastGuard AI — Breast Cancer Analyzer

An AI-powered mammography analysis web application that classifies breast cancer findings into **Normal**, **Benign**, or **Malignant** categories and generates professional PDF patient reports.

> **Disclaimer:** This tool is for educational and research purposes only. It is **not** a substitute for professional medical advice or clinical diagnosis.

---

## ✨ Features

- 🌙 **Dual Theme** — Dark & Light mode with smooth transitions
- 🩻 **Image Upload** — Drag-and-drop mammogram analysis
- 🏥 **Sample Patients** — 4 pre-loaded NYU dataset exams (L-CC, L-MLO, R-CC, R-MLO)
- 📊 **Visual Results** — Animated doughnut chart, probability bars, risk gauge
- 💊 **Clinical Recommendations** — Tailored advice per classification
- 📄 **PDF Reports** — Full patient medical report generated in one click

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+

### Installation

```bash
# 1. Clone/navigate to project
cd d:\Projects\breasts_cancer_analysis

# 2. Install dependencies
pip install -r requirements.txt

# 3. Train the ML model (one-time)
python app/model/train_model.py

# 4. Start the server
python app/server.py
```

Open **http://localhost:5000** in your browser.

---

## 📁 Project Structure

```
breasts_cancer_analysis/
├── sample_data/
│   ├── images/                    # 4 patient exams × 4 mammogram views (PNG)
│   └── exam_list_before_cropping.pkl
├── app/
│   ├── server.py                  # Flask REST API
│   ├── report_generator.py        # PDF report generator (ReportLab)
│   ├── model/
│   │   ├── train_model.py         # ML model trainer
│   │   ├── predict.py             # Prediction logic
│   │   └── breast_cancer_model.pkl  # Saved trained model
│   └── static/
│       ├── index.html             # Frontend app
│       ├── style.css              # Dual-theme styles
│       └── app.js                 # Frontend logic & API calls
└── requirements.txt
```

---

## 🧠 How It Works

### Pipeline
```
Mammogram Image → Feature Extraction → ML Classifier → Results + PDF Report
```

1. **Upload** a mammogram image (or pick a sample patient)
2. **Feature extraction** — 30 radiometric descriptors computed from image statistics
3. **Classification** — Random Forest model outputs probabilities for each class
4. **Results displayed** with probability chart, risk gauge, and recommendation
5. **Generate PDF** with full patient details and clinical summary

### Classifications

| Class | Description | Action |
|-------|-------------|--------|
| ✅ Normal | No suspicious findings | Routine annual screening |
| ⚠️ Benign | Non-cancerous findings | Follow-up in 6 months |
| 🚨 Malignant | Potentially cancerous | Immediate oncology consult |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web UI |
| `GET` | `/health` | Server health check |
| `GET` | `/api/samples` | List sample patient exams |
| `GET` | `/api/samples/<id>/image/<view>` | Serve thumbnail image |
| `POST` | `/api/analyze/exam/<id>` | Analyze a sample exam |
| `POST` | `/api/predict/image` | Predict from uploaded image |
| `POST` | `/api/predict/features` | Predict from feature vector |
| `POST` | `/api/report` | Generate PDF patient report |

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask, Flask-CORS |
| ML | scikit-learn (Random Forest + Calibration) |
| Training Data | Wisconsin Diagnostic Breast Cancer (UCI) |
| Image Processing | Pillow, SciPy |
| PDF Generation | ReportLab |
| Frontend | HTML5, Vanilla CSS, JavaScript |
| Charts | Chart.js |

---



## 📋 Sample Data

The `sample_data/images/` directory contains 4 de-identified mammography exams from the NYU dataset, each with four standard views:
- **L-CC** — Left Craniocaudal
- **L-MLO** — Left Mediolateral Oblique
- **R-CC** — Right Craniocaudal
- **R-MLO** — Right Mediolateral Oblique

---

