import { useState } from "react";
import { getUsername } from "../auth/keycloak";
import { useAlerts } from "../hooks/useAlerts";
import { updateAlert, getExplanation } from "../api/client";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { SeverityBadge } from "../components/SeverityBadge";
import { TrustScoreBadge } from "../components/TrustScoreBadge";
import { SHAPChart } from "../components/SHAPChart";
import { Alert, Explanation } from "../types";
import { AlertTriangle, ChevronDown, ChevronUp, Clock, User, Filter } from "lucide-react";

export function AlertDashboard() {
  const currentAnalyst = getUsername();

  // Filters state
  const [severityFilter, setSeverityFilter] = useState<string>("all");

  const { data: alerts, loading: loadingAlerts, refresh: refreshAlerts, error: errorAlerts } = useAlerts();

  // Expanded card & explanation cache state
  const [expandedAlertId, setExpandedAlertId] = useState<string | null>(null);
  const [loadingExplanation, setLoadingExplanation] = useState(false);
  const [explanations, setExplanations] = useState<Record<string, Explanation>>({});



  const isDemoMode = (errorAlerts || (alerts && alerts.length === 0)) && !loadingAlerts;
  const activeAlerts = isDemoMode ? MOCK_ALERTS : alerts || [];

  // Severity filter client-side processing
  const filteredAlerts = activeAlerts.filter((alert) => {
    if (severityFilter === "all") return true;
    return alert.severity.toLowerCase() === severityFilter.toLowerCase();
  });

  const columns = [
    { id: "open", title: "Open Issues" },
    { id: "reviewed", title: "Reviewed" },
    { id: "escalated", title: "Escalated" },
    { id: "dismissed", title: "Dismissed" },
  ];

  // Compute alerts in each column
  const alertsByColumn = columns.reduce((acc, col) => {
    acc[col.id] = filteredAlerts.filter((a) => a.status.toLowerCase() === col.id);
    return acc;
  }, {} as Record<string, Alert[]>);

  const handleStatusChange = async (alertId: string, nextStatus: string) => {
    try {
      await updateAlert(alertId, nextStatus, currentAnalyst);
      refreshAlerts();
    } catch (err) {
      console.error(`Failed to transition status for alert ${alertId}:`, err);
      if (isDemoMode) {
        // Mock updates locally in demo mode
        const alertIdx = MOCK_ALERTS.findIndex((a) => a.id === alertId);
        if (alertIdx > -1) {
          MOCK_ALERTS[alertIdx].status = nextStatus;
          MOCK_ALERTS[alertIdx].reviewed_by = currentAnalyst;
          MOCK_ALERTS[alertIdx].reviewed_at = new Date().toISOString();
        }
        refreshAlerts();
      }
    }
  };

  const handleCardExpand = async (alert: Alert) => {
    const isExpanding = expandedAlertId !== alert.id;
    setExpandedAlertId(isExpanding ? alert.id : null);

    if (isExpanding && !explanations[alert.id]) {
      setLoadingExplanation(true);
      try {
        const scoreIdToUse = isDemoMode ? "mock-score" : (alert.trust_score_id || "");

        if (scoreIdToUse) {
          const exp = await getExplanation(scoreIdToUse);
          setExplanations((prev) => ({ ...prev, [alert.id]: exp }));
        } else {
          throw new Error("Unable to map alert to a score log ID.");
        }
      } catch (err) {
        console.warn("Falling back to simulated SHAP data:", err);
        const mockExp = generateMockExplanation(alert.trust_score ?? 50);
        setExplanations((prev) => ({ ...prev, [alert.id]: mockExp }));
      } finally {
        setLoadingExplanation(false);
      }
    }
  };



  if (loadingAlerts && !isDemoMode) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-white">Loading Security Incidents...</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <LoadingSkeleton rows={4} />
          <LoadingSkeleton rows={4} />
          <LoadingSkeleton rows={4} />
          <LoadingSkeleton rows={4} />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {isDemoMode && (
        <div className="bg-yellow-950/40 border border-yellow-800 text-yellow-300 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0 text-brand-yellow" />
          <span className="text-sm font-medium">
            ⚠ Demo Mode — showing simulated security threat queues.
          </span>
        </div>
      )}

      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white">Alert Board</h1>
          <p className="text-sm text-gray-400 mt-1">
            Perform case reviews, audit anomaly factors, and transition status in Kanban pipelines.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => window.open("/api/v1/reports/access-logs/csv", "_blank")}
            className="text-xs font-bold bg-blue-950/40 border border-blue-800 hover:bg-blue-900/40 text-blue-300 px-3.5 py-2 rounded-lg transition-all"
          >
            Export Logs (CSV)
          </button>
          <button
            onClick={() => window.open("/api/v1/reports/trust-scores/csv", "_blank")}
            className="text-xs font-bold bg-cyan-950/40 border border-cyan-800 hover:bg-cyan-900/40 text-cyan-300 px-3.5 py-2 rounded-lg transition-all"
          >
            Export Scores (CSV)
          </button>
        </div>
      </div>


      {/* Filter Bar */}
      <div className="flex flex-wrap gap-2 items-center bg-gray-800/40 border border-gray-700 rounded-xl p-4">
        <span className="text-xs font-bold text-gray-400 uppercase mr-2 flex items-center gap-1.5">
          <Filter className="w-3.5 h-3.5" /> Severity Filter:
        </span>
        {["all", "critical", "high", "medium", "low"].map((sev) => (
          <button
            key={sev}
            onClick={() => setSeverityFilter(sev)}
            className={`text-xs font-bold px-3 py-1.5 rounded-lg border transition-all ${
              severityFilter === sev
                ? "bg-gray-700 border-gray-500 text-white shadow-inner"
                : "bg-gray-800 border-gray-700 text-gray-400 hover:text-white"
            }`}
          >
            {sev.toUpperCase()}
          </button>
        ))}
      </div>

      {/* Kanban Board Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {columns.map((col) => {
          const colAlerts = alertsByColumn[col.id] || [];
          return (
            <div
              key={col.id}
              className="bg-gray-900 border border-gray-800 rounded-xl flex flex-col min-h-[500px]"
            >
              {/* Column Header */}
              <div className="flex items-center justify-between border-b border-gray-800 px-4 py-3 bg-gray-900/50">
                <h3 className="font-extrabold text-sm text-white flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-gray-600" />
                  {col.title}
                </h3>
                <span className="bg-gray-800 text-gray-400 rounded-full px-2 py-0.5 text-xs font-bold">
                  {colAlerts.length}
                </span>
              </div>

              {/* Cards Container */}
              <div className="p-4 space-y-4 flex-1 overflow-y-auto max-h-[600px]">
                {colAlerts.map((alert) => {
                  const isExpanded = expandedAlertId === alert.id;
                  const explanationData = explanations[alert.id];

                  // Define action transitions based on state machine
                  const transitions: string[] = [];
                  const statusLower = alert.status.toLowerCase();
                  if (statusLower === "open") {
                    transitions.push("reviewed", "escalated", "dismissed");
                  } else if (statusLower === "reviewed") {
                    transitions.push("escalated", "dismissed");
                  } else if (statusLower === "escalated") {
                    transitions.push("reviewed", "dismissed");
                  }

                  return (
                    <div
                      key={alert.id}
                      onClick={() => handleCardExpand(alert)}
                      className={`bg-gray-800 border border-gray-700 rounded-lg p-4 shadow-md cursor-pointer hover:border-gray-500 transition-all select-none relative ${
                        isExpanded ? "ring-1 ring-brand-green border-transparent" : ""
                      }`}
                    >
                      {/* Top Row: User & Severity */}
                      <div className="flex items-start justify-between">
                        <div className="overflow-hidden pr-2">
                          <h4 className="font-extrabold text-white text-sm truncate">
                            {alert.username || "Unknown User"}
                          </h4>
                          <span className="text-[10px] text-gray-500 font-medium font-mono">
                            {alert.id.slice(0, 8)}...
                          </span>
                        </div>
                        <SeverityBadge severity={alert.severity} />
                      </div>

                      {/* Middle Row: Score & Date */}
                      <div className="flex items-center justify-between mt-4">
                        <div className="flex items-center gap-2">
                          <TrustScoreBadge score={alert.trust_score} size="sm" />
                          <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">
                            Score Rated
                          </span>
                        </div>
                        <div className="flex items-center gap-1 text-[11px] text-gray-500 font-semibold">
                          <Clock className="w-3 h-3" />
                          {timeAgo(alert.created_at)}
                        </div>
                      </div>

                      {/* Expand Indicator */}
                      <div className="text-center text-[10px] text-gray-500 font-bold uppercase tracking-wider pt-2 border-t border-gray-700/50 mt-4 hover:text-white flex items-center justify-center gap-1">
                        {isExpanded ? (
                          <>
                            Collapse Details <ChevronUp className="w-3.5 h-3.5" />
                          </>
                        ) : (
                          <>
                            Explain Anomaly <ChevronDown className="w-3.5 h-3.5" />
                          </>
                        )}
                      </div>

                      {/* Expanded SHAP Section */}
                      {isExpanded && (
                        <div
                          className="mt-4 pt-4 border-t border-gray-700 space-y-4"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {loadingExplanation ? (
                            <div className="space-y-2 py-4">
                              <span className="text-xs font-semibold text-gray-400 text-center animate-pulse block">
                                Loading explainability...
                              </span>
                              <LoadingSkeleton rows={2} />
                            </div>
                          ) : explanationData ? (
                            <div className="space-y-4">
                              <div className="grid grid-cols-2 gap-2 text-center text-xs">
                                <div className="bg-gray-900/60 p-2 rounded border border-gray-750">
                                  <span className="text-[8px] font-bold text-gray-500 block uppercase">
                                    Risk Probability
                                  </span>
                                  <span className="text-xs font-bold text-white">
                                    {(explanationData.risk_probability * 100).toFixed(1)}%
                                  </span>
                                </div>
                                <div className="bg-gray-900/60 p-2 rounded border border-gray-750">
                                  <span className="text-[8px] font-bold text-gray-500 block uppercase">
                                    Anomaly Score
                                  </span>
                                  <span className="text-xs font-bold text-white">
                                    {explanationData.anomaly_score.toFixed(3)}
                                  </span>
                                </div>
                              </div>
                              <SHAPChart features={explanationData.shap_top_features} />
                            </div>
                          ) : (
                            <span className="text-xs text-red-400 block text-center">
                              Explanation load failed.
                            </span>
                          )}
                        </div>
                      )}

                      {/* Action transition buttons */}
                      {transitions.length > 0 && (
                        <div className="mt-4 pt-3 border-t border-gray-700/50 flex flex-wrap gap-1.5 justify-end" onClick={(e) => e.stopPropagation()}>
                          {transitions.map((status) => {
                            let btnColor = "bg-gray-700 hover:bg-gray-600 text-gray-200";
                            if (status === "reviewed") btnColor = "bg-emerald-950/50 hover:bg-emerald-900/60 text-emerald-400 border border-emerald-800";
                            if (status === "escalated") btnColor = "bg-amber-950/50 hover:bg-amber-900/60 text-amber-400 border border-amber-800";
                            if (status === "dismissed") btnColor = "bg-gray-900/80 hover:bg-gray-850 text-gray-400 border border-gray-700";
                            
                            return (
                              <button
                                key={status}
                                onClick={() => handleStatusChange(alert.id, status)}
                                className={`text-[10px] font-extrabold uppercase px-2.5 py-1 rounded transition-colors ${btnColor}`}
                              >
                                {status}
                              </button>
                            );
                          })}
                        </div>
                      )}


                      {/* Review Status Details (If not open) */}
                      {alert.reviewed_by && (
                        <div className="mt-4 pt-3 border-t border-gray-750 flex items-center gap-1.5 text-[10px] text-gray-500 font-semibold italic">
                          <User className="w-3 h-3 text-gray-400" />
                          <span>
                            Reviewed by {alert.reviewed_by}
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })}
                {colAlerts.length === 0 && (
                  <div className="py-12 text-center text-gray-600 text-xs border-2 border-dashed border-gray-800 rounded-lg">
                    No alerts in this category.
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Helper to calculate relative times
function timeAgo(dateString: string): string {
  const now = new Date();
  const past = new Date(dateString);
  const diffMs = now.getTime() - past.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHr = Math.floor(diffMin / 60);
  const diffDays = Math.floor(diffHr / 24);

  if (diffSec < 60) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  if (diffHr < 24) return `${diffHr}h ago`;
  return `${diffDays}d ago`;
}

// Generate mock explanations dynamically if API is down
function generateMockExplanation(scoreVal: number): Explanation {
  const isSuspicious = scoreVal < 60;
  return {
    shap_top_features: isSuspicious
      ? [
          { feature: "is_off_hours", shap_value: 0.28, direction: "increase" },
          { feature: "bytes_transferred_24h", shap_value: 0.19, direction: "increase" },
          { feature: "files_downloaded_count", shap_value: 0.12, direction: "increase" },
        ]
      : [
          { feature: "is_known_device", shap_value: -0.22, direction: "decrease" },
          { feature: "hours_since_last_login", shap_value: -0.11, direction: "decrease" },
          { feature: "login_time_deviation", shap_value: 0.03, direction: "increase" },
        ],
    risk_class: scoreVal < 40 ? "high" : scoreVal < 70 ? "medium" : "low",
    risk_probability: scoreVal < 40 ? 0.88 : scoreVal < 70 ? 0.48 : 0.08,
    anomaly_score: scoreVal < 40 ? 0.912 : scoreVal < 70 ? 0.482 : 0.065,
  };
}

// Mock Alert Array
const MOCK_ALERTS: Alert[] = [
  { id: "a1", severity: "critical", status: "open", created_at: new Date(Date.now() - 3600000).toISOString(), reviewed_by: null, reviewed_at: null, trust_score: 18.2, username: "eve.insider" },
  { id: "a2", severity: "medium", status: "open", created_at: new Date(Date.now() - 7200000).toISOString(), reviewed_by: null, reviewed_at: null, trust_score: 55.4, username: "charlie.ops" },
  { id: "a3", severity: "high", status: "reviewed", created_at: new Date(Date.now() - 14400000).toISOString(), reviewed_by: "test.analyst", reviewed_at: new Date(Date.now() - 10800000).toISOString(), trust_score: 35.5, username: "bob.dev" },
];
export default AlertDashboard;
