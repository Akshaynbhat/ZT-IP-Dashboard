-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table 0: Organizations (Multi-Tenant isolation)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Seed default organization
INSERT INTO organizations (id, name) VALUES ('9f9bbf10-e3f3-470b-85be-587265bf02ab', 'Default Organization');

-- Table 1: Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    keycloak_sub VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'employee',
    department VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT now(),
    tenant_id UUID REFERENCES organizations(id) ON DELETE SET NULL DEFAULT '9f9bbf10-e3f3-470b-85be-587265bf02ab'
);

-- Table 2: Devices
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_fingerprint VARCHAR(255) NOT NULL,
    os VARCHAR(50),
    is_known BOOLEAN DEFAULT false,
    first_seen TIMESTAMPTZ DEFAULT now(),
    tenant_id UUID REFERENCES organizations(id) ON DELETE SET NULL DEFAULT '9f9bbf10-e3f3-470b-85be-587265bf02ab'
);

-- Table 3: Access Logs (Append-Only)
CREATE TABLE access_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id UUID REFERENCES devices(id) ON DELETE SET NULL,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN ('login', 'repo_access', 'file_download', 'privilege_change', 'code_export')),
    resource VARCHAR(255),
    bytes_transferred BIGINT DEFAULT 0,
    event_time TIMESTAMPTZ DEFAULT now(),
    ip_address VARCHAR(45),
    location VARCHAR(100),
    tenant_id UUID REFERENCES organizations(id) ON DELETE SET NULL DEFAULT '9f9bbf10-e3f3-470b-85be-587265bf02ab'
);

-- Enforce Append-Only constraints on access_logs (prevent updates and deletes)
CREATE RULE no_update_access_logs AS ON UPDATE TO access_logs DO INSTEAD NOTHING;
CREATE RULE no_delete_access_logs AS ON DELETE TO access_logs DO INSTEAD NOTHING;

-- Table 4: Model Scores
CREATE TABLE model_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    access_log_id UUID REFERENCES access_logs(id) ON DELETE SET NULL,
    anomaly_score FLOAT NOT NULL,
    risk_class VARCHAR(20) NOT NULL CHECK (risk_class IN ('low', 'medium', 'high')),
    risk_probability FLOAT NOT NULL,
    shap_values JSONB NOT NULL DEFAULT '[]'::jsonb,
    scored_at TIMESTAMPTZ DEFAULT now()
);

-- Table 5: Trust Scores
CREATE TABLE trust_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    trust_score FLOAT NOT NULL CHECK (trust_score >= 0.0 AND trust_score <= 100.0),
    anomaly_component FLOAT NOT NULL,
    risk_component FLOAT NOT NULL,
    computed_at TIMESTAMPTZ DEFAULT now(),
    model_score_id UUID REFERENCES model_scores(id) ON DELETE SET NULL,
    tenant_id UUID REFERENCES organizations(id) ON DELETE SET NULL DEFAULT '9f9bbf10-e3f3-470b-85be-587265bf02ab'
);

-- Table 6: Policy Rules
CREATE TABLE policy_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(100) UNIQUE NOT NULL,
    threshold_min FLOAT NOT NULL,
    threshold_max FLOAT NOT NULL,
    action VARCHAR(50) NOT NULL CHECK (action IN ('allow', 'require_mfa', 'restrict')),
    active BOOLEAN DEFAULT true
);

-- Table 7: Alerts
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trust_score_id UUID REFERENCES trust_scores(id) ON DELETE SET NULL,
    policy_rule_id UUID REFERENCES policy_rules(id) ON DELETE SET NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'reviewed', 'escalated', 'dismissed')),
    reviewed_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT now(),
    reviewed_at TIMESTAMPTZ,
    tenant_id UUID REFERENCES organizations(id) ON DELETE SET NULL DEFAULT '9f9bbf10-e3f3-470b-85be-587265bf02ab'
);


-- Indexes
CREATE INDEX idx_access_logs_user_time ON access_logs(user_id, event_time);
CREATE INDEX idx_trust_scores_user ON trust_scores(user_id, computed_at DESC);
CREATE INDEX idx_alerts_status ON alerts(status);

-- Seed data for policy_rules
INSERT INTO policy_rules (id, rule_name, threshold_min, threshold_max, action, active) VALUES
('a0e8140d-d684-4860-84c1-2ba6d934bb61', 'restrict', 0, 40, 'restrict', true),
('b5fbf104-e3f3-470b-85be-587265bf02ab', 'require_mfa', 40, 70, 'require_mfa', true),
('c65d836d-1bf8-466c-be7d-78a05c317db6', 'allow', 70, 101, 'allow', true);
