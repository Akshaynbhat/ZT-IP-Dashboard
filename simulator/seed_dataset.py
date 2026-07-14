import os
import sys
import uuid
import random
import json
import numpy as np
import pandas as pd
import joblib
import shap
import psycopg2
from datetime import datetime, timedelta

# Database Connection Settings
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "zt_dashboard")
DB_USER = os.getenv("DB_USER", "zt_admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "zt_pass")
DEFAULT_TENANT_ID = "9f9bbf10-e3f3-470b-85be-587265bf02ab"

def main():
    print("=" * 60)
    print("ZT-IP DATABASE CERT DATASET SEEDER")
    print("=" * 60)

    # 1. Load ML Models
    model_dir = os.getenv("MODEL_DIR", "ml/models")
    if_path = os.path.join(model_dir, "final_isolation_forest.pkl")
    rf_path = os.path.join(model_dir, "final_random_forest.pkl")
    
    if not os.path.exists(if_path) or not os.path.exists(rf_path):
        print(f"ERROR: Model files not found in {model_dir}")
        sys.exit(1)

    print("Loading Isolation Forest and Random Forest models...")
    if_model = joblib.load(if_path)
    rf_model = joblib.load(rf_path)
    explainer = shap.TreeExplainer(rf_model)
    print("Models loaded successfully.")

    # 2. Load Features CSV
    csv_path = "ml/data/features_daily.csv"
    if not os.path.exists(csv_path):
        print(f"ERROR: Features CSV not found at {csv_path}")
        sys.exit(1)

    print("Loading features_daily.csv (this might take a few seconds)...")
    df = pd.read_csv(csv_path)
    print(f"CSV Loaded. Shape: {df.shape}")

    # 3. Select Target Users (10 Insiders + 10 Normal)
    insider_users = [f"U{i:04d}" for i in range(10)]
    normal_users = [f"U{i:04d}" for i in range(100, 110)]
    target_users = insider_users + normal_users
    print(f"Target users: {target_users}")

    # 4. Connect to PostgreSQL
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()
        print("Connected to PostgreSQL database.")
    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}")
        sys.exit(1)

    # 5. Clear Old Data (using TRUNCATE to bypass append-only rules on access_logs)
    print("Clearing old telemetry, scores, and alerts from database...")
    try:
        cur.execute("TRUNCATE TABLE alerts, trust_scores, model_scores, access_logs, devices CASCADE;")
        cur.execute("DELETE FROM users WHERE username NOT IN ('test.admin', 'test.analyst', 'test.employee') AND username NOT LIKE 'user_%';")
        conn.commit()
        print("Database cleared successfully.")
    except Exception as e:
        conn.rollback()
        print(f"ERROR: Failed to clear old database tables: {e}")
        sys.exit(1)

    # Policy Rule ID maps from database seeding
    policy_rules = {
        "restrict": "a0e8140d-d684-4860-84c1-2ba6d934bb61",
        "require_mfa": "b5fbf104-e3f3-470b-85be-587265bf02ab",
        "allow": "c65d836d-1bf8-466c-be7d-78a05c317db6"
    }

    feature_cols = [
        "total_logins", "unique_login_pcs", "avg_login_hour", "off_hour_logins",
        "total_device_events", "unique_devices", "off_hour_device", "files_accessed",
        "unique_files", "unique_content", "off_hour_file", "files_per_login",
        "device_login_ratio", "off_hour_ratio"
    ]

    departments = ["Engineering", "DevOps", "Sales", "HR", "Finance", "Security"]

    total_scores_inserted = 0
    total_logs_inserted = 0

    # 6. Seed Target Users
    for username in target_users:
        # Deterministic UUID5 based on user string
        user_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, username))
        email = f"{username.lower()}@zt-enterprise.io"
        
        # Deterministic choices using string hashing as seed
        random.seed(username)
        dept = random.choice(departments)
        
        print(f"\nSeeding user: {username} | UUID: {user_uuid} | Dept: {dept}")
        
        # Insert User
        cur.execute("""
            INSERT INTO users (id, keycloak_sub, username, email, role, department, tenant_id)
            VALUES (%s, %s, %s, %s, 'employee', %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """, (user_uuid, user_uuid, username, email, dept, DEFAULT_TENANT_ID))

        # Insert Device for recent activity logs
        device_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{username}-device"))
        device_fingerprint = f"{username.lower()}-laptop-001"
        cur.execute("""
            INSERT INTO devices (id, user_id, device_fingerprint, os, is_known, tenant_id)
            VALUES (%s, %s, %s, 'Windows 11', true, %s)
            ON CONFLICT (id) DO NOTHING;
        """, (device_uuid, user_uuid, device_fingerprint, DEFAULT_TENANT_ID))

        # Filter user days
        user_df = df[df["user"] == username].copy().sort_values("day")
        num_days = len(user_df)
        print(f"  - Found {num_days} days of telemetry features.")

        # Compute rolling dates ending today
        end_time = datetime.utcnow()
        start_date = end_time - timedelta(days=num_days)

        # Iterate days
        day_rows = list(user_df.iterrows())
        for idx, (df_idx, row) in enumerate(day_rows):
            day_date = start_date + timedelta(days=idx)
            
            # Prepare feature DataFrame
            feature_dict = {col: float(row[col]) for col in feature_cols}
            df_row = pd.DataFrame([feature_dict], columns=feature_cols)

            # 1. Isolation Forest Anomaly Score
            d = float(if_model.decision_function(df_row)[0])
            anomaly_score = 1.0 / (1.0 + np.exp(10.0 * d))

            # 2. Random Forest Threat Probability
            probs = rf_model.predict_proba(df_row)[0]
            risk_probability = float(probs[1]) # Malicious class
            
            risk_class = "low"
            if risk_probability > 0.30:
                risk_class = "medium"
            if risk_probability > 0.60:
                risk_class = "high"

            # 3. Trust Score formula
            # 0.5 (medium) identity confidence baseline for general historical telemetry
            identity_confidence = 0.5
            trust_score = 100.0 * (
                0.4 * (1.0 - anomaly_score) +
                0.4 * (1.0 - risk_probability) +
                0.2 * identity_confidence
            )
            trust_score = max(0.0, min(100.0, trust_score))

            # 4. Explainable SHAP values
            sv_all = explainer.shap_values(df_row)
            if isinstance(sv_all, list):
                sv = sv_all[1][0]
            elif isinstance(sv_all, np.ndarray):
                if sv_all.ndim == 3:
                    sv = sv_all[0, :, 1] if sv_all.shape[0] != 2 else sv_all[1][0]
                else:
                    sv = sv_all[0]
            else:
                sv = sv_all[0]

            shap_list = []
            for col_name, val in zip(feature_cols, sv):
                shap_list.append({"feature": col_name, "shap_value": float(val)})
            top_5_shap = sorted(shap_list, key=lambda x: abs(x["shap_value"]), reverse=True)[:5]

            # 5. Insert ModelScore
            model_score_uuid = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO model_scores (id, access_log_id, anomaly_score, risk_class, risk_probability, shap_values, scored_at)
                VALUES (%s, NULL, %s, %s, %s, %s, %s);
            """, (model_score_uuid, anomaly_score, risk_class, risk_probability, json.dumps(top_5_shap), day_date))

            # 6. Insert TrustScore
            trust_score_uuid = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO trust_scores (id, user_id, trust_score, anomaly_component, risk_component, computed_at, model_score_id, tenant_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """, (trust_score_uuid, user_uuid, trust_score, 0.4 * (1.0 - anomaly_score), 0.4 * (1.0 - risk_probability), day_date, model_score_uuid, DEFAULT_TENANT_ID))

            # 7. Seed Policy Action Trigger & Alerts
            action = "allow"
            if trust_score < 40:
                action = "restrict"
            elif trust_score < 70:
                action = "require_mfa"

            if action in ("restrict", "require_mfa"):
                severity = "critical" if trust_score < 40 else "high" if trust_score < 60 else "medium"
                alert_uuid = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO alerts (id, trust_score_id, policy_rule_id, severity, status, created_at, tenant_id)
                    VALUES (%s, %s, %s, %s, 'open', %s, %s);
                """, (alert_uuid, trust_score_uuid, policy_rules[action], severity, day_date, DEFAULT_TENANT_ID))

            total_scores_inserted += 1

            # 8. For the final (latest) day, seed matching access logs so UI shows real telemetry
            if idx == num_days - 1:
                logins_count = int(row["total_logins"])
                files_count = int(row["files_accessed"])
                device_count = int(row["total_device_events"])

                last_log_uuid = None
                log_time = day_date - timedelta(hours=2)

                # Seed logins
                for l_idx in range(max(1, logins_count)):
                    log_uuid = str(uuid.uuid4())
                    cur.execute("""
                        INSERT INTO access_logs (id, user_id, device_id, event_type, resource, bytes_transferred, event_time, ip_address, location, tenant_id)
                        VALUES (%s, %s, %s, 'login', 'okta-auth', 0, %s, '10.0.1.55', 'Chicago, US', %s);
                    """, (log_uuid, user_uuid, device_uuid, log_time + timedelta(minutes=l_idx * 5), DEFAULT_TENANT_ID))
                    last_log_uuid = log_uuid
                    total_logs_inserted += 1

                # Seed file downloads
                for f_idx in range(files_count):
                    log_uuid = str(uuid.uuid4())
                    cur.execute("""
                        INSERT INTO access_logs (id, user_id, device_id, event_type, resource, bytes_transferred, event_time, ip_address, location, tenant_id)
                        VALUES (%s, %s, %s, 'file_download', 'repo-portal/src/index.js', 1048576, %s, '10.0.1.55', 'Chicago, US', %s);
                    """, (log_uuid, user_uuid, device_uuid, log_time + timedelta(minutes=f_idx * 3 + 10), DEFAULT_TENANT_ID))
                    last_log_uuid = log_uuid
                    total_logs_inserted += 1

                # Link final model_score to the last logged event
                if last_log_uuid:
                    cur.execute("""
                        UPDATE model_scores SET access_log_id = %s WHERE id = %s;
                    """, (last_log_uuid, model_score_uuid))

        print(f"  - Completed. Seeded {num_days} historical score days for {username}.")
        conn.commit()

    cur.close()
    conn.close()

    print("\n" + "=" * 60)
    print("DATABASE SEEDING COMPLETE!")
    print(f"  - Total Trust Score records inserted: {total_scores_inserted}")
    print(f"  - Total Access Log records inserted: {total_logs_inserted}")
    print("=" * 60)

if __name__ == "__main__":
    main()
