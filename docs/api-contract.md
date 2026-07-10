# ZT-IP Dashboard API Contract Specification

This document defines the interface contract between the FastAPI backend and the React frontend application for the Zero Trust Insider Threat Detection Dashboard.

---

## Global Design Decisions

### Authentication
- All API endpoints (except `/health`) require an OAuth2 bearer token in the HTTP headers:
  `Authorization: Bearer <access_token>`
- Token credentials are validated dynamically using Keycloak RS256 JWKS caching.

### Data Types
- **UUIDs**: Represented as standard string types in request/response JSONs.
- **Timestamps**: Expressed as ISO 8601 strings in UTC format (e.g., `2026-07-09T08:30:00Z`).
- **Trust Scores**: Float values constrained to the `0.0 - 100.0` range.
- **Risk Classes**: Exactly `"low" | "medium" | "high"`.
- **Severities**: Exactly `"low" | "medium" | "high" | "critical"`.
- **Alert Statuses**: Exactly `"open" | "reviewed" | "escalated" | "dismissed"`.

### Trust Score Color Bands (Frontend Standard)
Implement these styling rules across frontend indicator components:
- **Score < 40**: Red (`#EF4444`) -> policy: `restrict`
- **Score 40 - 70**: Yellow (`#F59E0B`) -> policy: `require_mfa`
- **Score >= 70**: Green (`#10B981`) -> policy: `allow`

### Error Response Format
All endpoint validation, authentication, or operational failures return a standard JSON model:
```json
{
  "detail": "Descriptive error message string",
  "code": "ERROR_CODE"
}
```
**Common Error Codes to Handle:**
- `UNAUTHORIZED` (401): Token is missing or invalid.
- `FORBIDDEN` (403): User lacks required role permission.
- `NOT_FOUND` (404): Resource could not be located.
- `VALIDATION_ERROR` (422): Query parameters or request body failed validation.
- `LOGICAL_CONFLICT` (400): Invalid ranges or overlapping policies.

### CORS Rules
- **Allowed Origins**: `http://localhost:3000`
- **Credentials**: `true`
- **Allowed Methods**: `*` (All standard HTTP methods)
- **Allowed Headers**: `*` (All custom client request headers)

### Polling Instructions
The backend does not support WebSockets. The frontend is required to poll the following paths:
- **`GET /api/v1/scores`**: Every 30 seconds
- **`GET /api/v1/alerts`**: Every 15 seconds
- **`GET /api/v1/users`**: Every 60 seconds

---

## Keycloak Integration Settings

Frontend OIDC Client setup parameters for the `keycloak-js` library:
- **Realm URL**: `http://localhost:8080`
- **Realm Name**: `zt-dashboard`
- **Client ID**: `dashboard-frontend`

### Fetching a Token via HTTP POST (Testing Reference)
```bash
curl -s -X POST http://localhost:8080/realms/zt-dashboard/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "client_id=backend-api" \
  -d "client_secret=zt_backend_secret" \
  -d "username=test.admin" \
  -d "password=Admin@123" \
  -d "grant_type=password"
```

---

## Endpoint Specifications

### 1. GET /health
Retrieves the service status. Accessible without authentication.

- **Request**: No parameters.
- **Response 200**:
  ```json
  {
    "status": "ok",
    "service": "zt-ip-dashboard"
  }
  ```

---

### 2. POST /api/v1/events
Ingests telemetry event logs from development tools or simulators.

- **Auth**: Bearer token (any role: `admin`, `analyst`, `employee`).
- **Request Body**:
  ```json
  {
    "user_id": "f5fbf104-e3f3-470b-85be-587265bf02ab",
    "device_fingerprint": "test-device-abc123",
    "event_type": "repo_access",
    "resource": "core-payments-service",
    "bytes_transferred": 1024,
    "ip_address": "10.0.0.1",
    "location": "Bengaluru, IN"
  }
  ```
  *Note: `event_type` must be one of `login`, `repo_access`, `file_download`, `privilege_change`, `code_export`.*
