# MITRE ATT&CK Mapping

## Overview

The MITRE ATT&CK Framework is a globally recognized knowledge base of attacker tactics and techniques based on real-world observations. It helps organizations understand attacker behavior and improve threat detection and response.

The AI-Powered Zero Trust Security Dashboard maps common attack techniques to Zero Trust security controls, AI-based anomaly detection, and continuous monitoring to detect insider threats and unauthorized activities.

---

# MITRE ATT&CK Mapping Table

| MITRE ATT&CK Tactic | Technique | Example Attack | Project Detection / Mitigation |
|---------------------|-----------|----------------|--------------------------------|
| **Initial Access** | Valid Accounts (T1078) | Attacker logs in using stolen employee credentials | Keycloak authentication, RBAC, MFA (planned), trust score evaluation |
| **Execution** | Command and Scripting Interpreter (T1059) | Malicious scripts executed after login | User behavior monitoring, anomaly detection, security alerts |
| **Persistence** | Account Manipulation (T1098) | Attacker creates or modifies user accounts | RBAC, audit logging, administrator approval |
| **Privilege Escalation** | Exploitation for Privilege Escalation (T1068) | Normal employee gains administrator privileges | Role-Based Access Control, authorization checks, permission reviews |
| **Defense Evasion** | Clear Windows Event Logs (T1070) | Attacker deletes activity logs | Secure audit logs, centralized logging, restricted permissions |
| **Credential Access** | Credential Dumping (T1003) | Passwords or authentication tokens are stolen | Secure authentication, MFA (planned), encrypted credentials |
| **Discovery** | Account Discovery (T1087) | Attacker enumerates users and permissions | Continuous monitoring, anomaly detection, RBAC |
| **Lateral Movement** | Remote Services (T1021) | Attacker moves across internal systems | Device verification, continuous authentication, trust score evaluation |
| **Collection** | Data from Local System (T1005) | Confidential files are collected | File access monitoring, AI anomaly detection, audit logs |
| **Exfiltration** | Exfiltration Over Web Services (T1567) | Sensitive data uploaded outside the organization | Real-time monitoring, trust score reduction, security alerts |
| **Impact** | Data Destruction (T1485) | Critical files are deleted | RBAC, backups, audit logging, administrator approval |

---

# Mapping Explanation

## Initial Access

Attackers may attempt to log in using stolen employee credentials. The project reduces this risk using Keycloak authentication, Role-Based Access Control (RBAC), continuous verification, and trust score evaluation. Multi-Factor Authentication (MFA) can further strengthen protection.

---

## Execution

After gaining access, attackers may execute malicious commands or scripts. The machine learning engine continuously analyzes user behavior and detects abnormal activities using Isolation Forest and Random Forest models.

---

## Persistence

Attackers may attempt to maintain long-term access by modifying user accounts or permissions. RBAC, audit logs, and administrator-controlled account management help prevent unauthorized persistence.

---

## Privilege Escalation

An attacker may attempt to gain administrator privileges. The project enforces Least Privilege access, RBAC, and authorization checks on every request to prevent privilege escalation.

---

## Defense Evasion

Attackers may try to delete logs or hide malicious activity. Secure audit logging and centralized log storage preserve security records for investigation.

---

## Credential Access

Attackers may attempt to steal passwords or authentication tokens. Secure authentication, encrypted credentials, and planned MFA reduce the risk of credential theft.

---

## Discovery

Attackers often enumerate users, systems, or permissions before launching attacks. Continuous monitoring and anomaly detection help identify unusual discovery activities.

---

## Lateral Movement

After compromising one account, attackers may attempt to move to other systems. Continuous authentication, device verification, and trust score evaluation help restrict unauthorized movement.

---

## Collection

Attackers may collect confidential files before exfiltration. The dashboard monitors file access patterns and uses AI models to detect unusual download behavior.

---

## Exfiltration

Sensitive organizational data may be transferred outside the network. Real-time monitoring, trust score calculation, and security alerts help detect and respond to exfiltration attempts.

---

## Impact

Attackers may delete or modify important organizational data. RBAC, audit logs, regular backups, and administrator approval help reduce the impact of destructive attacks.

---

# Conclusion

The AI-Powered Zero Trust Security Dashboard aligns with the MITRE ATT&CK framework by mapping common attacker tactics to security controls based on Zero Trust Architecture. Through Keycloak authentication, RBAC, AI-powered anomaly detection, continuous monitoring, trust score evaluation, and audit logging, the project detects insider threats, reduces unauthorized access, and strengthens enterprise cybersecurity.
