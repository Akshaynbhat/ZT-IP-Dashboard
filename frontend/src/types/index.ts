export interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  department: string;
  created_at: string;
  current_trust_score: number | null;
}

export interface TrustScore {
  id: string;
  user_id: string;
  trust_score: number;
  anomaly_component: number;
  risk_component: number;
  computed_at: string;
}

export interface AccessLog {
  id: string;
  user_id: string;
  device_id: string | null;
  event_type: string;
  resource: string | null;
  bytes_transferred: number;
  event_time: string;
  ip_address: string | null;
  location: string | null;
}

export interface UserHistory {
  user: User;
  trust_scores: TrustScore[];
  recent_events: AccessLog[];
}

export interface SHAPFeature {
  feature: string;
  shap_value: number;
  direction: string;
}

export interface Explanation {
  shap_top_features: SHAPFeature[];
  risk_class: string;
  risk_probability: number;
  anomaly_score: number;
}

export interface Alert {
  id: string;
  severity: string;
  status: string;
  created_at: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
  trust_score: number | null;
  username: string | null;
}

export interface PolicyRule {
  id: string;
  rule_name: string;
  threshold_min: number;
  threshold_max: number;
  action: string;
  active: boolean;
}
