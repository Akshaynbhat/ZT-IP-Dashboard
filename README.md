# Zero Trust Insider Pathogen (ZT-IP) Security Dashboard

An enterprise-grade Zero Trust security telemetry and explainable anomaly detection platform. The system ingests developer activity logs, runs them through dynamic machine learning scoring pipelines, evaluates security policies under role-based access controls, and explains threat contributions using SHAP (SHapley Additive exPlanations).

---

## 🏗 System Architecture

The project is structured as a containerized microservices application:

```
                  +----------------------------------------------+
                  |               Web Browser                    |
                  |  (Vite + React 18 + TS + Tailwind + CSS)    |
                  +-------+-----------------------------+--------+
                          |                             |
             OIDC Auth Flow (Authorization)             | JSON Requests
                          v                             v
+-------------------------+----+       +----------------+--------+
|          OIDC Directory      |       |      Nginx Proxy Server |
|   (Keycloak 24.0 on :8080)   |       |  (Frontend Container :3000)
+-------------------------+----+       +----------------+--------+
                          ^                             |
                          | Validate Tokens             | Proxy API (/:api)
                          |                             v
                  +-------+-----------------------------+--------+
                  |               FastAPI Backend                |
                  |                (Port :8000)                  |
                  +-------+-----------------------------+--------+
                          |                             |
                Scores &  |                             | Read/Write
                Alerts    v                             v
                  +-------+--------+           +--------+--------+
                  |  APScheduler   |           |  PostgreSQL 15  |
                  | Scoring Worker |           |  (Port :5432)   |
                  +-------+--------+           +-----------------+
                          |
             Loads Pickle |
             Model Assets v
                  +-------+--------+
                  |  ML Inference  |
                  | (Scikit-Learn) |
                  +----------------+
```

*   **Frontend (`frontend/`)**: React 18, TypeScript, Tailwind CSS, and Recharts. Serves a responsive, dark-themed UI. Contains views tailored for security personnel (Admin/Analyst) and standard employees.
*   **Backend (`backend/`)**: FastAPI server exposes REST endpoints for event ingestion, score retrieves, alert reviews, and SHAP decision explanations. Runs a background `APScheduler` job to score new access logs.
*   **Identity Provider (`infra/keycloak/`)**: Keycloak directory managing authorization realms, roles (`admin`, `analyst`, `employee`), and clients.
*   **Database (`infra/postgres/`)**: PostgreSQL 15 storing raw access logs, user metadata, dynamic model outputs, and generated security alerts.

---

## 🧠 Machine Learning Scoring Engine

The ML scoring engine (`backend/app/ml/`) replaces basic static heuristics with double-model evaluations:

### 1. The Models
*   **Anomaly Classifier (Isolation Forest)**: 
    *   Trained with `n_estimators=200` and `contamination=0.1`.
    *   Estimates how out-of-distribution a user's behavior is.
    *   The raw decision score $d$ is squashed into a probability-like anomaly score ($0$ to $1$) using a logistic function:
        $$anomaly\_score = \frac{1}{1 + e^{10 \cdot d}}$$
        *(where negative $d$ represents high anomaly, mapping scores close to $1.0$)*.
*   **Risk Classifier (Random Forest)**:
    *   Trained with `n_estimators=300` and `max_depth=12` for binary classification (`[0: normal, 1: malicious]`).
    *   Predicts the probability of insider threat behavior based on patterns mapped from the CERT r4.2 dataset.
*   **Explainer Engine (SHAP)**:
    *   Utilizes a cached `shap.TreeExplainer` built on top of the Random Forest model.
    *   Calculates the exact feature contributions for each prediction, sending the top 5 absolute contributors to the UI.

### 2. Feature Adapter Mappings (14 Features)
The system tracks activity over a trailing **24-hour rolling window** to build a feature vector:

