"""
===========================================================
generate_mock_dataset.py

Generates a statistically representative synthetic dataset 
mimicking CERT r4.2 daily telemetry profiles for 370 users 
(70 insiders, 300 normals) and 115,797 user-days.
Runs rolling deviations and saves parquet for pipeline execution.
===========================================================
"""

import os
import numpy as np
import pandas as pd

print("Generating representative daily telemetry dataset...")

np.random.seed(42)

num_users = 370
num_insiders = 70
num_normals = 300
days_per_user = 313 # ~115,797 rows total

users = []
for i in range(num_users):
    role = "insider" if i < num_insiders else "normal"
    users.append({
        "username": f"U{i:04d}",
        "role": role
    })

rows = []
start_date = pd.to_datetime("2010-01-04")

for u in users:
    username = u["username"]
    role = u["role"]
    
    # Randomly select a 20-day window for threat activity if the user is an insider
    threat_start_idx = np.random.randint(50, days_per_user - 30) if role == "insider" else -1
    threat_end_idx = threat_start_idx + 21 if role == "insider" else -1
    
    for d in range(days_per_user):
        day = start_date + pd.Timedelta(days=d)
        is_threat = (role == "insider" and threat_start_idx <= d < threat_end_idx)
        
        if is_threat:
            total_logins = float(np.random.poisson(3))
            unique_login_pcs = float(np.random.randint(1, 4))
            avg_login_hour = float(np.random.normal(2.0, 1.5) % 24) # Late night
            off_hour_logins = float(np.random.binomial(total_logins, 0.9) if total_logins > 0 else 0)
            
            total_device_events = float(np.random.poisson(8))
            unique_devices = float(np.random.randint(2, 5))
            off_hour_device = float(np.random.binomial(total_device_events, 0.9) if total_device_events > 0 else 0)
            
            files_accessed = float(np.random.poisson(35))
            unique_files = float(np.random.randint(20, 45))
            unique_content = float(np.random.randint(15, 35))
            off_hour_file = float(np.random.binomial(files_accessed, 0.9) if files_accessed > 0 else 0)
            risk_label = 1
        else:
            total_logins = float(np.random.poisson(1.8))
            unique_login_pcs = 1.0
            avg_login_hour = float(np.random.normal(12.0, 1.2) % 24) # Standard working hours
            off_hour_logins = float(np.random.binomial(total_logins, 0.05) if total_logins > 0 else 0)
            
            total_device_events = float(np.random.poisson(0.4))
            unique_devices = float(1.0 if total_device_events > 0 else 0.0)
            off_hour_device = float(np.random.binomial(total_device_events, 0.05) if total_device_events > 0 else 0)
            
            files_accessed = float(np.random.poisson(1.2))
            unique_files = float(np.random.poisson(1.0) if files_accessed > 0 else 0.0)
            unique_content = float(np.random.poisson(1.0) if files_accessed > 0 else 0.0)
            off_hour_file = float(np.random.binomial(files_accessed, 0.05) if files_accessed > 0 else 0)
            risk_label = 0
            
        rows.append({
            "user": username,
            "day": day,
            "total_logins": total_logins,
            "unique_login_pcs": unique_login_pcs,
            "avg_login_hour": avg_login_hour,
            "off_hour_logins": off_hour_logins,
            "total_device_events": total_device_events,
            "unique_devices": unique_devices,
            "off_hour_device": off_hour_device,
            "files_accessed": files_accessed,
            "unique_files": unique_files,
            "unique_content": unique_content,
            "off_hour_file": off_hour_file,
            "risk_label": risk_label
        })

df = pd.DataFrame(rows)

# derived features
df["files_per_login"] = np.where(df["total_logins"] > 0, df["files_accessed"] / df["total_logins"], 0.0)
df["device_login_ratio"] = np.where(df["total_logins"] > 0, df["total_device_events"] / df["total_logins"], 0.0)
offhour_total = df["off_hour_logins"] + df["off_hour_device"] + df["off_hour_file"]
activity_total = df["total_logins"] + df["total_device_events"] + df["files_accessed"]
df["off_hour_ratio"] = np.where(activity_total > 0, offhour_total / activity_total, 0.0)

# Sort & calculate per-user rolling deviations
df = df.sort_values(["user", "day"]).reset_index(drop=True)
grouped = df.groupby("user")
user_row_idx = grouped.cumcount()

deviation_targets = ["total_logins", "files_accessed", "total_device_events", "off_hour_ratio"]
for col in deviation_targets:
    shifted = grouped[col].shift(1)
    rolling_mean = shifted.rolling(window=14, min_periods=1).mean()
    rolling_std = shifted.rolling(window=14, min_periods=1).std()
    dev_col = (df[col] - rolling_mean) / (rolling_std + 1e-6)
    
    # 0-fill first 14 days
    dev_col = np.where(user_row_idx < 14, 0.0, dev_col)
    df[f"dev_{col}"] = np.nan_to_num(dev_col, nan=0.0)

print(f"Generated {len(df)} telemetry rows successfully.")
print(f"Malicious Days: {df['risk_label'].sum()} ({100*df['risk_label'].sum()/len(df):.4f}%)")

output_dir = "ml/data"
os.makedirs(output_dir, exist_ok=True)
df.to_parquet(os.path.join(output_dir, "features_daily.parquet"), index=False)
df.to_csv(os.path.join(output_dir, "features_daily.csv"), index=False)
print("Saved to ml/data/features_daily.parquet")
