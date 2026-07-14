"""
===========================================================
evaluate.py

Evaluate Random Forest (v3) and Isolation Forest (v3)
on isolated test users only. Generates tables and 300 DPI
figures for the IEEE paper.
===========================================================
"""

import os
import json
import joblib
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_curve,
    precision_recall_curve,
    roc_auc_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.ensemble import RandomForestClassifier, IsolationForest

warnings.filterwarnings("ignore")

print("=" * 60)
print("CERT R4.2 EVALUATION PIPELINE (v3)")
print("=" * 60)

FEATURE_FILE = "ml/data/features_daily.parquet"
MODEL_DIR = "ml/models"
FIGURE_DIR = "docs/paper/figures"
os.makedirs(FIGURE_DIR, exist_ok=True)

# ---------------------------------------------------------
# 1. LOAD MODELS, FEATURE SPECS, AND ISOLATED USERS
# ---------------------------------------------------------
print("\nLoading models and split configs...")
split_file = os.path.join(MODEL_DIR, "split_users.json")
meta_file = os.path.join(MODEL_DIR, "tuning_meta.json")

if not os.path.exists(split_file) or not os.path.exists(meta_file):
    raise FileNotFoundError("Missing split_users.json or tuning_meta.json. Please run train.py first.")

with open(split_file, "r") as f:
    splits = json.load(f)
train_users = splits["train_users"]
test_users = splits["test_users"]

with open(meta_file, "r") as f:
    tuning_meta = json.load(f)
tuned_threshold = tuning_meta["tuned_threshold"]

iso_model = joblib.load(os.path.join(MODEL_DIR, "isolation_forest_v3.pkl"))
rf_model = joblib.load(os.path.join(MODEL_DIR, "random_forest_v3.pkl"))

with open(os.path.join(MODEL_DIR, "feature_names.json"), "r") as f:
    feature_columns = json.load(f)

# The base features do not include anomaly_score
base_features = [f for f in feature_columns if f != "anomaly_score"]

# ---------------------------------------------------------
# 2. LOAD DATASET AND PARTITION
# ---------------------------------------------------------
df = pd.read_parquet(FEATURE_FILE)
train_df = df[df["user"].isin(train_users)].copy()
test_df = df[df["user"].isin(test_users)].copy()

print(f"Data partitioning loaded: Train rows={len(train_df)} | Test rows={len(test_df)}")

# Generate anomaly score feature on test set (must match training pipeline)
test_df["anomaly_score"] = -iso_model.decision_function(test_df[base_features])

X_test = test_df[feature_columns]
y_test = test_df["risk_label"]

# Predict probabilities and classes
test_probs = rf_model.predict_proba(X_test)[:, 1]
test_preds_05 = (test_probs >= 0.5).astype(int)
test_preds_tuned = (test_probs >= tuned_threshold).astype(int)

# ---------------------------------------------------------
# a) DATASET SUMMARY TABLE
# ---------------------------------------------------------
print("\nGenerating Dataset Summary Table...")
train_insiders = train_df[train_df["risk_label"] == 1]["user"].nunique()
train_normals = train_df["user"].nunique() - train_insiders
test_insiders = test_df[test_df["risk_label"] == 1]["user"].nunique()
test_normals = test_df["user"].nunique() - test_insiders

dataset_summary = f"""
### Dataset Partitioning Summary

| Split | Users (Insiders/Normal) | User-Days (Insiders/Normal) | Class Ratio (% Malicious Days) |
| :--- | :--- | :--- | :--- |
| **Train** | {train_df['user'].nunique()} ({train_insiders}/{train_normals}) | {len(train_df)} ({train_df['risk_label'].sum()}/{len(train_df)-train_df['risk_label'].sum()}) | {100*train_df['risk_label'].sum()/len(train_df):.4f}% |
| **Test**  | {test_df['user'].nunique()} ({test_insiders}/{test_normals}) | {len(test_df)} ({test_df['risk_label'].sum()}/{len(test_df)-test_df['risk_label'].sum()}) | {100*test_df['risk_label'].sum()/len(test_df):.4f}% |
"""
print(dataset_summary)

# ---------------------------------------------------------
# COMPILATION OF PERFORMANCE METRICS (v2 vs v3 COMPARISON)
# ---------------------------------------------------------
# Compute metrics for v3
rf_v3_auc = roc_auc_score(y_test, test_probs)

