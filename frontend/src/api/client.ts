import axios from "axios";
import { getToken } from "../auth/keycloak";
import keycloak from "../auth/keycloak";
import {
  User,
  UserHistory,
  TrustScore,
  Explanation,
  Alert,
  PolicyRule,
} from "../types";

const client = axios.create({
  baseURL: "", // Routing requests through Vite dev server proxy
});

// Attach bearer tokens to outgoing API requests
client.interceptors.request.use(
  async (config) => {
    try {
      await keycloak.updateToken(30);
    } catch (error) {
      console.error("Failed to refresh Keycloak token, redirecting to login:", error);
      keycloak.login();
    }
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Auto-trigger re-authentications on unauthorized status
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      console.warn("Unauthorized API call detected, redirecting to Keycloak...");
      keycloak.login();
    }
    return Promise.reject(error);
  }
);

export async function getUsers(): Promise<User[]> {
  const res = await client.get<User[]>("/api/v1/users");
  return res.data;
}

export async function getUserHistory(id: string): Promise<UserHistory> {
  const res = await client.get<UserHistory>(`/api/v1/users/${id}/history`);
  return res.data;
}

export async function getScores(): Promise<TrustScore[]> {
  const res = await client.get<TrustScore[]>("/api/v1/scores");
  return res.data;
}

export async function getExplanation(scoreId: string): Promise<Explanation> {
  const res = await client.get<Explanation>(`/api/v1/scores/${scoreId}/explanation`);
  return res.data;
}

export async function getAlerts(
  statusFilter?: string,
  severityFilter?: string
): Promise<Alert[]> {
  const params: Record<string, string> = {};
  if (statusFilter) params.status_filter = statusFilter;
  if (severityFilter) params.severity_filter = severityFilter;

  const res = await client.get<Alert[]>("/api/v1/alerts", { params });
  return res.data;
}

export async function updateAlert(
  id: string,
  status: string,
  reviewedBy: string
): Promise<Alert> {
  const res = await client.patch<Alert>(`/api/v1/alerts/${id}`, {
    status,
    reviewed_by: reviewedBy,
  });
  return res.data;
}

export async function getPolicyRules(): Promise<PolicyRule[]> {
  const res = await client.get<PolicyRule[]>("/api/v1/policy-rules");
  return res.data;
}

export async function updatePolicyRule(
  id: string,
  data: Partial<PolicyRule>
): Promise<PolicyRule> {
  const res = await client.put<PolicyRule>(`/api/v1/policy-rules/${id}`, data);
  return res.data;
}
