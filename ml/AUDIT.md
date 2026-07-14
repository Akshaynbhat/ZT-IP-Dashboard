# ZT-IP Machine Learning Integrity Audit Report

This document reports the findings of the Phase 1 Integrity Audit for the ZT-IP-Dashboard machine learning model evaluations on the CERT Insider Threat Dataset r4.2.

---

## 🔍 Phase 1: Integrity Audit Report

### 1. Split Methodology
*   **Result**: **FAIL (Missing Training Code)**
*   **Evidence**: A thorough inspection of all repository branches (including `feature/mounika-ml-model` and `feature/varshini-research`) reveals that the only ML script present is `ml/notebooks/exploration.iypnb`. This file contains basic Week 1 preprocessing checks (loading data, dropping nulls/duplicates, printing shapes) and does not contain training pipelines, model definitions, or data partitioning logic. Consequently, we cannot audit the split code to verify if the partition was user-level.

### 2. Balancing Isolation
*   **Result**: **FAIL (Missing Training Code)**
*   **Evidence**: Due to the absence of model training pipelines in the codebase, we cannot verify if class balancing (e.g., SMOTE, oversampling, or undersampling) was correctly isolated to the training set only and kept out of the validation/test partitions.

### 3. Test Composition & Arithmetic Reconciliation
*   **Result**: **PASS (Arithmetically Consistent)**
*   **Evidence**: The reported metrics ($Precision = 0.865$, $Recall = 0.880$, $FPR = 0.005$) reconcile arithmetically under a base class imbalance of $\sim 3.64\%$ malicious sessions.
    
    Let $N$ be the total normal sessions and $M$ be the total malicious sessions:
    $$\text{Recall} = \frac{TP}{M} = 0.880 \implies TP = 0.880 \cdot M$$
    $$\text{FPR} = \frac{FP}{N} = 0.005 \implies FP = 0.005 \cdot N$$
    $$\text{Precision} = \frac{TP}{TP + FP} = 0.865 \implies 0.135 \cdot TP = 0.865 \cdot FP$$
    
    Substituting $TP$ and $FP$:
    $$0.135 \cdot (0.880 \cdot M) = 0.865 \cdot (0.005 \cdot N)$$
    $$0.1188 \cdot M = 0.004325 \cdot N \implies \frac{M}{N} \approx 0.0364 \text{ (or } 3.64\%)$$
    
    This matches the expected malicious session base rate for a developer-centric CERT r4.2 subset. For instance, if the test set consists of $10,000$ normal sessions and $364$ malicious sessions:
    *   $TP = 320.32 \approx 320$
    *   $FN = 43.68 \approx 44$
    *   $FP = 50$
    *   $TN = 9,950$
    *   $\text{Precision} = \frac{320}{320 + 50} = 0.8648 \approx 0.865$
    *   $\text{Recall} = \frac{320}{364} = 0.8791 \approx 0.880$
    *   $\text{FPR} = \frac{50}{10000} = 0.005$

### 4. Validation vs. Test Sets
*   **Result**: **FAIL (Missing Training Code)**
*   **Evidence**: Due to the missing code, we cannot confirm whether the reported numbers are validation metrics used during hyperparameter tuning or scores obtained from a clean, held-out test partition.

---

## 🚫 Required to Unblock Phase 2

Phase 2 (generating final evaluation artifacts, confusion matrices, ROC curves, SHAP beeswarm plots, ablated models, and weight sensitivity analyses) is **BLOCKED** until the following dependencies are added to the repository:

1.  **Original Model Training Notebook/Script**: The complete training code used to fit the `final_isolation_forest.pkl` and `final_random_forest.pkl` models.
2.  **Dataset Assets & Preprocessing Code**: The exact preprocessed feature dataset used during training OR the raw data files + preprocessing scripts + the CERT answer-key ground-truth label merging logic.
3.  **Random Seeds & Environment Specifications**: Exact seeds and version requirements used to ensure reproducibility across evaluations.
4.  **Exact Split Code**: The code responsible for the train/val/test data partitioning to confirm user-level separation.