def get_metrics_for_pred(preds, probs):
    prec = precision_score(y_test, preds, zero_division=0)
    rec = recall_score(y_test, preds, zero_division=0)
    f1_insider = f1_score(y_test, preds, zero_division=0)
    f1_macro = f1_score(y_test, preds, average="macro", zero_division=0)
    auc = roc_auc_score(y_test, probs)
    return auc, prec, rec, f1_insider, f1_macro

metrics_v3_05 = get_metrics_for_pred(test_preds_05, test_probs)
metrics_v3_tuned = get_metrics_for_pred(test_preds_tuned, test_probs)
if_v3_auc = roc_auc_score(y_test, test_df["anomaly_score"])

v2_vs_v3_table = f"""
### Model Comparison Table (v2 vs v3)

| Model Split | Threshold | ROC-AUC | Precision | Recall | F1-Insider | F1-Macro |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Random Forest v2 (Baseline)** | 0.50 | 0.8943 | 0.1083 | 0.7535 | 0.1894 | 0.5727 |
| **Isolation Forest v2 (Baseline)**| N/A | 0.7777 | N/A | N/A | N/A | N/A |
| **Random Forest v3 (Augmented)** | 0.50 | {metrics_v3_05[0]:.4f} | {metrics_v3_05[1]:.4f} | {metrics_v3_05[2]:.4f} | {metrics_v3_05[3]:.4f} | {metrics_v3_05[4]:.4f} |
| **Random Forest v3 (Augmented)** | {tuned_threshold:.4f} (Tuned) | {metrics_v3_tuned[0]:.4f} | {metrics_v3_tuned[1]:.4f} | {metrics_v3_tuned[2]:.4f} | {metrics_v3_tuned[3]:.4f} | {metrics_v3_tuned[4]:.4f} |
| **Isolation Forest v3** | N/A | {if_v3_auc:.4f} | N/A | N/A | N/A | N/A |
"""
print(v2_vs_v3_table)

# ---------------------------------------------------------
# b) CONFUSION MATRIX
# ---------------------------------------------------------
print("\nPlotting confusion matrix...")
cm = confusion_matrix(y_test, test_preds_tuned)
cm_norm = confusion_matrix(y_test, test_preds_tuned, normalize='true')

fig, ax = plt.subplots(figsize=(5, 4), dpi=300)
labels = [f"{val}\n({norm:.2%})" for val, norm in zip(cm.flatten(), cm_norm.flatten())]
labels = np.asarray(labels).reshape(2, 2)
sns.heatmap(cm, annot=labels, fmt="", cmap="Blues", cbar=True,
            xticklabels=["Normal", "Threat"], yticklabels=["Normal", "Threat"], ax=ax)
ax.set_title(f"Confusion Matrix (Threshold: {tuned_threshold:.4f})")
ax.set_ylabel("True Category")
ax.set_xlabel("Predicted Category")
plt.tight_layout()
plt.savefig(os.path.join(FIGURE_DIR, "confusion_matrix.png"), dpi=300)
plt.close()

# ---------------------------------------------------------
# c) ROC CURVES (RF-v3 vs IF)
# ---------------------------------------------------------
print("\nPlotting ROC curves...")
fpr_rf, tpr_rf, _ = roc_curve(y_test, test_probs)
fpr_if, tpr_if, _ = roc_curve(y_test, test_df["anomaly_score"])

plt.figure(figsize=(6, 5), dpi=300)
plt.plot(fpr_rf, tpr_rf, label=f"RF-v3 (AUC = {rf_v3_auc:.4f})", color="darkblue", lw=2)
plt.plot(fpr_if, tpr_if, label=f"IF-v3 (AUC = {if_v3_auc:.4f})", color="orange", linestyle="--", lw=1.5)
plt.plot([0, 1], [0, 1], color="gray", linestyle=":", lw=1)
plt.xlim([-0.02, 1.02])
plt.ylim([-0.02, 1.02])
plt.xlabel("False Positive Rate (FPR)")
plt.ylabel("True Positive Rate (TPR)")
plt.title("ROC Curves Comparison")
plt.legend(loc="lower right")
plt.grid(True, linestyle=":", alpha=0.6)
plt.tight_layout()
plt.savefig(os.path.join(FIGURE_DIR, "roc_curves.png"), dpi=300)
plt.close()

