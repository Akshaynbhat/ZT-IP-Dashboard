# Architecture Review

## Project Overview

The **Zero Trust Insider Pathogen (ZT-IP) Security Dashboard** is an enterprise-grade security platform designed using the principles of **Zero Trust Architecture (ZTA)**. It combines Identity and Access Management, Machine Learning, Explainable AI (SHAP), Role-Based Access Control (RBAC), and continuous monitoring to detect insider threats and protect organizational resources.

---

# 1. User Flow

The user flow follows Zero Trust principles by verifying every access request before granting access.

### Flow

```
User Login
      │
      ▼
Authentication (Keycloak/OIDC)
      │
      ▼
Authorization (RBAC)
      │
      ▼
Dashboard Access
      │
      ▼
Continuous Monitoring
```

### Review

**Strengths**
- Secure authentication using Keycloak (OIDC).
- Role-Based Access Control (Admin, Analyst, Employee).
- Every API request requires authentication.
- User sessions are continuously validated.

**Suggestions**
- Enable Multi-Factor Authentication (MFA).
- Add device verification before login.
- Include adaptive authentication based on trust score.

---

# 2. Machine Learning Flow

The ML module analyzes user activity and predicts insider threats using AI models.

### Flow

```
CERT r4.2 Dataset
        │
        ▼
Data Preprocessing
        │
        ▼
Feature Extraction (14 Features)
        │
        ▼
Isolation Forest
(Random Forest)
        │
        ▼
Risk Prediction
        │
        ▼
Trust Score Generation
        │
        ▼
SHAP Explainability
        │
        ▼
Alert Generation
```

### Review

**Strengths**
- Uses CERT Insider Threat Dataset Release 4.2.
- Isolation Forest detects anomalous behavior.
- Random Forest predicts insider threat probability.
- SHAP explains model decisions.
- Dynamic trust score is generated.

**Suggestions**
- Retrain models periodically.
- Support online learning.
- Add behavioral risk trends.
- Include confidence scores.

---

# 3. Dashboard Review

The dashboard provides real-time security monitoring and visualization.

### Dashboard Features

- Login Activity
- User Trust Score
- User Details
- Security Alerts
- Suspicious Activity Logs
- Risk Charts
- SHAP Explanation Graphs

### Review

**Strengths**
- Clean React-based interface.
- Real-time trust score visualization.
- Alert management.
- Explainable AI support.
- Separate dashboards for different user roles.

**Suggestions**
- Add threat timeline.
- Include device health status.
- Show geographical login locations.
- Add compliance reports.
- Display historical trust score trends.

---

# 4. Backend Review

The backend manages authentication, API services, machine learning integration, and security policies.

### Components

- FastAPI
- REST APIs
- APScheduler
- ML Inference Engine
- PostgreSQL Connection
- Keycloak Integration

### Review

**Strengths**
- Modular FastAPI architecture.
- Background scoring service.
- RESTful APIs.
- Easy integration with ML models.
- Containerized using Docker.

**Suggestions**
- Implement Policy Engine (PE).
- Add Policy Administrator (PA).
- Improve API rate limiting.
- Enable automatic policy updates.
- Add detailed audit APIs.

---

# 5. Database Review

The PostgreSQL database stores all security-related information.

### Database Stores

- Users
- Roles
- Activity Logs
- Login History
- Trust Scores
- Alerts
- ML Predictions
- User Metadata

### Review

**Strengths**
- Centralized storage.
- Stores complete audit history.
- Maintains trust score history.
- Supports alert tracking.

**Suggestions**
- Encrypt sensitive data.
- Implement backup strategy.
- Archive old logs.
- Improve indexing for faster searches.

---

# 6. Security Review

The project follows Zero Trust security principles from NIST SP 800-207.

### Implemented

- Authentication
- Authorization
- Role-Based Access Control (RBAC)
- Continuous Monitoring
- AI-Based Anomaly Detection
- Trust Score Generation
- Explainable AI (SHAP)
- Secure API Access

### Missing Components

- Multi-Factor Authentication (MFA)
- Device Verification
- Policy Engine (PE)
- Policy Administrator (PA)
- Policy Enforcement Point (PEP)
- Adaptive Access Control

### Suggestions

- Enable MFA using Keycloak.
- Verify endpoint devices before granting access.
- Implement Policy Engine for dynamic decision-making.
- Add Policy Administrator for session management.
- Deploy Policy Enforcement Point for enforcing access policies.
- Introduce adaptive risk-based authentication.

---

# Overall Architecture Strengths

- Clear separation between frontend, backend, machine learning, identity provider, and database.
- Microservices-based architecture.
- AI-powered insider threat detection.
- Explainable AI using SHAP.
- Continuous monitoring and alert generation.
- Role-Based Access Control.
- Docker-based deployment.
- Scalable enterprise architecture.

---

# Areas for Improvement

- Implement complete NIST SP 800-207 logical components (PE, PA, PEP).
- Enable Multi-Factor Authentication.
- Add device trust verification.
- Introduce adaptive access control.
- Improve compliance reporting.
- Integrate automated incident response (SOAR).
- Enhance audit logging and security analytics.

---

# Conclusion

The **Zero Trust Insider Pathogen (ZT-IP) Security Dashboard** provides a strong enterprise security architecture by integrating Zero Trust principles with Artificial Intelligence, Machine Learning, Explainable AI, and Role-Based Access Control. The current architecture successfully supports continuous authentication, insider threat detection, trust score generation, and real-time monitoring. By incorporating additional Zero Trust components such as **Policy Engine, Policy Administrator, Policy Enforcement Point, Multi-Factor Authentication, and Device Verification**, the system can achieve closer alignment with **NIST SP 800-207** and become a more secure, scalable, and enterprise-ready cybersecurity solution.
