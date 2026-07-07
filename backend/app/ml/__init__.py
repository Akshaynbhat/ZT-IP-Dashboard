import logging

logger = logging.getLogger(__name__)

def score_event(features: dict) -> dict:
    """
    STUB: Member 2 will replace this with real ML model calls.
    Interface contract — input features dict keys:
    files_downloaded_count, bytes_transferred_24h, login_count_24h,
    unique_resources_accessed, is_off_hours, is_weekend,
    hours_since_last_login, login_time_deviation, is_known_device,
    bytes_deviation_from_baseline, downloads_deviation_from_baseline,
    privilege_change_flag
    
    Returns dict with: anomaly_score (float 0-1), risk_class (str low/medium/high),
    risk_probability (float 0-1), shap_values (list of dicts)
    """
    logger.warning("ML stub called — Member 2 has not yet replaced this with real models")
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
