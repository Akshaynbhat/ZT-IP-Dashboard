import os
import logging
import numpy as np
import pandas as pd
import joblib
import shap

logger = logging.getLogger(__name__)

# Resolve model directory: support environment variable first, then container path, and fallback to local repository root.
MODEL_DIR = os.getenv("MODEL_DIR")
if not MODEL_DIR:
    container_path = "/app/ml_models"
    if os.path.exists(container_path):
        MODEL_DIR = container_path
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        MODEL_DIR = os.path.join(base_dir, "ml", "models")

# Singletons for models and explainers
_isolation_forest = None
_random_forest = None
_explainer = None
_load_failed = False

def load_models():
    """
    Lazy singleton loader for models and explainers.
    """
    global _isolation_forest, _random_forest, _explainer
    if _isolation_forest is not None:
        return

    if_path = os.path.join(MODEL_DIR, "final_isolation_forest.pkl")
    rf_path = os.path.join(MODEL_DIR, "final_random_forest.pkl")

    if not os.path.exists(if_path) or not os.path.exists(rf_path):
        raise FileNotFoundError(f"Model files not found in {MODEL_DIR}. Paths: IF={if_path}, RF={rf_path}")

    _isolation_forest = joblib.load(if_path)
    _random_forest = joblib.load(rf_path)
    _explainer = shap.TreeExplainer(_random_forest)

def score_event(features) -> dict:
    """
    Computes anomaly score, risk probability, risk class, and SHAP explainability.
    
    Accepts:
    - pd.DataFrame (1 row containing the 14 CERT features)
    - dict (maps old or new formats to the 14-feature format)
    
    Returns:
    - dict: {anomaly_score, risk_class, risk_probability, shap_values}
    """
    global _load_failed
    
    # 1. Backwards compatibility mapping for dict inputs
    if isinstance(features, dict):
        feature_order = [
            "total_logins", "unique_login_pcs", "avg_login_hour", "off_hour_logins",
            "total_device_events", "unique_devices", "off_hour_device", "files_accessed",
            "unique_files", "unique_content", "off_hour_file", "files_per_login",
            "device_login_ratio", "off_hour_ratio"
        ]
        
        mapped = {}
        for k in feature_order:
            if k in features:
                mapped[k] = float(features[k])
            else:
                # Map old dictionary keys to approximate CERT features
                if k == "total_logins":
                    mapped[k] = float(features.get("login_count_24h", 0))
                elif k == "unique_login_pcs":
                    mapped[k] = float(1.0 if features.get("is_known_device", 1) else 0.0)
                elif k == "avg_login_hour":
                    mapped[k] = float(12.0)
                elif k == "off_hour_logins":
                    mapped[k] = float(features.get("login_count_24h", 0) if features.get("is_off_hours", 0) else 0.0)
                elif k == "total_device_events":
                    mapped[k] = float(features.get("login_count_24h", 0))
                elif k == "unique_devices":
                    mapped[k] = float(1.0)
                elif k == "off_hour_device":
                    mapped[k] = float(features.get("login_count_24h", 0) if features.get("is_off_hours", 0) else 0.0)
                elif k == "files_accessed":
                    mapped[k] = float(features.get("files_downloaded_count", 0))
                elif k == "unique_files":
                    mapped[k] = float(features.get("unique_resources_accessed", 0))
                elif k == "unique_content":
                    mapped[k] = float(features.get("unique_resources_accessed", 0))
                elif k == "off_hour_file":
                    mapped[k] = float(features.get("files_downloaded_count", 0) if features.get("is_off_hours", 0) else 0.0)
                elif k == "files_per_login":
                    logins = max(1, features.get("login_count_24h", 1))
                    mapped[k] = float(features.get("files_downloaded_count", 0) / logins)
                elif k == "device_login_ratio":
                    logins = max(1, features.get("login_count_24h", 1))
                    mapped[k] = float(1.0 / logins)
                elif k == "off_hour_ratio":
                    mapped[k] = float(1.0 if features.get("is_off_hours", 0) else 0.0)
                else:
                    mapped[k] = 0.0
        features = pd.DataFrame([mapped])

    # 2. Try to load models or log warning and fall back
    try:
        load_models()
    except Exception as e:
        if not _load_failed:
            logger.warning(f"Failed to load ML models, falling back to simulated stub: {str(e)}")
            _load_failed = True
            
        # Return fallback stub values
        return {
            "anomaly_score": 0.5,
            "risk_class": "medium",
            "risk_probability": 0.5,
            "shap_values": [
                {"feature": "is_off_hours", "shap_value": 0.12},
                {"feature": "files_downloaded_count", "shap_value": 0.08},
                {"feature": "bytes_transferred_24h", "shap_value": 0.05}
            ]
        }

    # 3. Model Scoring
    # Logistic squashing function mapping Isolation Forest score to 0-1 range
    # k=10 is the squashing scaling coefficient (tunable)
    k = 10
    d = float(_isolation_forest.decision_function(features)[0])
    anomaly_score = 1.0 / (1.0 + np.exp(k * d))

    # Random Forest risk prediction
    RF_POSITIVE_CLASS = int(os.getenv("RF_POSITIVE_CLASS", "1"))
    probs = _random_forest.predict_proba(features)[0]
    risk_probability = float(probs[RF_POSITIVE_CLASS])

    # Map risk probability to qualitative class
    if risk_probability <= 0.30:
        risk_class = "low"
    elif risk_probability <= 0.60:
        risk_class = "medium"
    else:
        risk_class = "high"

    # SHAP feature contributions
    sv_all = _explainer.shap_values(features)
    
    # Handle list-of-arrays (shap standard format) vs multi-dimensional arrays
    if isinstance(sv_all, list):
        sv = sv_all[RF_POSITIVE_CLASS][0]
    elif isinstance(sv_all, np.ndarray):
        if sv_all.ndim == 3:
            if sv_all.shape[0] == 2:  # n_classes is first dimension
                sv = sv_all[RF_POSITIVE_CLASS][0]
            else:  # n_classes is last dimension
                sv = sv_all[0, :, RF_POSITIVE_CLASS]
        else:
            sv = sv_all[0]
    else:
        sv = sv_all[0]

    # Map SHAP values to features and select the top 5 absolute contributors
    feature_names = list(features.columns)
    shap_list = []
    for name, val in zip(feature_names, sv):
        shap_list.append({
            "feature": name,
            "shap_value": float(val)
        })
        
    top_5_shap = sorted(shap_list, key=lambda x: abs(x["shap_value"]), reverse=True)[:5]

    return {
        "anomaly_score": anomaly_score,
        "risk_class": risk_class,
        "risk_probability": risk_probability,
        "shap_values": top_5_shap
    }