# ---------------------------------------------------------
# d) PRECISION-RECALL CURVE
# ---------------------------------------------------------
print("\nPlotting Precision-Recall curve...")
precision, recall, thresholds_pr = precision_recall_curve(y_test, test_probs)

# Find precision and recall at operating point
op_precision = precision_score(y_test, test_preds_tuned, zero_division=0)
op_recall = recall_score(y_test, test_preds_tuned, zero_division=0)

plt.figure(figsize=(6, 5), dpi=300)
plt.plot(recall, precision, label="Precision-Recall Curve", color="teal", lw=2)
plt.scatter(op_recall, op_precision, color="red", s=100, zorder=5,
            label=f"Operating Point (Th={tuned_threshold:.3f}\nPrec={op_precision:.3f}, Rec={op_recall:.3f})")
plt.xlabel("Recall")
plt.ylabel("Precision")
plt.title("Precision-Recall Curve with Operating Point")
plt.xlim([-0.02, 1.02])
plt.ylim([-0.02, 1.02])
plt.legend(loc="upper right")
plt.grid(True, linestyle=":", alpha=0.6)
plt.tight_layout()
plt.savefig(os.path.join(FIGURE_DIR, "precision_recall_curve.png"), dpi=300)
plt.close()

# ---------------------------------------------------------
# e) PRECISION@K / RECALL@K (ANALYST TRIAGE)
# ---------------------------------------------------------
print("\nComputing Precision@K / Recall@K triage metrics...")
# Sort test rows by RF probability descending
sort_idx = np.argsort(test_probs)[::-1]
y_test_sorted = y_test.iloc[sort_idx].values
total_positives = y_test.sum()

triage_results = []
for k in [50, 100, 200]:
    tp_k = y_test_sorted[:k].sum()
    prec_k = tp_k / k
    rec_k = tp_k / total_positives
    triage_results.append((k, prec_k, rec_k))

triage_table = """
### Analyst Triage Metrics (Top-K)

| Rank Threshold (K) | Precision@K | Recall@K | True Positives Detected |
| :--- | :--- | :--- | :--- |
"""
for k, pk, rk in triage_results:
    triage_table += f"| Top-{k} | {pk:.4f} | {rk:.4f} | {int(pk*k)} / {total_positives} |\n"
print(triage_table)

# Plot Precision@K / Recall@K
plt.figure(figsize=(6, 5), dpi=300)
ks = list(range(1, min(1000, len(y_test) + 1)))
p_at_k = [y_test_sorted[:k].sum() / k for k in ks]
r_at_k = [y_test_sorted[:k].sum() / total_positives for k in ks]

plt.plot(ks, p_at_k, label="Precision@K", color="navy")
plt.plot(ks, r_at_k, label="Recall@K", color="forestgreen", linestyle="--")
plt.xlabel("Number of Telemetry Daily Instances Reviewed (K)")
plt.ylabel("Metric Score")
plt.title("Precision@K and Recall@K Triage Analysis")
plt.legend()
plt.grid(True, linestyle=":", alpha=0.6)
plt.tight_layout()
plt.savefig(os.path.join(FIGURE_DIR, "triage_precision_recall_k.png"), dpi=300)
plt.close()

# ---------------------------------------------------------
# f) SHAP EXPLAINABILITY (FALLBACK SUPPORTED)
# ---------------------------------------------------------
print("\nExtracting SHAP explainability values...")
has_shap = False
shap_vals = None
shap_importance = {}

try:
    import shap
    explainer = shap.TreeExplainer(rf_model)
    shap_vals = explainer.shap_values(X_test)
    
    # Extract shap values corresponding to class 1
    if isinstance(shap_vals, list):
        shap_vals_class1 = shap_vals[1]
    elif len(shap_vals.shape) == 3:
        shap_vals_class1 = shap_vals[:, :, 1]
    else:
        shap_vals_class1 = shap_vals
        
    has_shap = True
    print("SHAP values calculated successfully.")
    
    # Plot SHAP summary/beeswarm
    plt.figure(figsize=(8, 6), dpi=300)
    shap.summary_plot(shap_vals_class1, X_test, show=False)
    plt.title("SHAP Beeswarm Plot (Insiders Class)", fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURE_DIR, "shap_beeswarm.png"), dpi=300)
    plt.close()
    
    # Compute mean |SHAP| values
    mean_shaps = np.mean(np.abs(shap_vals_class1), axis=0)
    for feat, val in zip(feature_columns, mean_shaps):
        shap_importance[feat] = val
        
