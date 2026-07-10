import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { hasRole, getUserId, getUsername } from "../auth/keycloak";
import { useUsers } from "../hooks/useUsers";
import { useScores } from "../hooks/useScores";
import { useAlerts } from "../hooks/useAlerts";
import { getUserHistory } from "../api/client";
import { StatCard } from "../components/StatCard";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { TrustScoreBadge } from "../components/TrustScoreBadge";
import { RiskBadge } from "../components/RiskBadge";
import { User, TrustScore, Alert, UserHistory } from "../types";
import { AlertTriangle, Users, BarChart3, ShieldAlert, FileText, Globe } from "lucide-react";

export function Overview() {
  const navigate = useNavigate();
  const isSecurityStaff = hasRole("admin") || hasRole("analyst");
  const employeeId = getUserId();
  const username = getUsername();

  // 1. Data hooks for Security Staff
  const { data: users, loading: loadingUsers, error: errorUsers } = useUsers();
  const { data: scores, loading: loadingScores, error: errorScores } = useScores();
  const { data: alerts, loading: loadingAlerts, error: errorAlerts } = useAlerts();

  // 2. Data hooks for Employee role
  const [employeeHistory, setEmployeeHistory] = useState<UserHistory | null>(null);
  const [loadingEmployee, setLoadingEmployee] = useState(true);
  const [employeeError, setEmployeeError] = useState(false);

  useEffect(() => {
    if (!isSecurityStaff && employeeId) {
      setLoadingEmployee(true);
      getUserHistory(employeeId)
        .then((res) => {
          setEmployeeHistory(res);
          setEmployeeError(false);
        })
        .catch((err) => {
          console.error("Failed to load employee history", err);
          setEmployeeError(true);
        })
        .finally(() => {
          setLoadingEmployee(false);
        });
    }
  }, [isSecurityStaff, employeeId]);

  // Check if any error triggered Demo/Mock mode
  const isDemoMode =
    (isSecurityStaff && (errorUsers || errorScores || errorAlerts || !users || !scores)) ||
    (!isSecurityStaff && (employeeError || !employeeHistory));

  // Determine active datasets
  const activeUsers = isDemoMode ? MOCK_USERS : users || [];
  const activeScores = isDemoMode ? MOCK_SCORES : scores || [];
  const activeAlerts = isDemoMode ? MOCK_ALERTS : alerts || [];

  // Calculate stats for Security Staff
  const totalUsers = activeUsers.length;
  const openAlerts = activeAlerts.filter((a) => a.status === "open").length;
  const criticalAlerts = activeAlerts.filter((a) => a.severity === "critical").length;
  
  const validScores = activeScores.map((s) => s.trust_score);
  const avgTrustScore =
    validScores.length > 0
      ? (validScores.reduce((a, b) => a + b, 0) / validScores.length).toFixed(1)
      : "—";

  // Build Riskiest Users list
  const riskiestScores = activeScores.slice(0, 5); // Sorted ascending by backend
  const riskiestUsersJoined = riskiestScores.map((score) => {
    const userMatch = activeUsers.find((u) => u.id === score.user_id);
    return {
      scoreId: score.id,
      userId: score.user_id,
      username: userMatch?.username || `User ${score.user_id.slice(0, 8)}`,
      department: userMatch?.department || "Unknown",
      trustScore: score.trust_score,
      riskClass: score.trust_score < 40 ? "High" : score.trust_score < 70 ? "Medium" : "Low",
    };
  });

  // Loading states
  const showLoader = isSecurityStaff
    ? loadingUsers || loadingScores || loadingAlerts
    : loadingEmployee;

  if (showLoader && !isDemoMode) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-white">Loading Security Telemetry...</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <LoadingSkeleton rows={2} />
          <LoadingSkeleton rows={2} />
          <LoadingSkeleton rows={2} />
          <LoadingSkeleton rows={2} />
        </div>
        <LoadingSkeleton rows={8} className="mt-8" />
      </div>
    );
  }

  // --- RENDER EMPLOYEE LAYOUT ---
  if (!isSecurityStaff) {
    const currentScore = isDemoMode
      ? 82.3
      : employeeHistory?.user.current_trust_score;
    const recentEvents = isDemoMode
      ? MOCK_EVENTS
      : employeeHistory?.recent_events || [];

    return (
      <div className="space-y-6">
        {/* Employee Banner */}
        <div className="bg-yellow-950/40 border border-yellow-800 text-yellow-300 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0 text-brand-yellow" />
          <span className="text-sm font-medium">
            Standard Employee Access: You only have access to your own personal security summary view.
          </span>
        </div>

        {isDemoMode && (
          <div className="bg-blue-950/40 border border-blue-800 text-blue-300 rounded-lg p-3 text-xs font-semibold">
            ⚠ Demo Mode — showing sample data for {username}
          </div>
        )}

        <h1 className="text-3xl font-extrabold text-white">Employee Security Summary</h1>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-gray-800 border border-gray-700 rounded-xl p-6 flex items-center justify-between">
            <div>
              <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block">
                My Security Trust Score
              </span>
              <span className="text-xs text-gray-500 mt-1 block">
                Evaluated against peer behavior baselines
              </span>
            </div>
            <TrustScoreBadge score={currentScore} size="lg" />
          </div>

          <StatCard
            title="My Logged Actions (24h)"
            value={recentEvents.length}
            subtitle="Access logs tracked for authentication audits"
            color="#3B82F6"
          />
        </div>

        {/* Employee Recent Audit Logs */}
        <div className="bg-gray-800 border border-gray-700 rounded-xl shadow-lg p-6">
          <h2 className="text-lg font-bold text-white mb-4">My Recent Activity History</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-gray-700 text-gray-400 font-medium">
                  <th className="py-3 px-4">Time</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Resource</th>
                  <th className="py-3 px-4">IP Address</th>
                  <th className="py-3 px-4">Location</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700 text-gray-300">
                {recentEvents.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-750/30">
                    <td className="py-3 px-4">{new Date(log.event_time).toLocaleString()}</td>
                    <td className="py-3 px-4 uppercase font-semibold text-xs text-gray-400">
                      {log.event_type}
                    </td>
                    <td className="py-3 px-4 font-mono text-xs">{log.resource || "—"}</td>
                    <td className="py-3 px-4 text-xs">{log.ip_address || "—"}</td>
                    <td className="py-3 px-4 text-xs">{log.location || "—"}</td>
                  </tr>
                ))}
                {recentEvents.length === 0 && (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-gray-500">
                      No activity logs detected in the last 24 hours.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  }

  // --- RENDER SECURITY STAFF LAYOUT ---
  return (
    <div className="space-y-8">
      {isDemoMode && (
        <div className="bg-yellow-950/40 border border-yellow-800 text-yellow-300 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0 text-brand-yellow animate-pulse" />
          <span className="text-sm font-medium">
            ⚠ Demo Mode — showing sample security logs and simulated baseline metrics.
          </span>
        </div>
      )}

      <div>
        <h1 className="text-3xl font-extrabold text-white">System Security Overview</h1>
        <p className="text-sm text-gray-400 mt-1">
          Zero Trust dynamic score evaluations and developer activity audits.
        </p>
      </div>

      {/* KPI Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard
          title="Monitored Accounts"
          value={totalUsers}
          subtitle="Active Keycloak developer identities"
          color="#3B82F6"
        />
        <StatCard
          title="Open Alerts"
          value={openAlerts}
          subtitle="Alerts awaiting security analyst review"
          color={openAlerts > 0 ? "#F59E0B" : "#10B981"}
        />
        <StatCard
          title="Avg System Trust"
          value={avgTrustScore}
          subtitle="Overall workforce trust rating"
          color={typeof avgTrustScore === "string" && Number(avgTrustScore) < 60 ? "#EF4444" : "#10B981"}
        />
        <StatCard
          title="Critical Incidents"
          value={criticalAlerts}
          subtitle="Alerts with high threat severity ratings"
          color={criticalAlerts > 0 ? "#7C3AED" : "#9CA3AF"}
        />
      </div>

      {/* Riskiest Users Table */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-white">Riskiest Active Profiles</h2>
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
            Lowest Trust Score First
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm border-collapse">
            <thead>
              <tr className="border-b border-gray-700 text-gray-400 font-medium">
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">Department</th>
                <th className="py-3 px-4">Dynamic Rating</th>
                <th className="py-3 px-4">Risk Class</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700 text-gray-300">
              {riskiestUsersJoined.map((rUser) => (
                <tr
                  key={rUser.userId}
                  className="hover:bg-gray-750/30 cursor-pointer"
                  onClick={() => navigate("/risk", { state: { highlightUserId: rUser.userId } })}
                >
                  <td className="py-4 px-4 font-bold text-white">{rUser.username}</td>
                  <td className="py-4 px-4">{rUser.department}</td>
                  <td className="py-4 px-4">
                    <TrustScoreBadge score={rUser.trustScore} size="sm" />
                  </td>
                  <td className="py-4 px-4">
                    <RiskBadge riskClass={rUser.riskClass} />
                  </td>
                  <td className="py-4 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => navigate("/risk", { state: { highlightUserId: rUser.userId } })}
                      className="text-xs font-bold text-brand-green border border-brand-green/30 hover:bg-brand-green/10 rounded-md px-3 py-1.5 transition-all duration-150"
                    >
                      Audit History
                    </button>
                  </td>
                </tr>
              ))}
              {riskiestUsersJoined.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-6 text-center text-gray-500">
                    No risk score calculations computed in the database.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ==========================================
//               MOCK DATA
// ==========================================
const MOCK_USERS: User[] = [
  { id: "u1", username: "alice.dev", email: "alice@zt.enterprise.io", role: "employee", department: "Engineering", created_at: "2026-07-09T08:00:00Z", current_trust_score: 95.0 },
  { id: "u2", username: "bob.dev", email: "bob@zt.enterprise.io", role: "employee", department: "Engineering", created_at: "2026-07-09T08:05:00Z", current_trust_score: 82.3 },
  { id: "u3", username: "charlie.ops", email: "charlie@zt.enterprise.io", role: "employee", department: "DevOps", created_at: "2026-07-09T08:10:00Z", current_trust_score: 74.1 },
  { id: "u4", username: "diana.sec", email: "diana@zt.enterprise.io", role: "analyst", department: "Security", created_at: "2026-07-09T08:15:00Z", current_trust_score: 88.0 },
  { id: "u5", username: "eve.insider", email: "eve@zt.enterprise.io", role: "employee", department: "Engineering", created_at: "2026-07-09T08:20:00Z", current_trust_score: 18.2 },
];

const MOCK_SCORES: TrustScore[] = [
  { id: "s1", user_id: "u5", trust_score: 18.2, anomaly_component: 0.38, risk_component: 0.4, computed_at: "2026-07-09T08:29:00Z" },
  { id: "s2", user_id: "u3", trust_score: 74.1, anomaly_component: 0.1, risk_component: 0.1, computed_at: "2026-07-09T08:12:00Z" },
  { id: "s3", user_id: "u2", trust_score: 82.3, anomaly_component: 0.08, risk_component: 0.09, computed_at: "2026-07-09T08:15:00Z" },
  { id: "s4", user_id: "u4", trust_score: 88.0, anomaly_component: 0.05, risk_component: 0.07, computed_at: "2026-07-09T08:25:00Z" },
  { id: "s5", user_id: "u1", trust_score: 95.0, anomaly_component: 0.02, risk_component: 0.03, computed_at: "2026-07-09T08:30:00Z" },
];

const MOCK_ALERTS: Alert[] = [
  { id: "a1", severity: "critical", status: "open", created_at: "2026-07-09T08:29:05Z", reviewed_by: null, reviewed_at: null, trust_score: 18.2, username: "eve.insider" },
  { id: "a2", severity: "medium", status: "open", created_at: "2026-07-09T08:12:15Z", reviewed_by: null, reviewed_at: null, trust_score: 74.1, username: "charlie.ops" },
  { id: "a3", severity: "high", status: "reviewed", created_at: "2026-07-09T08:16:10Z", reviewed_by: "test.analyst", reviewed_at: "2026-07-09T08:30:00Z", trust_score: 35.5, username: "bob.dev" },
];

const MOCK_EVENTS: AccessLog[] = [
  { id: "e1", user_id: "u1", device_id: "d1", event_type: "login", resource: "okta-auth", bytes_transferred: 0, event_time: "2026-07-09T08:00:00Z", ip_address: "10.0.0.103", location: "Bengaluru, IN" },
  { id: "e2", user_id: "u1", device_id: "d1", event_type: "repo_access", resource: "api-gateway", bytes_transferred: 0, event_time: "2026-07-09T08:05:00Z", ip_address: "10.0.0.103", location: "Bengaluru, IN" },
  { id: "e3", user_id: "u1", device_id: "d1", event_type: "file_download", resource: "api-gateway/src/main.py", bytes_transferred: 245000, event_time: "2026-07-09T08:10:00Z", ip_address: "10.0.0.103", location: "Bengaluru, IN" },
];
export default Overview;