| Feature Name | Description | CERT Dataset Proxy |
| :--- | :--- | :--- |
| `total_logins` | Total count of `login` events in the last 24h. | `ldap.csv` |
| `unique_login_pcs` | Number of distinct `device_id` values on login events. | `ldap.csv` |
| `avg_login_hour` | The mean hour of day of all login events. Defaults to `12.0` if no logins. | `ldap.csv` |
| `off_hour_logins` | Count of login events occurring in off-hours (before 6 AM or at/after 8 PM). | `ldap.csv` |
| `total_device_events` | Total events with non-null `device_id`. | `device.csv` (USB logs) |
| `unique_devices` | Count of distinct physical devices observed. | `device.csv` (USB logs) |
| `off_hour_device` | Count of device-linked events in off-hours. | `device.csv` (USB logs) |
| `files_accessed` | Count of `file_download` + `repo_access` events. | `file.csv` |
| `unique_files` | Number of distinct resources targeted. | `file.csv` |
| `unique_content` | Number of distinct resources on `file_download` only. | `file.csv` |
| `off_hour_file` | Count of file interaction events in off-hours. | `file.csv` |
| `files_per_login` | Ratio of files accessed to logins: $\frac{files\_accessed}{\max(total\_logins, 1)}$. | Derivative |
| `device_login_ratio` | Ratio of device events to logins: $\frac{total\_device\_events}{\max(total\_logins, 1)}$. | Derivative |
| `off_hour_ratio` | Ratio of all off-hour events to all events in the 24h window. | Derivative |

---

## ⚙️ Role-Based Access Controls (RBAC)

The system enforces route-level and API-level Zero Trust role guards:

*   **Security Admin (`test.admin`)**: Full access to global telemetry, policy configuration rules, alerts, SHAP charts, and risk audit logs.
*   **Security Analyst (`test.analyst`)**: Access to risk audits, scores, and alerts. Authorized to mark security alerts as "reviewed". Restricted from policy rule modifications.
*   **Standard Employee (`test.employee`)**: Strictly restricted from global security views. Redirected back to the Overview page showing *only* their personal profile, personal trust score, and personal 24h activity history. An alert banner notifies them of restriction events.

---

## 🚀 Installation & Local Run Guide

### Prerequisites
*   [Docker Desktop](https://www.docker.com/products/docker-desktop/) (must be running on host).
*   Python 3.10+ (for local host verification).

### Step 1: Clone and Position ML Models
Ensure the following pre-trained models are present at the root `ml/models/` folder:
*   `ml/models/final_isolation_forest.pkl`
*   `ml/models/final_random_forest.pkl`

### Step 2: Spin Up Containers
From the repository root, run the Docker Compose commands inside the `infra/` folder:
```bash
cd infra
docker compose up -d --build
```
This builds and launches four services:
*   `zt_postgres` on port `5432`
*   `zt_keycloak` on port `8080`
*   `zt_backend` on port `8000`
*   `zt_frontend` on port `3000` (production Nginx proxy)

---

## 🔍 Verification & Testing

### 1. Run the Local Model Tester
Run the standalone model scoring script on the host to verify the pickled scikit-learn models:
```bash
python tests/verify_models.py
```
*Expected Output:*
```
[Quiet Day Scenario]
  Anomaly Score: 0.7904
  Risk Probability: 0.2560
  Risk Class: low

[Suspicious Day Scenario]
  Anomaly Score: 0.9330
  Risk Probability: 0.9303
  Risk Class: high

SUCCESS: Suspicious scenario correctly scored higher risk and anomaly!
```

### 2. Run the End-to-End API Integration Suite
Verify API-level authorization logic, scheduler tasks, database inserts, and OIDC tokens:
```bash
# Run using Git Bash on Windows or Linux terminal
./tests/test_api_e2e.sh
```
*Expected Output:* All **15/15** integration tests pass.

### 3. Run the Live Event Simulator
Simulate 10 minutes of mixed traffic containing normal developer activities and TOR exit-node logins/insider downloads:
```bash
python simulator/simulate_events.py --scenario mixed --duration 10
```

### 4. Query postgres to verify score variation
Verify that scores dynamically change across users:
```bash
docker exec -it zt_postgres psql -U zt_admin -d zt_dashboard -c "SELECT u.username, ROUND(avg(t.trust_score)::numeric, 2) as avg_score, count(t.id) as score_count FROM trust_scores t JOIN users u ON t.user_id = u.id GROUP BY u.username ORDER BY avg_score ASC;"
```
*(User representing `eve.insider` will display the lowest average score).*
