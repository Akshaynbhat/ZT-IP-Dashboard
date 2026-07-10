import React, { useState, useEffect } from "react";
import { useUsers } from "../hooks/useUsers";
import { getUserHistory, getExplanation } from "../api/client";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { SHAPChart } from "../components/SHAPChart";
import { RiskBadge } from "../components/RiskBadge";
import { User, TrustScore, UserHistory, Explanation } from "../types";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea,
  ReferenceLine,
} from "recharts";
import { AlertTriangle, Info, X } from "lucide-react";

export function TrustScoreViz() {
  const { data: users, loading: loadingUsers, error: errorUsers } = useUsers();
  
  const [selectedUserId, setSelectedUserId] = useState<string>("");
  const [history, setHistory] = useState<UserHistory | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [errorHistory, setErrorHistory] = useState(false);

  // Modal explanation states
  const [selectedScoreId, setSelectedScoreId] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [loadingExplanation, setLoadingExplanation] = useState(false);
  const [showModal, setShowModal] = useState(false);

  const isDemoMode = errorUsers || !users || errorHistory;
  const activeUsers = isDemoMode ? MOCK_USERS : users || [];

  // Handle user select dropdown
  useEffect(() => {
    if (activeUsers.length > 0 && !selectedUserId) {
      setSelectedUserId(activeUsers[0].id);
    }
  }, [activeUsers, selectedUserId]);

  // Load selected user history
  useEffect(() => {
    if (selectedUserId) {
      setLoadingHistory(true);
      getUserHistory(selectedUserId)
        .then((res) => {
          setHistory(res);
          setErrorHistory(false);
        })
        .catch((err) => {
          console.error("Failed to load user history", err);
          setErrorHistory(true);
          // Load mock history
          const mockHist = generateMockHistory(selectedUserId);
          setHistory(mockHist);
        })
        .finally(() => {
          setLoadingHistory(false);
        });
    }
  }, [selectedUserId]);

  const handleChartClick = async (state: any) => {
    if (state && state.activePayload && state.activePayload[0]) {
      const pointData = state.activePayload[0].payload;
      const scoreId = pointData.id;
      
      setSelectedScoreId(scoreId);
      setLoadingExplanation(true);
      setShowModal(true);

      try {
        const exp = await getExplanation(scoreId);
        setExplanation(exp);
      } catch (err) {
        console.error("Failed to fetch SHAP explanation:", err);
        // Fallback mock explanation
        const mockExp = generateMockExplanation(pointData.trust_score);
        setExplanation(mockExp);
      } finally {
        setLoadingExplanation(false);
      }
    }
  };

  if (loadingUsers && !isDemoMode) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-white">Loading Score Visualizations...</h2>
        <LoadingSkeleton rows={8} />
      </div>
    );
  }

  // Format timestamps for the X-Axis
  const chartData = history
    ? [...history.trust_scores].reverse().map((s) => {
        const d = new Date(s.computed_at);
        const mm = String(d.getMonth() + 1).padStart(2, "0");
        const dd = String(d.getDate()).padStart(2, "0");
        const hh = String(d.getHours()).padStart(2, "0");
        const min = String(d.getMinutes()).padStart(2, "0");
        return {
          ...s,
          formatted_time: `${mm}/${dd} ${hh}:${min}`,
        };
      })
    : [];

  // Determine line color of the latest score point
  let lineColor = "#10B981"; // green
  if (chartData.length > 0) {
    const latestScoreVal = chartData[chartData.length - 1].trust_score;
    if (latestScoreVal < 40) lineColor = "#EF4444"; // red
    else if (latestScoreVal < 70) lineColor = "#F59E0B"; // yellow
  }

  return (
    <div className="space-y-6">
      {isDemoMode && (
        <div className="bg-yellow-950/40 border border-yellow-800 text-yellow-300 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0 text-brand-yellow" />
          <span className="text-sm font-medium">
            ⚠ Demo Mode — showing simulated history visualizer.
          </span>
        </div>
      )}

      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white">Trust Score Timelines</h1>
          <p className="text-sm text-gray-400 mt-1">
            Analyze mathematical variance bands and click points to explain rating drops.
          </p>
        </div>

        {/* User Select Dropdown */}
        <div className="flex items-center gap-2">
          <label htmlFor="user-select" className="text-xs font-bold text-gray-400 uppercase">
            Select Account:
          </label>
          <select
            id="user-select"
            value={selectedUserId}
            onChange={(e) => setSelectedUserId(e.target.value)}
            className="bg-gray-800 border border-gray-700 text-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-green"
          >
            {activeUsers.map((u) => (
              <option key={u.id} value={u.id}>
                {u.username} ({u.department})
              </option>
            ))}
          </select>
        </div>
      </div>

      {loadingHistory ? (
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-8 h-[400px] flex flex-col justify-center">
          <h4 className="text-gray-400 text-sm mb-4 font-semibold text-center">
            Retrieving score history...
          </h4>
          <LoadingSkeleton rows={4} />
        </div>
      ) : history ? (
        <div className="space-y-6">
          {/* Main LineChart Card */}
          <div className="bg-gray-800 border border-gray-700 rounded-xl shadow-lg p-6">
            <div className="flex items-center gap-2 text-gray-400 text-xs mb-6 bg-gray-900/40 p-3 rounded-lg border border-gray-850">
              <Info className="w-4 h-4 text-brand-yellow shrink-0" />
              <span>
                <strong>Interaction Instructions:</strong> Click directly on any node point on the timeline chart to display the explainable SHAP contribution breakdown factors.
              </span>
            </div>

            <div className="h-[350px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={chartData}
                  onClick={handleChartClick}
                  margin={{ top: 20, right: 20, left: -20, bottom: 5 }}
                >
                  <XAxis
                    dataKey="formatted_time"
                    stroke="#9CA3AF"
                    fontSize={10}
                    tickLine={false}
                  />
                  <YAxis
                    domain={[0, 100]}
                    stroke="#9CA3AF"
                    fontSize={10}
                    tickLine={false}
                    ticks={[0, 20, 40, 60, 70, 80, 100]}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1F2937",
                      borderColor: "#374151",
                      borderRadius: "8px",
                    }}
                    labelStyle={{ color: "#9CA3AF", fontWeight: "bold" }}
                    formatter={(val: any) => [`Score: ${Number(val).toFixed(1)}`, "Trust Level"]}
                  />
                  {/* Reference Areas defining the 3 Policy bands */}
                  <ReferenceArea y1={0} y2={40} fill="#EF4444" fillOpacity={0.06} />
                  <ReferenceArea y1={40} y2={70} fill="#F59E0B" fillOpacity={0.06} />
                  <ReferenceArea y1={70} y2={100} fill="#10B981" fillOpacity={0.06} />

                  {/* Highlight dashed lines at policy boundaries */}
                  <ReferenceLine y={40} stroke="#EF4444" strokeDasharray="3 3" />
                  <ReferenceLine y={70} stroke="#F59E0B" strokeDasharray="3 3" />

                  <Line
                    type="monotone"
                    dataKey="trust_score"
                    stroke={lineColor}
                    strokeWidth={3}
                    activeDot={{ r: 8, cursor: "pointer" }}
                    dot={{ r: 5, strokeWidth: 2, cursor: "pointer" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-gray-800 border border-gray-700 rounded-xl p-12 text-center text-gray-500">
          No history profile data found for this account.
        </div>
      )}

      {/* SHAP EXPLANATION MODAL PANEL */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-fadeIn">
          <div className="bg-gray-800 border border-gray-700 rounded-xl shadow-2xl w-full max-w-xl overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-gray-700 p-5 bg-gray-850">
              <div>
                <h3 className="font-extrabold text-lg text-white">Decision Explanation</h3>
                <span className="text-[10px] text-gray-400 tracking-wider font-semibold uppercase">
                  Log ID: {selectedScoreId?.slice(0, 18)}...
                </span>
              </div>
              <button
                onClick={() => {
                  setShowModal(false);
                  setExplanation(null);
                }}
                className="text-gray-400 hover:text-white hover:bg-gray-700/50 p-1.5 rounded-lg transition-all"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-6">
              {loadingExplanation ? (
                <div className="space-y-4 py-8">
                  <h4 className="text-sm font-semibold text-gray-400 text-center animate-pulse">
                    Computing SHAP values...
                  </h4>
                  <LoadingSkeleton rows={3} />
                </div>
              ) : explanation ? (
                <div className="space-y-6">
                  {/* Summary Badges Grid */}
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div className="bg-gray-900/40 border border-gray-750 p-3 rounded-lg">
                      <span className="text-[9px] font-bold text-gray-500 uppercase tracking-widest block">
                        Risk Class
                      </span>
                      <div className="mt-2">
                        <RiskBadge riskClass={explanation.risk_class} />
                      </div>
                    </div>

                    <div className="bg-gray-900/40 border border-gray-750 p-3 rounded-lg">
                      <span className="text-[9px] font-bold text-gray-500 uppercase tracking-widest block">
                        Probability
                      </span>
                      <span className="text-base font-extrabold text-white mt-1 block">
                        {(explanation.risk_probability * 100).toFixed(1)}%
                      </span>
                    </div>

                    <div className="bg-gray-900/40 border border-gray-750 p-3 rounded-lg">
                      <span className="text-[9px] font-bold text-gray-500 uppercase tracking-widest block">
                        Anomaly Score
                      </span>
                      <span className="text-base font-extrabold text-white mt-1 block">
                        {explanation.anomaly_score.toFixed(3)}
                      </span>
                    </div>
                  </div>

                  {/* SHAP Chart */}
                  <SHAPChart features={explanation.shap_top_features} />
                </div>
              ) : (
                <div className="text-center py-6 text-red-400 text-sm">
                  Failed to fetch SHAP explanations for this node score.
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="bg-gray-850 border-t border-gray-700 px-6 py-4 flex justify-end">
              <button
                onClick={() => {
                  setShowModal(false);
                  setExplanation(null);
                }}
                className="bg-gray-700 hover:bg-gray-650 text-white font-bold text-xs px-4 py-2 rounded-md transition-all"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
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

// Mock histories generator
function generateMockHistory(userId: string): UserHistory {
  const user = MOCK_USERS.find((u) => u.id === userId) || MOCK_USERS[0];
  const base = user.current_trust_score || 85.0;

  const trust_scores: TrustScore[] = Array.from({ length: 8 }).map((_, i) => ({
    id: `ts-viz-${userId}-${i}`,
    user_id: userId,
    trust_score: Math.max(0, Math.min(100, base - i * (userId === "u5" ? 10 : 1.5))),
    anomaly_component: 0.1,
    risk_component: 0.1,
    computed_at: new Date(Date.now() - i * 4 * 3600000).toISOString(),
  }));

  return { user, trust_scores, recent_events: [] };
}

const MOCK_USERS: User[] = [
  { id: "u1", username: "alice.dev", email: "alice@zt-enterprise.io", role: "employee", department: "Engineering", created_at: "2026-07-09T08:00:00Z", current_trust_score: 95.0 },
  { id: "u2", username: "bob.dev", email: "bob@zt-enterprise.io", role: "employee", department: "Engineering", created_at: "2026-07-09T08:05:00Z", current_trust_score: 82.3 },
  { id: "u3", username: "charlie.ops", email: "charlie@zt-enterprise.io", role: "employee", department: "DevOps", created_at: "2026-07-09T08:10:00Z", current_trust_score: 74.1 },
  { id: "u4", username: "diana.sec", email: "diana@zt-enterprise.io", role: "analyst", department: "Security", created_at: "2026-07-09T08:15:00Z", current_trust_score: 88.0 },
  { id: "u5", username: "eve.insider", email: "eve@zt-enterprise.io", role: "employee", department: "Engineering", created_at: "2026-07-09T08:20:00Z", current_trust_score: 18.2 },
];
export default TrustScoreViz;
