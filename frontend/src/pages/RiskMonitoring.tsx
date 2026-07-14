import React, { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useUsers } from "../hooks/useUsers";
import { useScores } from "../hooks/useScores";
import { getUserHistory } from "../api/client";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { TrustScoreBadge } from "../components/TrustScoreBadge";
import { RiskBadge } from "../components/RiskBadge";
import { User, TrustScore, UserHistory, AccessLog } from "../types";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Search, ChevronDown, ChevronUp, ArrowUp, ArrowDown, ArrowRight, AlertTriangle } from "lucide-react";

export function RiskMonitoring() {
  const location = useLocation();
  const highlightUserId = location.state?.highlightUserId as string | undefined;

  const { data: users, loading: loadingUsers, error: errorUsers } = useUsers();
  const { data: scores, loading: loadingScores, error: errorScores } = useScores();

  // Search and sorting states
  const [searchTerm, setSearchTerm] = useState("");
  const [sortAsc, setSortAsc] = useState<boolean | null>(true); // true = asc, false = desc, null = default

  // Expandable row state
  const [expandedUserId, setExpandedUserId] = useState<string | null>(null);
  const [userHistories, setUserHistories] = useState<Record<string, UserHistory>>({});
  const [loadingHistoryId, setLoadingHistoryId] = useState<string | null>(null);

  // Auto-expand highlighted user if navigated from Overview
  useEffect(() => {
    if (highlightUserId) {
      setExpandedUserId(highlightUserId);
      loadHistory(highlightUserId);
    }
  }, [highlightUserId]);

  const loadHistory = async (userId: string) => {
    if (userHistories[userId]) return; // Already cached

    setLoadingHistoryId(userId);
    try {
      const history = await getUserHistory(userId);
      setUserHistories((prev) => ({ ...prev, [userId]: history }));
    } catch (err) {
      console.error(`Failed to fetch history for user ${userId}:`, err);
      // Inject mock history on error
      const mockHist = generateMockUserHistory(userId);
      setUserHistories((prev) => ({ ...prev, [userId]: mockHist }));
    } finally {
      setLoadingHistoryId(null);
    }
  };

  const toggleExpand = (userId: string) => {
    if (expandedUserId === userId) {
      setExpandedUserId(null);
    } else {
      setExpandedUserId(userId);
      loadHistory(userId);
    }
  };

  const isDemoMode = (errorUsers || errorScores || (users && users.length === 0) || (scores && scores.length === 0)) && !loadingUsers && !loadingScores;

  const activeUsers = isDemoMode ? MOCK_USERS : users || [];
  const activeScores = isDemoMode ? MOCK_SCORES : scores || [];

  // Map users with their scores and trends
  const joinedData = activeUsers.map((user) => {
    // Find all scores of this user (sorted descending by computed_at)
    const userScores = activeScores.filter((s) => s.user_id === user.id);
    const latestScore = userScores[0];
    const previousScore = userScores[1];

    let trend = "stable";
    if (latestScore && previousScore) {
      if (latestScore.trust_score > previousScore.trust_score) trend = "up";
      else if (latestScore.trust_score < previousScore.trust_score) trend = "down";
    }

    const currentScoreVal = latestScore ? latestScore.trust_score : (user.current_trust_score ?? null);
    const riskClass = currentScoreVal === null 
      ? "Low" 
      : currentScoreVal < 40 
      ? "High" 
      : currentScoreVal < 70 
      ? "Medium" 
      : "Low";

    return {
      user,
      currentScoreVal,
      riskClass,
      trend,
      latestScoreId: latestScore?.id || null,
      lastCalculated: latestScore ? new Date(latestScore.computed_at).toLocaleString() : "Never",
    };
  });

  // Client-side filtering by username
  const filteredData = joinedData.filter((item) =>
    item.user.username.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Sorting logic based on Trust Score
  const sortedData = [...filteredData].sort((a, b) => {
    if (sortAsc === null) return 0;
    const scoreA = a.currentScoreVal ?? 100;
    const scoreB = b.currentScoreVal ?? 100;
    return sortAsc ? scoreA - scoreB : scoreB - scoreA;
  });

  if (loadingUsers || loadingScores) {
    if (!isDemoMode) {
      return (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-white">Loading Risk Profiles...</h2>
          <LoadingSkeleton rows={10} />
        </div>
      );
    }
  }

  return (
    <div className="space-y-6">
      {isDemoMode && (
        <div className="bg-yellow-950/40 border border-yellow-800 text-yellow-300 rounded-lg p-4 flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0 text-brand-yellow" />
          <span className="text-sm font-medium">
            ⚠ Demo Mode — showing simulated user behaviors and risk metrics.
          </span>
        </div>
      )}

      <div>
        <h1 className="text-3xl font-extrabold text-white">Risk Monitoring Center</h1>
        <p className="text-sm text-gray-400 mt-1">
          Perform audits, view score trends, and inspect specific developer behavioral deviations.
        </p>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3 top-3 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search by username..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-brand-green"
          />
        </div>

        <div className="text-xs text-gray-400">
          Showing {sortedData.length} profile(s)
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl shadow-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm border-collapse">
            <thead>
              <tr className="border-b border-gray-700 text-gray-400 font-medium bg-gray-800/50">
                <th className="py-3 px-6">Username</th>
                <th className="py-3 px-4">Department</th>
                <th className="py-3 px-4">Role</th>
                <th
                  className="py-3 px-4 cursor-pointer hover:text-white select-none transition-colors"
                  onClick={() => setSortAsc((prev) => (prev === null ? true : prev ? false : null))}
                >
                  <div className="flex items-center gap-1">
                    Trust Score
                    {sortAsc === true && <ArrowUp className="w-3 h-3 text-brand-green" />}
                    {sortAsc === false && <ArrowDown className="w-3 h-3 text-brand-red" />}
                  </div>
                </th>
                <th className="py-3 px-4">Risk Level</th>
                <th className="py-3 px-4">Last Calculated</th>
                <th className="py-3 px-4">Trend</th>
                <th className="py-3 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700 text-gray-300">
              {sortedData.map(({ user, currentScoreVal, riskClass, trend, lastCalculated }) => {
                const isExpanded = expandedUserId === user.id;
                const historyData = userHistories[user.id];
                const isHistoryLoading = loadingHistoryId === user.id;

                return (
                  <React.Fragment key={user.id}>
                    {/* Primary Row */}
                    <tr
                      className={`hover:bg-gray-750/30 transition-all duration-150 ${
                        isExpanded ? "bg-gray-750/20" : ""
                      } ${highlightUserId === user.id ? "border-l-4 border-brand-yellow" : ""}`}
                    >
                      <td className="py-4 px-6 font-bold text-white">{user.username}</td>
                      <td className="py-4 px-4">{user.department}</td>
                      <td className="py-4 px-4 capitalize text-gray-400 text-xs font-semibold">
                        {user.role}
                      </td>
                      <td className="py-4 px-4">
                        <TrustScoreBadge score={currentScoreVal} size="sm" />
                      </td>
                      <td className="py-4 px-4">
                        <RiskBadge riskClass={riskClass} />
                      </td>
                      <td className="py-4 px-4 text-xs text-gray-500">{lastCalculated}</td>
                      <td className="py-4 px-4">
                        {trend === "up" && (
                          <span className="flex items-center gap-1 text-xs text-brand-green font-bold">
                            <ArrowUp className="w-3.5 h-3.5" />
                            Up
                          </span>
                        )}
                        {trend === "down" && (
                          <span className="flex items-center gap-1 text-xs text-brand-red font-bold">
                            <ArrowDown className="w-3.5 h-3.5" />
                            Down
                          </span>
                        )}
                        {trend === "stable" && (
                          <span className="flex items-center gap-1 text-xs text-gray-500 font-bold">
                            <ArrowRight className="w-3.5 h-3.5" />
                            Stable
                          </span>
                        )}
                      </td>
                      <td className="py-4 px-6 text-right">
                        <button
                          onClick={() => toggleExpand(user.id)}
                          className="inline-flex items-center gap-1.5 text-xs font-bold text-gray-300 hover:text-white bg-gray-700 hover:bg-gray-600 rounded-md px-3.5 py-2 border border-gray-600 transition-all"
                        >
                          {isExpanded ? (
                            <>
                              Collapse <ChevronUp className="w-3.5 h-3.5" />
                            </>
                          ) : (
                            <>
                              Audit History <ChevronDown className="w-3.5 h-3.5" />
                            </>
                          )}
                        </button>
                      </td>
                    </tr>

                    {/* Expandable History Detail Row */}
                    {isExpanded && (
                      <tr>
                        <td colSpan={8} className="bg-gray-900/60 p-6 border-b border-gray-700">
                          {isHistoryLoading ? (
                            <div className="space-y-4">
                              <h4 className="text-sm font-bold text-gray-400">Loading audit history...</h4>
                              <LoadingSkeleton rows={4} />
                            </div>
                          ) : historyData ? (
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                              {/* Left Panel: Line Chart of Trust History */}
                              <div className="lg:col-span-1 bg-gray-800 p-4 border border-gray-700 rounded-lg">
                                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">
                                  Trust Score Timeline (Last 20 Runs)
                                </h4>
                                <div className="h-[150px] w-full">
                                  <ResponsiveContainer width="100%" height="100%">
                                    <LineChart
                                      data={[...historyData.trust_scores].reverse()}
                                      margin={{ top: 5, right: 10, left: -25, bottom: 5 }}
                                    >
                                      <XAxis dataKey="computed_at" hide />
                                      <YAxis domain={[0, 100]} stroke="#4B5563" fontSize={9} />
                                      <Tooltip
                                        contentStyle={{
                                          backgroundColor: "#1F2937",
                                          borderColor: "#374151",
                                        }}
                                        formatter={(val: any) => [`${Number(val).toFixed(1)}`, "Trust Score"]}
                                      />
                                      <Line
                                        type="monotone"
                                        dataKey="trust_score"
                                        stroke="#10B981"
                                        strokeWidth={2}
                                        dot={false}
                                      />
                                    </LineChart>
                                  </ResponsiveContainer>
                                </div>
                              </div>

                              {/* Right Panel: Recent Access Events Table */}
                              <div className="lg:col-span-2 bg-gray-800 p-4 border border-gray-700 rounded-lg">
                                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">
                                  Recent Access Telemetry logs
                                </h4>
                                <div className="overflow-x-auto">
                                  <table className="w-full text-left text-xs border-collapse">
                                    <thead>
                                      <tr className="border-b border-gray-700 text-gray-500 font-medium">
                                        <th className="py-2 px-3">Time</th>
                                        <th className="py-2 px-3">Event</th>
                                        <th className="py-2 px-3">Asset</th>
                                        <th className="py-2 px-3">IP Address</th>
                                        <th className="py-2 px-3">Location</th>
                                      </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-700 text-gray-300">
                                      {historyData.recent_events.slice(0, 5).map((log) => (
                                        <tr key={log.id} className="hover:bg-gray-750/20">
                                          <td className="py-2 px-3">
                                            {new Date(log.event_time).toLocaleTimeString()}
                                          </td>
                                          <td className="py-2 px-3 font-semibold uppercase text-[10px] text-gray-400">
                                            {log.event_type}
                                          </td>
                                          <td className="py-2 px-3 font-mono text-[10px] truncate max-w-[120px]" title={log.resource || ""}>
                                            {log.resource || "—"}
                                          </td>
                                          <td className="py-2 px-3 font-mono">{log.ip_address || "—"}</td>
                                          <td className="py-2 px-3 truncate max-w-[100px]" title={log.location || ""}>
                                            {log.location || "—"}
                                          </td>
                                        </tr>
                                      ))}
                                      {historyData.recent_events.length === 0 && (
                                        <tr>
                                          <td colSpan={5} className="py-4 text-center text-gray-500">
                                            No access logs logged for this user.
                                          </td>
                                        </tr>
                                      )}
                                    </tbody>
                                  </table>
                                </div>
                              </div>
                            </div>
                          ) : (
                            <div className="text-center text-red-400 text-sm">
                              Failed to load history data for this user.
                            </div>
                          )}
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
              {sortedData.length === 0 && (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-gray-500">
                    No matching user risk records located.
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

// Helper to generate mock user history dynamically if API fails
function generateMockUserHistory(userId: string): UserHistory {
  const user = MOCK_USERS.find((u) => u.id === userId) || MOCK_USERS[0];
  const baseline = user.current_trust_score || 80.0;

  // Synthesize 10 history points
  const trust_scores: TrustScore[] = Array.from({ length: 10 }).map((_, i) => ({
    id: `ms-${userId}-${i}`,
    user_id: userId,
    trust_score: Math.max(0, Math.min(100, baseline + (i === 0 ? 0 : randomSign() * randomOffset(5)))),
    anomaly_component: 0.1,
    risk_component: 0.1,
    computed_at: new Date(Date.now() - i * 3600000).toISOString(),
  }));

  const recent_events: AccessLog[] = [
    {
      id: `l-${userId}-1`,
      user_id: userId,
      device_id: "d-mock",
      event_type: "repo_access",
      resource: "payments-core",
      bytes_transferred: 0,
      event_time: new Date(Date.now() - 600000).toISOString(),
      ip_address: "10.0.0.12",
      location: "Bengaluru, IN",
    },
    {
      id: `l-${userId}-2`,
      user_id: userId,
      device_id: "d-mock",
      event_type: "file_download",
      resource: "payments-core/src/index.js",
      bytes_transferred: 10450,
      event_time: new Date(Date.now() - 1200000).toISOString(),
      ip_address: "10.0.0.12",
      location: "Bengaluru, IN",
    },
  ];

  return { user, trust_scores, recent_events };
}

const randomSign = () => (Math.random() > 0.5 ? 1 : -1);
const randomOffset = (max: number) => Math.floor(Math.random() * max);

// Mock datasets for Overview & Table view fallbacks
const MOCK_USERS: User[] = [
  { id: "u1", username: "alice.dev", email: "alice@zt-enterprise.io", role: "employee", department: "Engineering", created_at: "2026-07-09T08:00:00Z", current_trust_score: 95.0 },
  { id: "u2", username: "bob.dev", email: "bob@zt-enterprise.io", role: "employee", department: "Engineering", created_at: "2026-07-09T08:05:00Z", current_trust_score: 82.3 },
  { id: "u3", username: "charlie.ops", email: "charlie@zt-enterprise.io", role: "employee", department: "DevOps", created_at: "2026-07-09T08:10:00Z", current_trust_score: 74.1 },
  { id: "u4", username: "diana.sec", email: "diana@zt-enterprise.io", role: "analyst", department: "Security", created_at: "2026-07-09T08:15:00Z", current_trust_score: 88.0 },
  { id: "u5", username: "eve.insider", email: "eve@zt-enterprise.io", role: "employee", department: "Engineering", created_at: "2026-07-09T08:20:00Z", current_trust_score: 18.2 },
];

const MOCK_SCORES: TrustScore[] = [
  { id: "s1", user_id: "u5", trust_score: 18.2, anomaly_component: 0.38, risk_component: 0.4, computed_at: "2026-07-09T08:29:00Z" },
  { id: "s2", user_id: "u3", trust_score: 74.1, anomaly_component: 0.1, risk_component: 0.1, computed_at: "2026-07-09T08:12:00Z" },
  { id: "s3", user_id: "u2", trust_score: 82.3, anomaly_component: 0.08, risk_component: 0.09, computed_at: "2026-07-09T08:15:00Z" },
  { id: "s4", user_id: "u4", trust_score: 88.0, anomaly_component: 0.05, risk_component: 0.07, computed_at: "2026-07-09T08:25:00Z" },
  { id: "s5", user_id: "u1", trust_score: 95.0, anomaly_component: 0.02, risk_component: 0.03, computed_at: "2026-07-09T08:30:00Z" },
];
export default RiskMonitoring;
