"""
===========================================================
build_features.py

Build per-user-per-day features for CERT R4.2
Ground truth labels come ONLY from insiders.csv
===========================================================
"""

import os
import json
import random
import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ----------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------

logon_path = "logon.csv"
device_path = "device.csv"
file_path = "file.csv"
insiders_path = "insiders.csv"

print("=" * 60)
print("CERT R4.2 FEATURE BUILD PIPELINE")
print("=" * 60)

print("\nLoading datasets...")
logon = pd.read_csv(logon_path)
device = pd.read_csv(device_path)
file_data = pd.read_csv(file_path)
insiders = pd.read_csv(insiders_path)

print("Datasets Loaded Successfully!\n")
print("Logon :", logon.shape)
print("Device:", device.shape)
print("File  :", file_data.shape)
print("Insiders:", insiders.shape)

OUTPUT_DIR = "ml/data"
RANDOM_STATE = 42
NORMAL_SAMPLE_USERS = 300

np.random.seed(RANDOM_STATE)
random.seed(RANDOM_STATE)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ----------------------------------------------------------
# KEEP ONLY CERT R4.2 INSIDERS
# ----------------------------------------------------------
insiders = insiders[insiders["dataset"] == 4.2].copy()
print("\nCERT R4.2 Insider Users:", insiders["user"].nunique())

# ----------------------------------------------------------
# DATE CONVERSION
# ----------------------------------------------------------
print("\nParsing timestamps...")
logon["date"] = pd.to_datetime(logon["date"], format="%m/%d/%Y %H:%M:%S", errors="coerce")
device["date"] = pd.to_datetime(device["date"], format="%m/%d/%Y %H:%M:%S", errors="coerce")
file_data["date"] = pd.to_datetime(file_data["date"], format="%m/%d/%Y %H:%M:%S", errors="coerce")
insiders["start"] = pd.to_datetime(insiders["start"], errors="coerce")
insiders["end"] = pd.to_datetime(insiders["end"], errors="coerce")
print("Timestamp conversion completed.")

# ----------------------------------------------------------
# REMOVE BAD ROWS
# ----------------------------------------------------------
logon = logon.dropna(subset=["date", "user"])
device = device.dropna(subset=["date", "user"])
file_data = file_data.dropna(subset=["date", "user"])

# ----------------------------------------------------------
# EXTRACT DATE + HOUR
# ----------------------------------------------------------
for df in [logon, device, file_data]:
    df["day"] = df["date"].dt.date
    df["hour"] = df["date"].dt.hour

# ----------------------------------------------------------
# OFF HOURS DEFINITION
# ----------------------------------------------------------
def off_hour(hour):
    return int(hour >= 20 or hour < 6)

logon["off_hour"] = logon["hour"].apply(off_hour)
device["off_hour"] = device["hour"].apply(off_hour)
file_data["off_hour"] = file_data["hour"].apply(off_hour)

# ----------------------------------------------------------
# KEEP ONLY REQUIRED EVENTS
# ----------------------------------------------------------
logon = logon[logon["activity"].isin(["Logon", "Logoff"])]
device = device[device["activity"].isin(["Connect", "Disconnect"])]

print("\nData Ready")
print("Logon Rows :", len(logon))
print("Device Rows:", len(device))
print("File Rows  :", len(file_data))

print("\nDate Range")
print(logon["date"].min(), "->", logon["date"].max())

# ==========================================================
# BUILD DAILY LOGIN FEATURES
# ==========================================================
print("\nBuilding Login Features...")
login_daily = (
    logon.groupby(["user", "day"])
    .agg(
        total_logins=("activity", "count"),
        unique_login_pcs=("pc", "nunique"),
        avg_login_hour=("hour", "mean"),
        off_hour_logins=("off_hour", "sum"),
    )
    .reset_index()
)
print("Login feature rows :", len(login_daily))

# ==========================================================
# BUILD DAILY DEVICE FEATURES
# ==========================================================
print("\nBuilding Device Features...")
device_daily = (
    device.groupby(["user", "day"])
    .agg(
        total_device_events=("activity", "count"),
        unique_devices=("pc", "nunique"),
        off_hour_device=("off_hour", "sum"),
    )
    .reset_index()
)
print("Device feature rows :", len(device_daily))

# ==========================================================
# BUILD DAILY FILE FEATURES
# ==========================================================
print("\nBuilding File Features...")
file_daily = (
    file_data.groupby(["user", "day"])
    .agg(
        files_accessed=("filename", "count"),
        unique_files=("filename", "nunique"),
        unique_content=("content", "nunique"),
        off_hour_file=("off_hour", "sum"),
    )
    .reset_index()
)
print("File feature rows :", len(file_daily))

# ==========================================================
# MERGE ALL DAILY FEATURES
# ==========================================================
print("\nMerging Daily Features...")
features = login_daily.merge(device_daily, on=["user", "day"], how="outer")
features = features.merge(file_daily, on=["user", "day"], how="outer")
print("Merged rows :", len(features))

# ==========================================================
# REPLACE MISSING VALUES WITH 0
# ==========================================================
numeric_columns = [
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
]
for column in numeric_columns:
    features[column] = features[column].fillna(0)