except Exception as e:
    print("SHAP explainability libraries missing or errored. Generating fallback Gini Importance plots:", e)
    # Generate feature importance bar chart as fallback
    importances = rf_model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    plt.figure(figsize=(8, 6), dpi=300)
    plt.barh(range(len(feature_columns)), importances[indices[::-1]], align="center", color="teal")
    plt.yticks(range(len(feature_columns)), [feature_columns[i] for i in indices[::-1]])
    plt.xlabel("Mean Gini Feature Importance")
    plt.title("Feature Importance Ablation (Fallback)")
    plt.tight_layout()
    plt.savefig(os.path.join(FIGURE_DIR, "shap_beeswarm.png"), dpi=300)
    plt.close()
    
    for feat, val in zip(feature_columns, importances):
        shap_importance[feat] = val

sorted_shap = sorted(shap_importance.items(), key=lambda x: x[1], reverse=True)[:10]
shap_table = """
### Top 10 Feature Importance Table

| Rank | Feature Name | Mean Attribute Contribution |
| :--- | :--- | :--- |
"""
for idx, (feat, val) in enumerate(sorted_shap, 1):
    shap_table += f"| {idx} | `{feat}` | {val:.6f} |\n"
print(shap_table)

# ---------------------------------------------------------
# g) TRUST SCORE DISTRIBUTION BY LABEL
# ---------------------------------------------------------
print("\nEvaluating trust score distribution...")
# decision_function is from Isolation Forest
decision_func = iso_model.decision_function(X_test[base_features])
anom01 = 1.0 / (1.0 + np.exp(10.0 * decision_func))
# risk probability from Random Forest
prob = rf_model.predict_proba(X_test)[:, 1]

# TrustScore = 100 * (0.4 * (1 - anom01) + 0.4 * (1 - prob) + 0.2 * 0.5)
trust_scores = 100.0 * (0.4 * (1.0 - anom01) + 0.4 * (1.0 - prob) + 0.1)
test_df["trust_score"] = trust_scores

# ROC-AUC of Trust Score (lower score = higher risk, so we evaluate threat score: 100 - trust_score)
trust_auc = roc_auc_score(y_test, 100.0 - trust_scores)
print(f"Trust Score ROC-AUC: {trust_auc:.4f}")

plt.figure(figsize=(7, 4.5), dpi=300)
sns.kdeplot(data=test_df[test_df["risk_label"] == 0], x="trust_score", fill=True, color="forestgreen", label="Normal User-Days", alpha=0.4)
sns.kdeplot(data=test_df[test_df["risk_label"] == 1], x="trust_score", fill=True, color="crimson", label="Insider Threat Days", alpha=0.4)
plt.axvline(x=40, color="red", linestyle="--", label="Critical Threshold (40)")
plt.axvline(x=70, color="orange", linestyle=":", label="Warning Threshold (70)")
plt.xlabel("Zero Trust Compliance Score (0-100)")
plt.ylabel("Density")
plt.title("Trust Score Distribution by Ground-Truth Label")
plt.legend()
plt.grid(True, linestyle=":", alpha=0.6)
plt.tight_layout()
plt.savefig(os.path.join(FIGURE_DIR, "trust_score_distribution.png"), dpi=300)
plt.close()

# ---------------------------------------------------------
# h) WEIGHT SENSITIVITY TABLE
# ---------------------------------------------------------
print("\nRunning Weight Sensitivity tests...")
weights_scenarios = [
    (0.4, 0.4, 0.2),
    (0.5, 0.3, 0.2),
    (0.3, 0.5, 0.2),
    (0.5, 0.5, 0.0),
    (0.33, 0.33, 0.34)
]

sensitivity_rows = []
for w1, w2, w3 in weights_scenarios:
    sc = 100.0 * (w1 * (1.0 - anom01) + w2 * (1.0 - prob) + w3 * 0.5)
    auc_val = roc_auc_score(y_test, 100.0 - sc)
    below_40 = np.mean(sc < 40) * 100.0
    below_70 = np.mean(sc < 70) * 100.0
    sensitivity_rows.append((w1, w2, w3, auc_val, below_40, below_70))

