# NIST SP 800-207 Mapping

## NIST Principle to Project Mapping

| NIST Principle | Project Feature | Implementation |
|----------------|-----------------|----------------|
| **Never Trust, Always Verify** | User Authentication & Adaptive Access Control | Every user and device is authenticated and verified before access is granted using identity verification, MFA, and trust score evaluation. |
| **Least Privilege** | Role-Based Access Control (RBAC) | Users receive only the minimum permissions required for their roles, reducing unauthorized access to sensitive resources. |
| **Continuous Monitoring** | AI-Powered Security Dashboard | The dashboard continuously monitors user behavior, login activity, file access, device health, and network traffic to detect suspicious activities in real time. |
| **Policy Engine (PE)** | AI Decision Engine | Evaluates every access request based on user identity, device status, trust score, behavior analysis, and security policies before making an access decision. |
| **Policy Administrator (PA)** | Access & Session Management | Executes the Policy Engine's decisions by creating, updating, or terminating user sessions and applying security policies dynamically. |
| **Policy Enforcement Point (PEP)** | Secure Access Gateway | Enforces access decisions by allowing, denying, or revoking access to applications, files, and enterprise resources based on Zero Trust policies. |

---

## Never Trust, Always Verify

Every user and device requesting access is authenticated and authorized before permission is granted. The AI-Powered Zero Trust Security Dashboard continuously verifies user identity, device health, and contextual information, ensuring that trust is never assumed regardless of network location.

---

## Least Privilege

The dashboard implements Role-Based Access Control (RBAC) to ensure users receive only the permissions required for their responsibilities. Limiting access minimizes insider threats and reduces the possibility of unauthorized access to sensitive intellectual property and organizational resources.

---

## Continuous Monitoring

The dashboard continuously monitors user behavior, login attempts, device status, file access, and network activity. AI-based User and Entity Behavior Analytics (UEBA) and anomaly detection identify suspicious activities in real time, allowing security teams to respond quickly to potential threats.

---

## Policy Engine (PE)

The Policy Engine evaluates every access request using predefined security policies, user identity, device compliance, behavioral analysis, trust scores, and contextual risk factors. Based on this evaluation, it determines whether access should be granted, denied, or require additional verification.

---

## Policy Administrator (PA)

The Policy Administrator executes the decisions made by the Policy Engine. It creates user sessions, applies security policies, updates permissions dynamically, and terminates sessions when suspicious behavior or policy violations are detected, ensuring secure access management.

---

## Policy Enforcement Point (PEP)

The Policy Enforcement Point acts as the gateway between users and protected resources. It enforces access decisions by allowing, denying, or revoking access to applications, files, APIs, and network resources based on the decisions provided by the Policy Engine, ensuring continuous Zero Trust enforcement throughout the system.