# ==========================================================
# DERIVED FEATURES
# ==========================================================
print("\nCreating Derived Features...")
features["files_per_login"] = np.where(
    features["total_logins"] > 0,
    features["files_accessed"] / features["total_logins"],
    0,
)
features["device_login_ratio"] = np.where(
    features["total_logins"] > 0,
    features["total_device_events"] / features["total_logins"],
    0,
)
offhour_total = (
    features["off_hour_logins"]
    + features["off_hour_device"]
    + features["off_hour_file"]
)
activity_total = (
    features["total_logins"]
    + features["total_device_events"]
    + features["files_accessed"]
)
features["off_hour_ratio"] = np.where(
    activity_total > 0,
    offhour_total / activity_total,
    0,
)
print("\nDerived Features Completed")

# ==========================================================
# IMPROVEMENT 2: PER-USER ROLLING DEVIATION FEATURES
# ==========================================================
print("\nAdding per-user rolling deviation features...")
features = features.sort_values(["user", "day"]).reset_index(drop=True)
grouped = features.groupby("user")
user_row_idx = grouped.cumcount()

deviation_targets = ["total_logins", "files_accessed", "total_device_events", "off_hour_ratio"]
for col in deviation_targets:
    # 14-day trailing per-user baseline (shifted by 1 day to prevent leakage of today's value)
    shifted = grouped[col].shift(1)
    rolling_mean = shifted.rolling(window=14, min_periods=1).mean()
    rolling_std = shifted.rolling(window=14, min_periods=1).std()
    
    # dev_X = (X - rolling_mean) / (rolling_std + 1e-6)
    dev_col = (features[col] - rolling_mean) / (rolling_std + 1e-6)
    
    # First 14 days per user: fill deviation with 0
    dev_col = np.where(user_row_idx < 14, 0.0, dev_col)
    
    # Fill remaining NaNs or Infs with 0.0
    dev_col = np.nan_to_num(dev_col, nan=0.0, posinf=0.0, neginf=0.0)
    
    features[f"dev_{col}"] = dev_col

print("Rolling deviation features completed.")

# ==========================================================
# FEATURE LIST DEFINITION
# ==========================================================
feature_columns = [
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
print("\nNumber of Base + Deviation Features:", len(feature_columns))
print(feature_columns)

# ==========================================================
# CREATE GROUND TRUTH LABELS FROM insiders.csv
# ==========================================================
print("\nCreating Ground Truth Labels...")
features["risk_label"] = 0
features["day"] = pd.to_datetime(features["day"])

insiders = insiders.dropna(subset=["user", "start", "end"])
insiders = insiders[insiders["dataset"] == 4.2].copy()
insiders["label_start"] = insiders["start"] - pd.Timedelta(days=1)
insiders["label_end"] = insiders["end"] + pd.Timedelta(days=1)

print("R4.2 Insider Users :", insiders["user"].nunique())

for _, insider in insiders.iterrows():
    user = insider["user"]
    start = insider["label_start"].normalize()
    end = insider["label_end"].normalize()
    mask = (
        (features["user"] == user)
        & (features["day"] >= start)
        & (features["day"] <= end)
    )
    features.loc[mask, "risk_label"] = 1

print("Ground Truth Labels Assigned")

# ==========================================================
# CLASS BALANCE
# ==========================================================
print("\nClass Distribution")
class_counts = features["risk_label"].value_counts().sort_index()
print(class_counts)

positive = int(features["risk_label"].sum())
negative = int(len(features) - positive)
print("\nNormal User-Days :", negative)
print("Insider User-Days:", positive)
print("Positive Ratio : {:.4f}%".format(100 * positive / len(features)))

# ==========================================================
# VERIFY INSIDER USERS
# ==========================================================
print("\nVerifying Labels...")
labelled_users = features.loc[features["risk_label"] == 1, "user"].unique()
print("Users labelled malicious :", len(labelled_users))

missing_users = set(insiders["user"]) - set(labelled_users)
if len(missing_users) == 0:
    print("All insider users successfully labelled.")
else:
    print("WARNING: These users were not found:")
    print(sorted(list(missing_users)))

# ==========================================================
# SAMPLE USERS
# Keep all insider users + 300 normal users
# ==========================================================
print("\nSampling Users...")
insider_users = set(insiders["user"].unique())
all_users = set(features["user"].unique())
normal_users = list(all_users - insider_users)

print("Total Users           :", len(all_users))
print("Insider Users         :", len(insider_users))
print("Available Normal Users:", len(normal_users))

sample_size = min(NORMAL_SAMPLE_USERS, len(normal_users))
sampled_normal_users = random.sample(normal_users, sample_size)
selected_users = insider_users.union(sampled_normal_users)

features = features[features["user"].isin(selected_users)].copy()
print("\nUsers after sampling :", features["user"].nunique())

# ==========================================================
# SORT DATA
# ==========================================================
features = features.sort_values(["user", "day"]).reset_index(drop=True)

# ==========================================================
# SAVE FEATURE NAMES AND DATASETS
# ==========================================================
print("\nFinal Dataset Summary")
print("Rows :", len(features))
print("Users:", features["user"].nunique())

parquet_file = os.path.join(OUTPUT_DIR, "features_daily.parquet")
features.to_parquet(parquet_file, index=False)
print("\nFeature dataset saved:", parquet_file)

csv_file = os.path.join(OUTPUT_DIR, "features_daily.csv")
features.to_csv(csv_file, index=False)
print("Feature CSV saved:", csv_file)

print("\nFinished Successfully!")
print("=" * 60)
