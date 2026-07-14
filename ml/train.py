"""
===========================================================
train.py

Train Random Forest (v3) and Isolation Forest (v3)
with 19 features (including rolling deviations & IF score).
Implements user-level train/validation split for threshold tuning
and saves split_users.json for test isolation.
===========================================================
"""

import os
import json
import joblib
import warnings
import numpy as np
import pandas as pd
import sklearn
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    f1_score,
)

warnings.filterwarnings("ignore")

print("=" * 60)
print("CERT R4.2 TRAINING PIPELINE (v3)")
print("=" * 60)

FEATURE_FILE = "ml/data/features_daily.parquet"
MODEL_DIR = "ml/models"
os.makedirs(MODEL_DIR, exist_ok=True)

# ---------------------------------------------------------
# 1. LOAD FEATURES
# ---------------------------------------------------------
print("\nLoading Features...")
df = pd.read_parquet(FEATURE_FILE)
print("Data Shape:", df.shape)

base_features = [
    "total_logins",
    "unique_login_pcs",
    "avg_login_hour",
    "off_hour_logins",
    "total_device_events",
    "unique_devices",
    "off_hour_device",
    "files_accessed",
    "unique_files",
    "unique_content",
    "off_hour_file",
    "files_per_login",
    "device_login_ratio",
    "off_hour_ratio",
    "dev_total_logins",
    "dev_files_accessed",
    "dev_total_device_events",
    "dev_off_hour_ratio"
]

# ---------------------------------------------------------
# 2. STRATIFIED USER-LEVEL SPLIT (FIX 0)
# ---------------------------------------------------------
print("\nCreating stratified user-level train/test split...")
insider_users = sorted(list(df.loc[df["risk_label"] == 1, "user"].unique()))
all_users = sorted(list(df["user"].unique()))
normal_users = sorted(list(set(all_users) - set(insider_users)))

train_insiders, test_insiders = train_test_split(insider_users, test_size=0.20, random_state=42)
train_normals, test_normals = train_test_split(normal_users, test_size=0.20, random_state=42)

train_users = list(set(train_insiders).union(train_normals))
test_users = list(set(test_insiders).union(test_normals))

print("\nUser Split Summary:")
print("Total Users   :", len(all_users))
print("Train Users   :", len(train_users), f"({len(train_insiders)} insiders, {len(train_normals)} normal)")
print("Test Users    :", len(test_users), f"({len(test_insiders)} insiders, {len(test_normals)} normal)")

# Save split_users.json
split_file = os.path.join(MODEL_DIR, "split_users.json")
with open(split_file, "w") as f:
    json.dump({
        "train_users": sorted(train_users),
        "test_users": sorted(test_users)
    }, f, indent=4)
print("split_users.json saved to:", split_file)

# ---------------------------------------------------------
# 3. CARVE VALIDATION SET FROM TRAINING USERS ONLY (IMPROVEMENT 3)
# ---------------------------------------------------------
print("\nCarving validation set from training users...")
final_train_insiders, val_insiders = train_test_split(train_insiders, test_size=0.20, random_state=42)
final_train_normals, val_normals = train_test_split(train_normals, test_size=0.20, random_state=42)

final_train_users = list(set(final_train_insiders).union(final_train_normals))
val_users = list(set(val_insiders).union(val_normals))

print("Final Train Users:", len(final_train_users), f"({len(final_train_insiders)} insiders, {len(final_train_normals)} normal)")
print("Val Users        :", len(val_users), f"({len(val_insiders)} insiders, {len(val_normals)} normal)")

train_df = df[df["user"].isin(final_train_users)].copy()
val_df = df[df["user"].isin(val_users)].copy()
test_df = df[df["user"].isin(test_users)].copy()

print(f"Rows -> Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")

# ---------------------------------------------------------
# 4. TRAINING ISOLATION FOREST
# ---------------------------------------------------------
print("\n" + "=" * 60)
print("TRAINING ISOLATION FOREST (v3)")
print("=" * 60)

# Train on normal training samples only
normal_train_df = train_df[train_df["risk_label"] == 0]
print("Normal training samples:", len(normal_train_df))

iso_model = IsolationForest(
    n_estimators=200,
    contamination="auto",
    random_state=42,
    n_jobs=-1
)
iso_model.fit(normal_train_df[base_features])
print("Isolation Forest trained successfully.")

# ---------------------------------------------------------
# 5. INTEGRATE HYBRID FEATURE (IMPROVEMENT 1)
# ---------------------------------------------------------
print("\nGenerating anomaly score feature (-decision_function)...")
train_df["anomaly_score"] = -iso_model.decision_function(train_df[base_features])
val_df["anomaly_score"] = -iso_model.decision_function(val_df[base_features])
test_df["anomaly_score"] = -iso_model.decision_function(test_df[base_features])

# Save isolation forest model
iso_model_path = os.path.join(MODEL_DIR, "isolation_forest_v3.pkl")
joblib.dump(iso_model, iso_model_path)
print("Isolation Forest v3 saved to:", iso_model_path)

# Update feature names to include anomaly_score
all_feature_columns = base_features + ["anomaly_score"]
feature_names_path = os.path.join(MODEL_DIR, "feature_names.json")
with open(feature_names_path, "w") as f:
    json.dump(all_feature_columns, f, indent=4)
print(f"feature_names.json ({len(all_feature_columns)} features) saved.")

# ---------------------------------------------------------
# 6. TRAINING RANDOM FOREST
# ---------------------------------------------------------
print("\n" + "=" * 60)
print("TRAINING RANDOM FOREST (v3)")
print("=" * 60)

rf_model = RandomForestClassifier(
    n_estimators=300,
    max_depth=12,
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)
rf_model.fit(train_df[all_feature_columns], train_df["risk_label"])
print("Random Forest v3 trained successfully.")

# Save random forest model
rf_model_path = os.path.join(MODEL_DIR, "random_forest_v3.pkl")
joblib.dump(rf_model, rf_model_path)
print("Random Forest v3 saved to:", rf_model_path)

# ---------------------------------------------------------
# 7. VALIDATION THRESHOLD TUNING (IMPROVEMENT 3)
# ---------------------------------------------------------
print("\nTuning operating threshold on validation set...")
val_probs = rf_model.predict_proba(val_df[all_feature_columns])[:, 1]

best_threshold = 0.5
best_f1 = -1.0
fpr_threshold = 1.0

thresholds = np.linspace(0.0, 1.0, 1001)
for th in thresholds:
    val_pred = (val_probs >= th).astype(int)
    f1 = f1_score(val_df["risk_label"], val_pred, zero_division=0)
    if f1 > best_f1:
        best_f1 = f1
        best_threshold = th
        
    tn, fp, fn, tp = confusion_matrix(val_df["risk_label"], val_pred, labels=[0, 1]).ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    if fpr <= 0.01:
        fpr_threshold = min(fpr_threshold, th)

print(f"Best Validation F1: {best_f1:.4f} at Threshold: {best_threshold:.4f}")
print(f"Threshold for Validation FPR <= 0.01: {fpr_threshold:.4f}")

# Save metrics config/meta
val_metrics = {
    "tuned_threshold": float(best_threshold),
    "fpr_01_threshold": float(fpr_threshold),
    "validation_best_f1": float(best_f1)
}

# Write meta json
meta_path = os.path.join(MODEL_DIR, "tuning_meta.json")
with open(meta_path, "w") as f:
    json.dump(val_metrics, f, indent=4)
print("Tuning metadata saved to:", meta_path)

print("\nFinished train.py successfully!")
print("=" * 60)
