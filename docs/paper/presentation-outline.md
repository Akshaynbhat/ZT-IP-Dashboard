# Demo Day Presentation Outline (10 Slides, 10-Minute Slot)

## Slide 1: Title Slide
- **Slide Title:** A Zero Trust-Aligned Framework for Explainable Insider Threat Detection and Adaptive Access Control
- **Visual Content:**
  - Subtitle: "Demo Day - Undergraduate Internship Project (8-Week Implementation)"
  - Team Names & Roles:
    - Member 1: Security Architect & System Integration
    - Member 2: ML Pipeline & Modeling
    - Member 3: Backend Engineer (FastAPI & PDP)
    - Member 4: Frontend Engineer (React & UX)
    - Member 5: IEEE Documentation Lead
  - Visual of a locked codebase repository icon.
- **Speaker Notes (3-4 sentences):**
  "Good morning, everyone. We are excited to present our project: a Zero Trust-aligned framework for explainable insider threat detection. Over the past eight weeks, our team has designed, implemented, and validated a containerized prototype that bridges the gap between machine learning anomaly detection and dynamic access policy enforcement. Today, we will show you how our system monitors developer activity, computes threat scores, and enforces security constraints in real-time."

## Slide 2: Problem Statement
- **Slide Title:** The Threat Within: Insider Threats to Software IP
- **Visual Content:**
  - Bullet points highlighting:
    - Vulnerability of source code repositories to IP theft.
    - Limitations of "trust but verify" boundary-focused systems (VPN, static MFA).
    - Hard-to-detect nature of malicious insiders using legitimate credentials.
  - **Key Statistic Callout:** *"According to Ponemon Institute, the average annual cost of insider threats is $16.2M, with credential theft and IP exfiltration taking an average of 86 days to contain."*
- **Speaker Notes (3-4 sentences):**
  "Traditional perimeter security mechanisms focus on securing the network boundary, leaving organizations vulnerable once an adversary is inside. Insider threats are especially dangerous because attackers use authorized credentials and execute actions that closely mimic standard workflows, such as reading source code or downloading files. Our goal is to protect high-value software source repositories where IP theft is highly damaging. Existing solutions lack real-time enforcement or fail to explain why access was denied, creating friction for legitimate developers."

## Slide 3: Zero Trust Architecture & NIST SP 800-207
- **Slide Title:** NIST SP 800-207 Zero Trust Architecture (ZTA)
- **Visual Content:**
  - Simple block diagram showing the flow:
    - **Subject Request** $\rightarrow$ **Policy Enforcement Point (PEP)** $\leftrightarrow$ **Policy Decision Point (PDP)** $\rightarrow$ **Resource**.
  - Callout text: *"Never Trust, Always Verify."*
  - Key ZTA principles highlighted: Continuous verification, context-aware policy enforcement, and dynamic trust scoring.
- **Speaker Notes (3-4 sentences):**
  "To address the limitations of perimeter security, we aligned our system with the NIST Special Publication 800-207 Zero Trust Architecture. Zero Trust operates under the core principle of 'never trust, always verify,' requiring access to resources to be continually authorized and validated. In our system, we separate the Policy Enforcement Point (PEP), which intercepts developer actions, from the Policy Decision Point (PDP), which calculates behavioral risk and makes access control decisions. This ensures that every repository action is validated against real-time context."

## Slide 4: System Architecture Overview
- **Slide Title:** System Topology & Component Integration
- **Visual Content:**
  - Architecture diagram showing the interaction of the four Docker containers:
    - `zt_keycloak` (PEP) $\rightarrow$ `zt_backend` (PDP / FastAPI) $\rightarrow$ `zt_postgres` (Database) $\leftrightarrow$ `zt_frontend` (React Dashboard).
  - Icons indicating the protocols used (OIDC, JWT, REST API, Celery worker).
