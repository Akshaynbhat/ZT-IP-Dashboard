# AI Model Review

## Dataset

**CERT Insider Threat Dataset Release 4.2**

Main files used:
- `logon.csv`
- `device.csv`
- `file.csv`

Purpose:
- Analyze user behavior for insider threat detection.
- Generate trust scores and detect anomalous activities.

---

## Features Used

- Login frequency
- Device usage
- File access activity
- Off-hour logins
- Unique login devices
- Number of files accessed
- User behavior patterns

---

## Preprocessing

- Dataset exploration
- Missing value removal
- Duplicate removal
- Data validation
- Feature engineering preparation

---

## Machine Learning Algorithms

- **Isolation Forest** – Detects anomalous user behavior.
- **Random Forest** – Predicts insider threat probability.
- **SHAP (SHapley Additive Explanations)** – Explains the contribution of features to each prediction.
- **Trust Score Engine** – Generates a dynamic trust score for each user.

---

## Output

- Normal User
- Suspicious User
- Anomaly Score
- Risk Probability
- Dynamic Trust Score
- Security Alerts
- SHAP Feature Explanation

---

## Strengths

- Uses the CERT Insider Threat Dataset Release 4.2.
- Detects abnormal user behavior in real time.
- Supports continuous monitoring.
- Generates explainable AI predictions using SHAP.
- Integrates with the Zero Trust Security Dashboard.
- Supports dynamic trust score generation.

---

## Suggestions

- Tune Isolation Forest and Random Forest hyperparameters.
- Add more behavioral features from network and email logs.
- Retrain models periodically using recent data.
- Evaluate model performance using Precision, Recall, F1-Score, and ROC-AUC.
- Implement online learning for real-time adaptation.
- Reduce false positives using adaptive threshold tuning.
