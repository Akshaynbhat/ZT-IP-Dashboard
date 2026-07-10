To validate the proposed Zero Trust-aligned framework, a containerized prototype was implemented and deployed. This section details the system architecture, container organization, identity configuration, policy enforcement mechanism, and frontend monitoring interfaces.

## A. Containerized Deployment and Architecture

The system is deployed using Docker Compose and consists of four main containers, aligning with the architectural design depicted in the system topology. The roles of each container are as follows:
1) **PostgreSQL Database (`zt_postgres`):** Runs PostgreSQL version 15 to store historical developer activity logs, computed behavioral features, policy engine configuration tables, and security audit logs.
2) **Keycloak Identity Provider (`zt_keycloak`):** Runs Keycloak version 24.0, serving as the central authentication server and the primary Policy Enforcement Point (PEP) for user sessions.
3) **FastAPI Backend (`zt_backend`):** A Python-based FastAPI application acting as the Policy Decision Point (PDP). It hosts the machine learning scoring service, validates identity tokens, and evaluates access control decisions.
4) **React Frontend (`zt_frontend`):** A React-based web dashboard providing administrators with real-time visibility into developer sessions, threat scores, and system alerts.

## B. Identity and Access Configuration

Keycloak is configured with a dedicated security realm, defining client applications for the frontend (`zt-frontend`) and the backend (`zt-backend`). User profiles are mapped to organizational roles (`developer`, `lead_engineer`, `security_admin`) to enable baseline Role-Based Access Control (RBAC). In alignment with NIST SP 800-207, Keycloak acts as the Policy Enforcement Point (PEP). When a developer requests access to a repository resource, the client redirects the request to Keycloak for OpenID Connect (OIDC) authentication. The generated JSON Web Token (JWT) encapsulates authentication context (e.g., session age, authentication method, and device compliance), which the backend translates into the identity confidence score ($C_{id}$).

## C. Policy Decision Point (PDP) and Rule Engine

The FastAPI backend functions as the PDP. Upon receiving a request with a bearer JWT, the backend performs signature validation using Keycloak’s JSON Web Key Set (JWKS) endpoint. To make an access decision, the backend queries Postgres to retrieve the latest session features, computes the hybrid ML scores, and calculates the composite Trust Score. 

The decision is evaluated against a database-driven policy rule table. This table maps dynamic Trust Score bands to specific access postures:
- **Allow ($T \ge 80$):** Grants full access to repositories and deployment pipelines.
- **Require MFA ($50 \le T < 80$):** Demands step-up authentication via Keycloak prior to executing sensitive actions.
- **Restrict ($30 \le T < 50$):** Restricts the user to read-only capabilities and blocks code push actions.
- **Alert ($T < 30$):** Denies access immediately and flags the session for administrative review.

## D. Administrative Interface and Background Scoring

The React dashboard provides a monitoring interface comprised of four screens:
1) **Overview Screen:** Displays aggregated metrics, including average trust scores, active session counts, and system-wide alert statistics.
2) **Risk Monitoring Screen:** Shows real-time lists of developer sessions with their corresponding machine learning anomaly scores and risk classification labels.
3) **Trust Score Visualization Screen:** Illustrates the mathematical breakdown of individual trust scores, showing the relative contributions of $A(x)$, $P_r$, and $C_{id}$.
4) **Alert Management Screen:** Enables security teams to review flagged violations, inspect SHAP reason codes, and execute manual policy overrides.

To ensure continuous verification, a background scoring worker implemented using Celery runs at a regular [WORKER_INTERVAL] interval. The worker polls Postgres for newly generated events, updates the rolling 24-hour feature vectors, executes the hybrid ML pipeline, and updates the Trust Scores. Event generation for evaluation purposes was performed via a log replay simulator, with live agent-based monitoring identified as future work.