- **Speaker Notes (3-4 sentences):**
  "Our containerized prototype consists of four integrated services. Keycloak serves as the Policy Enforcement Point, managing authentication and injecting identity compliance details into OIDC tokens. The FastAPI backend serves as the Policy Decision Point, parsing these tokens, querying developer session features from PostgreSQL, and calculating trust scores. Security teams monitor these events via a React frontend dashboard, which communicates with the backend to show risk states and handle alerts."

## Slide 5: The Hybrid ML Pipeline & Trust Score Formula
- **Slide Title:** Hybrid Machine Learning & Dynamic Trust Scoring
- **Visual Content:**
  - Flowchart: Raw Logs $\rightarrow$ Feature Engineering (12 features) $\rightarrow$ Isolation Forest Anomaly Score $\rightarrow$ Random Forest Risk Classifier $\rightarrow$ Dynamic Trust Score.
  - **Equation Callout:**
    $$T = 100 \times \left[ 0.4 \times (1 - A) + 0.4 \times (1 - P_r) + 0.2 \times C_{id} \right]$$
  - Text description of weights ($w_1 = 40\%$, $w_2 = 40\%$, $w_3 = 20\%$).
- **Speaker Notes (3-4 sentences):**
  "We designed a two-stage hybrid machine learning pipeline to handle the extreme class imbalance in security logs. First, an unsupervised Isolation Forest calculates a global anomaly score, which is then injected directly as a feature into a supervised Random Forest classifier. The classifier outputs a supervised risk probability of a session being malicious. Finally, the PDP computes a composite Trust Score from these two ML outputs and Keycloak's identity confidence metric, allowing us to enforce security actions dynamically."

## Slide 6: Live Demo Scenario
- **Slide Title:** Walkthrough: Dynamic Policy Enforcement
- **Visual Content:**
  - Visual timeline of the simulation:
    - **Step 1:** Developer logs in (Normal Trust: 95 $\rightarrow$ Access Allowed).
    - **Step 2:** Off-hours file reads and repository clones occur (Trust drops to 45 $\rightarrow$ MFA Required).
    - **Step 3:** Keycloak prompts for step-up MFA challenge.
    - **Step 4:** Mass sensitive file deletion attempt (Trust drops to 15 $\rightarrow$ Session Terminated / Alert Sent).
  - Screenshots of the React Alert screen and SHAP explanations.
- **Speaker Notes (3-4 sentences):**
  "In this demo simulation, we will showcase a developer account being compromised. Initially, the user logs in and operates normally, maintaining a high Trust Score. However, when the user starts executing large file reads and repository clones during off-hours, their Trust Score drops, prompting Keycloak to issue a step-up MFA challenge. If the behavior escalates to deleting sensitive files, the backend immediately terminates the session and registers an alert on the dashboard."

## Slide 7: Experimental Results
- **Slide Title:** Performance Validation on CERT r4.2
- **Visual Content:**
  - Table showing key evaluation metrics:
    - **Precision (Macro-Avg):** `[RF_PRECISION]`
    - **Recall (Macro-Avg):** `[RF_RECALL]`
    - **F1-macro:** `[RF_F1_MACRO]`
    - **ROC-AUC:** `[RF_ROC_AUC]`
  - Standard confusion matrix display showing True Negatives (TN), False Positives (FP), False Negatives (FN), and True Positives (TP).
  - Note: *"Evaluation conducted using user-level split to prevent data leakage."*
- **Speaker Notes (3-4 sentences):**
  "We validated our machine learning models on a developer-focused subset of the CERT Insider Threat Dataset r4.2. Because malicious insider actions are rare, we optimized our supervised model using F1-macro, which treats both classes equally. The hybrid classifier achieved an F1-macro score of [RESULT_F1] and an ROC-AUC of [RESULT_AUCROC] on completely unseen test users. Our sensitivity analysis proved that allocating 80% weight to behavioral signals and 20% to identity signals provides the optimal detection posture."