sensitivity_table = """
### Weight Sensitivity Analysis

| Scenario (IF/RF/Prior) | Trust ROC-AUC | % Days Below 40 (Warning) | % Days Below 70 (Restrict) |
| :--- | :--- | :--- | :--- |
"""
for w1, w2, w3, auc_val, b40, b70 in sensitivity_rows:
    sensitivity_table += f"| {w1:.2f} / {w2:.2f} / {w3:.2f} | {auc_val:.4f} | {b40:.2f}% | {b70:.2f}% |\n"
print(sensitivity_table)

# ---------------------------------------------------------
# i) OFF-HOURS ABLATION STUDY
# ---------------------------------------------------------
print("\nRunning off-hours features ablation study...")
# Base features to drop
offhour_features = ["off_hour_logins", "off_hour_device", "off_hour_file", "off_hour_ratio", "dev_off_hour_ratio"]
ablated_base = [f for f in base_features if f not in offhour_features]

# Retrain IF on ablated features
X_train_normal_ablated = train_df[train_df["risk_label"] == 0][ablated_base]
iso_ablated = IsolationForest(
    n_estimators=200,
    contamination="auto",
    random_state=42,
    n_jobs=-1
)
iso_ablated.fit(X_train_normal_ablated)

# Generate ablated anomaly score
train_df["anomaly_score_ablated"] = -iso_ablated.decision_function(train_df[ablated_base])
test_df["anomaly_score_ablated"] = -iso_ablated.decision_function(test_df[ablated_base])

ablated_all_features = ablated_base + ["anomaly_score_ablated"]

# Train RF
rf_ablated = RandomForestClassifier(
    n_estimators=300,
    max_depth=12,
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)
rf_ablated.fit(train_df[ablated_all_features], train_df["risk_label"])

# Evaluate
test_probs_ablated = rf_ablated.predict_proba(test_df[ablated_all_features])[:, 1]
test_preds_ablated = (test_probs_ablated >= tuned_threshold).astype(int)

auc_abl, prec_abl, rec_abl, f1_ins_abl, f1_mac_abl = get_metrics_for_pred(test_preds_ablated, test_probs_ablated)

delta_auc = rf_v3_auc - auc_abl
delta_f1 = metrics_v3_tuned[3] - f1_ins_abl

ablation_table = f"""
### Off-Hours Features Ablation Study

| Model Config | ROC-AUC | F1-Insider | Delta ROC-AUC | Delta F1-Insider |
| :--- | :--- | :--- | :--- | :--- |
| **Random Forest v3 (Tuned)** | {rf_v3_auc:.4f} | {metrics_v3_tuned[3]:.4f} | -- | -- |
| **Ablated (No Off-Hour Features)** | {auc_abl:.4f} | {f1_ins_abl:.4f} | {delta_auc:+.4f} | {delta_f1:+.4f} |
"""
print(ablation_table)

# ---------------------------------------------------------
# WRITE ALL TABLES TO results-template.md
# ---------------------------------------------------------
template_content = f"""# IEEE Insider Threat Detection Evaluation Report (v3)

This artifact contains the performance reports and configuration metrics for the CERT r4.2 Zero Trust Security Model.

{dataset_summary}

---

{v2_vs_v3_table}

---

{triage_table}

---

{shap_table}

---

{sensitivity_table}

---

{ablation_table}
"""

with open("results-template.md", "w") as f:
    f.write(template_content)
print("\nresults-template.md generated successfully.")

# Save evaluation results to metrics.json
metrics_results = {
    "random_forest_v3_tuned": {
        "roc_auc": float(metrics_v3_tuned[0]),
        "precision": float(metrics_v3_tuned[1]),
        "recall": float(metrics_v3_tuned[2]),
        "f1_score": float(metrics_v3_tuned[3]),
        "f1_macro": float(metrics_v3_tuned[4]),
        "threshold": float(tuned_threshold)
    },
    "isolation_forest_v3": {
        "roc_auc": float(if_v3_auc)
    },
    "trust_score": {
        "roc_auc": float(trust_auc)
    },
    "ablation_study": {
        "roc_auc_delta": float(delta_auc),
        "f1_score_delta": float(delta_f1)
    }
}
with open(os.path.join(MODEL_DIR, "metrics.json"), "w") as f:
    json.dump(metrics_results, f, indent=4)
print("metrics.json saved successfully to:", os.path.join(MODEL_DIR, "metrics.json"))

print("\nEvaluation Pipeline Completed Successfully!")
print("=" * 60)