- **Response 202**:
  ```json
  {
    "message": "event accepted",
    "log_id": "8a719c8f-2831-4db8-b593-3cb3e659b85c"
  }
  ```
- **Response 401**: Unauthorized (missing/invalid token).
- **Response 422**: Body validation failed.

---

### 3. GET /api/v1/users
Lists all registered users alongside their current trust score.

- **Auth**: Restricted to `admin` and `analyst` roles.
- **Request**: No parameters.
- **Response 200**:
  ```json
  [
    {
      "id": "f5fbf104-e3f3-470b-85be-587265bf02ab",
      "username": "test.employee",
      "email": "employee@zt-enterprise.io",
      "role": "employee",
      "department": "Engineering",
      "created_at": "2026-07-09T08:00:00Z",
      "current_trust_score": 85.5
    }
  ]
  ```
- **Response 403**: Forbidden (lack permissions).

---

### 4. GET /api/v1/users/{id}/history
Returns chronological trust score historical points and recent access events for a user.

- **Auth**: Admins/Analysts can access any user's history; Employees are strictly restricted to their own ID.
- **Path Parameters**:
  - `id`: User UUID
- **Response 200**:
  ```json
  {
    "user": {
      "id": "f5fbf104-e3f3-470b-85be-587265bf02ab",
      "username": "test.employee",
      "email": "employee@zt-enterprise.io",
      "role": "employee",
      "department": "Engineering",
      "created_at": "2026-07-09T08:00:00Z",
      "current_trust_score": 85.5
    },
    "trust_scores": [
      {
        "id": "c138f29d-4708-4122-871d-7201b22e1b12",
        "user_id": "f5fbf104-e3f3-470b-85be-587265bf02ab",
        "trust_score": 85.5,
        "anomaly_component": 0.2,
        "risk_component": 0.1,
        "computed_at": "2026-07-09T08:10:00Z"
      }
    ],
    "recent_events": [
      {
        "id": "8a719c8f-2831-4db8-b593-3cb3e659b85c",
        "user_id": "f5fbf104-e3f3-470b-85be-587265bf02ab",
        "device_id": "6a992a11-8172-4b2a-89aa-5527a2e26922",
        "event_type": "repo_access",
        "resource": "core-payments-service",
        "bytes_transferred": 1024,
        "event_time": "2026-07-09T08:09:59Z",
        "ip_address": "10.0.0.1",
        "location": "Bengaluru, IN"
      }
    ]
  }
  ```
