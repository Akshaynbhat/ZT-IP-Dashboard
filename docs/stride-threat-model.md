# STRIDE Threat Model

## Overview

The **AI-Powered Zero Trust Security Dashboard** is designed to secure enterprise resources using **Zero Trust Architecture (NIST SP 800-207)**. This document applies the **STRIDE Threat Modeling** framework to identify possible security threats and describes how the project mitigates them.

---

# What is STRIDE?

STRIDE is a threat modeling framework developed by Microsoft to identify security risks during system design.

| Letter | Threat | Meaning |
|--------|--------|---------|
| **S** | Spoofing | Pretending to be another user or device |
| **T** | Tampering | Modifying data without authorization |
| **R** | Repudiation | Denying actions because there is no proof |
| **I** | Information Disclosure | Unauthorized access to confidential data |
| **D** | Denial of Service | Making the system unavailable |
| **E** | Elevation of Privilege | Gaining higher permissions illegally |

---

# Project Components

The AI-Powered Zero Trust Security Dashboard consists of the following components:

```
User
   │
   ▼
React Dashboard
   │
   ▼
Keycloak Authentication (OIDC)
   │
   ▼
FastAPI Backend
   │
   ▼
Machine Learning Engine
(Isolation Forest + Random Forest + SHAP)
   │
   ▼
PostgreSQL Database
   │
   ▼
Security Dashboard & Alerts
```

Potential attacks can target any of these components.

---

## STRIDE Summary Table

| STRIDE | Example Threat | Possible Impact | Mitigation |
|---------|----------------|-----------------|------------|
| **Spoofing** | Stolen employee credentials, fake user accounts | Unauthorized access to enterprise resources | Keycloak authentication, Multi-Factor Authentication (MFA), device verification, secure session management |
| **Tampering** | Modified activity logs, altered trust scores, changed ML predictions | Incorrect security decisions and loss of data integrity | Role-Based Access Control (RBAC), audit logs, encryption, database integrity checks |
| **Repudiation** | User denies login, file download, or policy changes | Lack of accountability and difficulty in investigations | Secure audit logging, timestamps, user ID and IP address logging |
| **Information Disclosure** | Unauthorized access to employee records, trust scores, or security logs | Exposure of confidential organizational data | HTTPS/TLS encryption, Least Privilege access, secure APIs, encrypted database |
| **Denial of Service** | API flooding, login flooding, excessive requests | Dashboard and backend services become unavailable | Rate limiting, request throttling, monitoring, Web Application Firewall (WAF), load balancing |
| **Elevation of Privilege** | Employee gains administrator privileges or bypasses RBAC | Complete system compromise and unauthorized administrative access | Role-Based Access Control (RBAC), authentication and authorization checks, Least Privilege principle, permission reviews |

---

# Spoofing

### Threats
- Stolen login credentials
- Fake employee accounts
- Session hijacking
- Fake devices

### Prevention
The project uses **Keycloak** for authentication and Role-Based Access Control (RBAC) for authorization. Every request is validated before access is granted. Future enhancements include Multi-Factor Authentication (MFA) and device verification.

---

# Tampering

### Threats
- Modifying activity logs
- Changing trust scores
- Altering ML predictions
- Editing database records

### Prevention
Role-Based Access Control restricts unauthorized modifications. Audit logs record every important action, while database integrity checks and encryption help protect stored information.

---

# Repudiation

### Threats
- Employee denies downloading confidential files
- Administrator denies policy changes
- User denies login attempts

### Prevention
Every important action is recorded with timestamps, user IDs, and IP addresses. Secure audit logs provide accountability and support forensic investigations.

---

# Information Disclosure

### Threats
- Exposure of employee records
- Leakage of trust scores
- Unauthorized access to logs
- Database compromise

### Prevention
Sensitive information is protected using HTTPS/TLS encryption, secure APIs, Role-Based Access Control, and Least Privilege principles. Only authorized users can access confidential data.

---

# Denial of Service (DoS)

### Threats
- Login flooding
- API flooding
- Resource exhaustion

### Prevention
The backend can be protected using rate limiting, request throttling, monitoring, Web Application Firewall (WAF), and load balancing to ensure service availability.

---

# Elevation of Privilege

### Threats
- Employee gaining administrator rights
- RBAC bypass
- Unauthorized access to restricted APIs

### Prevention
The project enforces Role-Based Access Control, Least Privilege access, and authentication and authorization checks for every request. Regular permission reviews help prevent privilege escalation.

---


# Conclusion

The STRIDE threat model identifies the major security risks in the AI-Powered Zero Trust Security Dashboard and maps them to appropriate mitigation strategies. By combining **Zero Trust principles**, **Keycloak authentication**, **RBAC**, **continuous monitoring**, **audit logging**, and **AI-based anomaly detection**, the system effectively reduces the risks of spoofing, tampering, repudiation, information disclosure, denial of service, and elevation of privilege, providing a secure and scalable enterprise security solution.
