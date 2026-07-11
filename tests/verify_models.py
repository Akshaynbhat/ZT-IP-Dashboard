import os
import sys
import numpy as np
import pandas as pd
import joblib

def main():
    # Resolve the local path for ml/models relative to the project root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_dir = os.path.join(base_dir, "ml", "models")
    
    print(f"Loading models from: {model_dir}")
    if_path = os.path.join(model_dir, "final_isolation_forest.pkl")
    rf_path = os.path.join(model_dir, "final_random_forest.pkl")
    
    if not os.path.exists(if_path) or not os.path.exists(rf_path):
        print("ERROR: Model pickle files not found. Make sure you run from the repo root.")
        sys.exit(1)
        
    if_model = joblib.load(if_path)
    rf_model = joblib.load(rf_path)
    
    # 14 CERT features in exact order (feature_names_in_)
    columns = [
        "total_logins", "unique_login_pcs", "avg_login_hour", "off_hour_logins",
        "total_device_events", "unique_devices", "off_hour_device", "files_accessed",
        "unique_files", "unique_content", "off_hour_file", "files_per_login",
        "device_login_ratio", "off_hour_ratio"
    ]
    
    # Test Vector A: Quiet 9-to-5 work day (Low risk)
    quiet_vector = {
        "total_logins": 2.0,
        "unique_login_pcs": 1.0,
        "avg_login_hour": 10.0,  # 10 AM average
        "off_hour_logins": 0.0,
        "total_device_events": 0.0,
        "unique_devices": 0.0,
        "off_hour_device": 0.0,
        "files_accessed": 5.0,
        "unique_files": 3.0,
        "unique_content": 3.0,
        "off_hour_file": 0.0,
        "files_per_login": 2.5,
        "device_login_ratio": 0.0,
        "off_hour_ratio": 0.0
    }
    
    # Test Vector B: Suspicious off-hours 300-file multi-device burst (High risk)
    suspicious_vector = {
        "total_logins": 1.0,
        "unique_login_pcs": 1.0,
        "avg_login_hour": 2.0,   # 2 AM average
        "off_hour_logins": 1.0,
        "total_device_events": 5.0,
        "unique_devices": 3.0,
        "off_hour_device": 5.0,
        "files_accessed": 300.0,
        "unique_files": 200.0,
        "unique_content": 200.0,
        "off_hour_file": 300.0,
        "files_per_login": 300.0,
        "device_login_ratio": 5.0,
        "off_hour_ratio": 1.0
    }
    
    df_quiet = pd.DataFrame([quiet_vector], columns=columns)
    df_suspicious = pd.DataFrame([suspicious_vector], columns=columns)
    
    RF_POSITIVE_CLASS = int(os.getenv("RF_POSITIVE_CLASS", "1"))
    print(f"Using RF_POSITIVE_CLASS = {RF_POSITIVE_CLASS}")
    
    # Helper to calculate and print scores
    def evaluate(df, label):
        # Isolation Forest Anomaly Score: squash d = decision_function to 0-1
        k = 10
        d = float(if_model.decision_function(df)[0])
        anomaly_score = 1.0 / (1.0 + np.exp(k * d))
        
        # Random Forest Risk Probability
        probs = rf_model.predict_proba(df)[0]
        risk_probability = float(probs[RF_POSITIVE_CLASS])
        
        # Qualitative Risk Class
        if risk_probability <= 0.30:
            risk_class = "low"
        elif risk_probability <= 0.60:
            risk_class = "medium"
        else:
            risk_class = "high"
            
        print(f"\n[{label} Scenario]")
        print(f"  Decision Function Value (d): {d:.4f}")
        print(f"  Anomaly Score: {anomaly_score:.4f}")
        print(f"  Risk Probability: {risk_probability:.4f}")
        print(f"  Risk Class: {risk_class}")
        return anomaly_score, risk_probability, risk_class

    quiet_anomaly, quiet_risk, quiet_class = evaluate(df_quiet, "Quiet Day")
    susp_anomaly, susp_risk, susp_class = evaluate(df_suspicious, "Suspicious Day")
    
    print("\n--- COMPARISON RESULTS ---")
    print(f"Anomaly Score Change: {quiet_anomaly:.4f} -> {susp_anomaly:.4f}")
    print(f"Risk Probability Change: {quiet_risk:.4f} -> {susp_risk:.4f}")
    
    # Assertions for verification
    if susp_risk > quiet_risk and susp_anomaly > quiet_anomaly:
        print("\nSUCCESS: Suspicious scenario correctly scored higher risk and anomaly!")
    else:
        print("\nWARNING: Verification assertion failed!")
        print("The suspicious scenario did not score higher in both risk and anomaly.")
        print("Please check if you need to set RF_POSITIVE_CLASS=0 as an environment variable.")
        sys.exit(1)

if __name__ == "__main__":
    main()
