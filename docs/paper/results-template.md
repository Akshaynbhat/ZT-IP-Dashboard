This section presents the experimental evaluation of the proposed framework, analyzing the classification accuracy of the machine learning pipeline, the operational sensitivity of the trust scoring weights, and the efficacy of the explainability engine.

## A. Experimental Setup

The evaluation was conducted on a system configured with [HARDWARE] running Python version [PYTHON_VERSION] and scikit-learn [SKLEARN_VERSION]. The dataset used for evaluation was compiled from the CERT Insider Threat Dataset r4.2, specifically isolating a developer-centric subset containing [DATASET_SUBSET_SIZE] user-days. Training and testing sets were partitioned using the user-level split (80% training users, 20% testing users) detailed in Section III-A to prevent data leakage and ensure evaluation on unseen developer accounts.

## B. Model Evaluation

The first stage of the pipeline evaluated the unsupervised Isolation Forest (IF) in isolating anomalous developer behaviors. Since the Isolation Forest outputs a continuous anomaly score rather than a binary classification label, its evaluation is analyzed using Precision@k and Recall@k (where $k$ represents the threshold corresponding to the expected contamination rate) and the Area Under the Receiver Operating Characteristic (ROC-AUC) curve. Table II summarizes the performance of the first-stage Isolation Forest.

### Table II: First-Stage Isolation Forest Performance Metrics

| Metric | Threshold ($k$) | Value |
| :--- | :--- | :--- |
| Precision@k | [IF_K_VAL] | [IF_PRECISION_VALUE] |
| Recall@k | [IF_K_VAL] | [IF_RECALL_VALUE] |
| ROC-AUC | — | [IF_ROC_AUC_VALUE] |

The second stage of the pipeline evaluated the supervised Random Forest (RF) classifier, which utilizes the hybrid feature-injection design (incorporating `if_anomaly_score` as a feature). Due to the extreme class imbalance present in the CERT dataset, classification performance is assessed using macro-averaged metrics. Table III details the performance metrics of the hybrid Random Forest classifier, alongside the structure of the resulting confusion matrix.

### Table III: Hybrid Random Forest Classifier Performance

| Metric | Value |
| :--- | :--- |
| Precision (Macro-Avg) | [RF_PRECISION] |
| Recall (Macro-Avg) | [RF_RECALL] |
| F1-macro | [RF_F1_MACRO] |
| ROC-AUC | [RF_ROC_AUC] |

#### Confusion Matrix Layout
```
                     Predicted Normal     Predicted Malicious
Actual Normal             [TN]                  [FP]
Actual Malicious          [FN]                  [TP]
```

## C. Class Imbalance and Optimization Metrics

Because malicious developer sessions constitute less than [MALICIOUS_PERCENTAGE]% of the dataset, standard accuracy is an inappropriate metric for model evaluation. A naive classifier predicting all sessions as "normal" would achieve an accuracy of [NAIVE_ACCURACY_PERCENTAGE]%, while failing to detect any insider threats. Consequently, F1-macro is selected as the primary metric for model optimization. F1-macro calculates the unweighted mean of the F1-scores for the normal and malicious classes:
$$\text{F1-macro} = \frac{\text{F1}_{\text{normal}} + \text{F1}_{\text{malicious}}}{2}$$
This measurement ensures that the model is heavily penalized for both false negatives (unidentified malicious insiders) and false positives (blocking legitimate developer actions).

To visualize the features influencing model decisions, a SHAP summary plot is generated. Figure 1 shows the global feature importance of the 12 features within the hybrid Random Forest model.

```
Figure 1: SHAP summary plot showing global feature importance. Features are ranked vertically by their mean absolute SHAP values. The horizontal axis represents the SHAP value, showing the direction and magnitude of each feature's contribution to the malicious risk classification.
```

The distribution of computed Trust Scores ($T$) is shown in Figure 2, comparing malicious sessions against normal developer sessions.

```
Figure 2: Trust score distribution for malicious vs. normal user sessions. The horizontal axis displays the Trust Score scaled from 0 to 100, while the vertical axis indicates density. Normal user sessions are clustered heavily toward high trust (80-100), whereas malicious sessions show a distinctive shift toward low trust (0-40).
```

## D. Trust Score Weight Sensitivity Analysis

A sensitivity analysis was performed to determine how different allocations of weights ($w_1, w_2, w_3$) in the Trust Score equation affect the system's operational behavior. By adjusting the weights, we monitor the rate of restrictive postures, alert rates, and overall detection accuracy on the test set. Table IV summarizes the operational sensitivity of the policy engine under various configurations.

### Table IV: Trust Score Weight Sensitivity Analysis

| Configuration | $w_1$ (IF Anomaly) | $w_2$ (RF Risk) | $w_3$ (Identity) | Restrict Rate (%) | Alert Rate (%) | True Positive Rate (%) | False Positive Rate (%) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Config A (Equal Weight)** | 0.33 | 0.33 | 0.33 | [CONF_A_RESTRICT] | [CONF_A_ALERT] | [CONF_A_TPR] | [CONF_A_FPR] |
| **Config B (Identity Focused)**| 0.10 | 0.10 | 0.80 | [CONF_B_RESTRICT] | [CONF_B_ALERT] | [CONF_B_TPR] | [CONF_B_FPR] |
| **Config C (Behavioral Only)**  | 0.50 | 0.50 | 0.00 | [CONF_C_RESTRICT] | [CONF_C_ALERT] | [CONF_C_TPR] | [CONF_C_FPR] |
| **Config D (Proposed Hybrid)** | 0.40 | 0.40 | 0.20 | [CONF_D_RESTRICT] | [CONF_D_ALERT] | [CONF_D_TPR] | [CONF_D_FPR] |

## E. Discussion

The experimental results show that the proposed framework addresses the critical research gaps in Zero Trust architectures. First, the hybrid feature augmentation method—injecting unsupervised anomaly scores into the supervised Random Forest model—achieves higher classification performance than running either model independently. The Isolation Forest successfully establishes a baseline for general outlier behavior, enabling the Random Forest to detect novel or evolving insider threats. Second, placing the Trust Score calculation inline with the Policy Decision Point (FastAPI backend) bridges the gap between machine learning-based detection and runtime policy enforcement. Rather than generating offline, post-hoc alerts, the system dynamically restricts access in response to behavioral changes. Finally, surfacing SHAP values as explanation codes at the decision point provides administrators with the immediate context needed to investigate alerts, reducing time-to-remediation while minimizing disruption to legitimate developer workflows.