- **Response 403**: Forbidden (employee querying another user's history).
- **Response 404**: User not found.

---

### 5. GET /api/v1/scores
Returns the latest computed trust score for all users, sorted in ascending order (riskiest users first).

- **Auth**: Restricted to `admin` and `analyst` roles.
- **Request**: No parameters.
- **Response 200**:
  ```json
  [
    {
      "id": "e2f182da-9122-482a-aef2-7203b22e9a22",
      "user_id": "d13264ff-8720-410a-9d90-587265bc11ab",
      "trust_score": 18.2,
      "anomaly_component": 0.38,
      "risk_component": 0.4,
      "computed_at": "2026-07-09T08:29:00Z"
    },
    {
      "id": "c138f29d-4708-4122-871d-7201b22e1b12",
      "user_id": "f5fbf104-e3f3-470b-85be-587265bf02ab",
      "trust_score": 85.5,
      "anomaly_component": 0.2,
      "risk_component": 0.1,
      "computed_at": "2026-07-09T08:10:00Z"
    }
  ]
  ```

---

### 6. GET /api/v1/scores/{id}/explanation
Retrieves the SHAP mathematical feature breakdown explaining a computed security score assessment.

- **Auth**: Restricted to `admin` and `analyst` roles.
- **Path Parameters**:
  - `id`: Model Score UUID (or matching Access Log UUID)
- **Response 200**:
  ```json
  {
    "shap_top_features": [
      {
        "feature": "is_off_hours",
        "shap_value": 0.12,
        "direction": "increase"
      },
      {
        "feature": "files_downloaded_count",
        "shap_value": 0.08,
        "direction": "increase"
      },
      {
        "feature": "bytes_transferred_24h",
        "shap_value": 0.05,
        "direction": "increase"
      }
    ],
    "risk_class": "medium",
    "risk_probability": 0.5,
    "anomaly_score": 0.5
  }
  ```
  *Note: Top features are limited to the 3 most significant items, sorted descending by absolute contribution value.*
- **Response 404**: Score explanation record not found.

---

### 7. GET /api/v1/alerts
Retrieves the history of system-generated security alerts.

- **Auth**: Restricted to `admin` and `analyst` roles.
- **Query Parameters**:
  - `status_filter` (optional string): Filter by status (`open`, `reviewed`, `escalated`, `dismissed`).
  - `severity_filter` (optional string): Filter by severity (`low`, `medium`, `high`, `critical`).
- **Response 200**:
  ```json
  [
    {
      "id": "a9a8f2bd-810a-412e-8a03-7221b22e11ac",
      "severity": "critical",
      "status": "open",
      "created_at": "2026-07-09T08:29:05Z",
      "reviewed_by": null,
      "reviewed_at": null,
      "trust_score": 18.2,
      "username": "eve.insider"
    }
  ]
  ```

---

### 8. PATCH /api/v1/alerts/{id}
Updates the lifecycle status of a security alert (e.g., dismissing it or escalating it for review).

- **Auth**: Restricted to `admin` and `analyst` roles.
- **Path Parameters**:
  - `id`: Alert UUID
- **Request Body**:
  ```json
  {
    "status": "reviewed",
    "reviewed_by": "test.analyst"
  }
  ```
- **Response 200**:
  ```json
  {
    "id": "a9a8f2bd-810a-412e-8a03-7221b22e11ac",
    "severity": "critical",
    "status": "reviewed",
    "created_at": "2026-07-09T08:29:05Z",
    "reviewed_by": "test.analyst",
    "reviewed_at": "2026-07-09T08:35:12Z",
    "trust_score": 18.2,
    "username": "eve.insider"
  }
  ```
- **Response 400**: Invalid alert status payload.
- **Response 404**: Alert not found.

---

### 9. GET /api/v1/policy-rules
Retrieves all configured policy rules defined in the system.

- **Auth**: Restricted to the `admin` role only.
- **Response 200**:
  ```json
  [
    {
      "id": "97e682ba-9110-4bc2-8ef1-7201b22f18aa",
      "rule_name": "Critical Risk Band",
      "threshold_min": 0.0,
      "threshold_max": 40.0,
      "action": "restrict",
      "active": true
    },
    {
      "id": "c7a812dd-812a-4bc8-8ac3-7201b22f18bc",
      "rule_name": "Medium Risk Band",
      "threshold_min": 40.0,
      "threshold_max": 70.0,
      "action": "require_mfa",
      "active": true
    },
    {
      "id": "f8a912bb-1872-4bc3-9ac1-7201b22f18cd",
      "rule_name": "Low Risk Band",
      "threshold_min": 70.0,
      "threshold_max": 101.0,
      "action": "allow",
      "active": true
    }
  ]
  ```
- **Response 403**: Forbidden (lack admin role permissions).

---

### 10. PUT /api/v1/policy-rules/{id}
Updates the boundary thresholds, response action, or active status of a policy rule.

- **Auth**: Restricted to the `admin` role only.
- **Path Parameters**:
  - `id`: Policy Rule UUID
- **Request Body**:
  ```json
  {
    "threshold_min": 40.0,
    "threshold_max": 65.0,
    "action": "require_mfa",
    "active": true
  }
  ```
- **Response 200**:
  ```json
  {
    "id": "c7a812dd-812a-4bc8-8ac3-7201b22f18bc",
    "rule_name": "Medium Risk Band",
    "threshold_min": 40.0,
    "threshold_max": 65.0,
    "action": "require_mfa",
    "active": true
  }
  ```
- **Response 400**: Bad Request (validation overlaps, or `threshold_min` >= `threshold_max` constraint).
- **Response 404**: Policy rule not found.