## Slide 8: Explainable Security (SHAP)
- **Slide Title:** Surfacing Explainability at the Decision Point
- **Visual Content:**
  - Graphic demonstrating SHAP explanation generation:
    - **Session Risk Probability** $\rightarrow$ **SHAP TreeExplainer** $\rightarrow$ **Top 3 Features** $\rightarrow$ **Human-Readable Reason Codes**.
  - Example card:
    - *Reason 1:* Anomalous off-hours activity ($+0.25$ risk shift)
    - *Reason 2:* Unusual external domain visits ($+0.18$ risk shift)
    - *Reason 3:* Mass repository clones ($+0.12$ risk shift)
- **Speaker Notes (3-4 sentences):**
  "Explainability is a core requirement of modern security systems, which is why we integrated SHAP values directly into our Policy Decision Point. When the Trust Score drops below a safe threshold, the backend calls SHAP's TreeExplainer to calculate the exact feature contributions for that request. The system extracts the top three positive features and maps them to human-readable explanation codes on the administrative UI. This eliminates the 'black box' problem, allowing security operators to instantly audit why access was restricted."

## Slide 9: Project Limitations & Future Work
- **Slide Title:** Limitations and Future Directions
- **Visual Content:**
  - Bulleted list of current limitations:
    - Log monitoring is simulated via event replay, not live OS agents.
    - Designed for single-tenant, single-organization deployment.
    - Offline machine learning training.
  - Bulleted list of future work:
    - Implementation of lightweight endpoint agents for file system event interception.
    - Transition from offline batch training to online, adaptive ML learning.
    - Multi-tenant cloud orchestration support.
- **Speaker Notes (3-4 sentences):**
  "As a student prototype, there are key limitations to note. Currently, developer activities are monitored via a log replay simulator running the CERT dataset, meaning we do not capture live OS-level telemetry. Additionally, the system is designed for single-tenant, single-organization configurations. In the future, we plan to implement live endpoint monitoring agents, transition to online machine learning models that adapt to new baseline behaviors in real-time, and scale the dashboard for multi-tenant deployments."

## Slide 10: Conclusion & Q&A Preparation
- **Slide Title:** Conclusion & Questions
- **Visual Content:**
  - Summary points:
    - NIST SP 800-207 Zero Trust compliance.
    - Two-stage hybrid ML pipeline (Isolation Forest + Random Forest).
    - Real-time explanation codes via SHAP TreeExplainer.
  - "Thank you! Any Questions?"
- **Q&A Preparation (5 Key Questions & Answers):**
  1. **Q:** *Why did you inject the Isolation Forest score into the Random Forest instead of running them in parallel?*
     **A:** Injecting the score as a feature allows the Random Forest to learn how global anomalies relate to supervised threat patterns, rather than relying on a simple voting ensemble, improving F1-macro performance.
  2. **Q:** *How does the system handle a developer who legitimately needs to work during off-hours?*
     **A:** Their Trust Score will decrease slightly due to off-hours activity, but if their identity confidence is high (e.g., they authenticated using hardware MFA on a managed device) and other behavioral signals are normal, the composite score stays high enough to avoid restriction.
  3. **Q:** *What is the computational overhead of calculating SHAP values inline for every request?*
     **A:** We calculate SHAP values using TreeExplainer only when the Trust Score drops below a threshold, limiting computation to suspicious requests and avoiding latency on standard access requests.
  4. **Q:** *How do you prevent attackers from slowly poisoning the behavioral baseline?*
     **A:** Baseline calculations use historical data across the entire developer population and are updated periodically. Unsupervised Isolation Forests are robust to poisoning because they look for statistical isolation, not just historical averages.
  5. **Q:** *How does your policy engine differ from standard role-based access control?*
     **A:** RBAC is static and role-based. Our engine is dynamic and context-aware, modifying a user's permissions at runtime based on their immediate behavior and identity verification confidence.
- **Speaker Notes (3-4 sentences):**
  "In conclusion, our framework demonstrates that integrating explainable anomaly detection with NIST SP 800-207 Zero Trust principles significantly mitigates insider threats without disrupting developer workflows. We have proved that machine learning outputs can be directly translated into dynamic, database-driven policy actions such as step-up authentication or access restrictions. We would like to thank our advisors, and we are now open to any questions."
