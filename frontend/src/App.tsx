import React, { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { initKeycloak, hasRole } from "./auth/keycloak";
import { Layout } from "./components/Layout";
import { Overview } from "./pages/Overview";
import { RiskMonitoring } from "./pages/RiskMonitoring";
import { TrustScoreViz } from "./pages/TrustScoreViz";
import { AlertDashboard } from "./pages/AlertDashboard";
import { ShieldAlert } from "lucide-react";

// Security role router guard to enforce Zero Trust route isolation
function RoleGuard({ children }: { children: React.ReactNode }) {
  const isSecurityStaff = hasRole("admin") || hasRole("analyst");
  
  if (!isSecurityStaff) {
    // Silently redirect standard employees back to Overview landing page
    return <Navigate to="/" state={{ restricted: true }} replace />;
  }
  return <>{children}</>;
}

export function App() {
  const [initializing, setInitializing] = useState(true);
  const [authError, setAuthError] = useState(false);

  useEffect(() => {
    // Boot OIDC authentication flow
    initKeycloak()
      .then((authenticated) => {
        if (authenticated) {
          setAuthError(false);
        } else {
          console.error("Keycloak returned authenticated = false status.");
          setAuthError(true);
        }
      })
      .catch((err) => {
        console.error("OIDC session initialization crash:", err);
        setAuthError(true);
      })
      .finally(() => {
        setInitializing(false);
      });
  }, []);

  // Show premium credential verification loader
  if (initializing) {
    return (
      <div className="min-h-screen w-screen bg-gray-950 flex flex-col items-center justify-center space-y-4 font-sans select-none">
        <div className="relative flex items-center justify-center">
          {/* Animated pulse rings */}
          <div className="absolute w-16 h-16 rounded-full border border-brand-green/30 animate-ping" />
          <div className="w-12 h-12 border-4 border-brand-green border-t-transparent rounded-full animate-spin" />
        </div>
        <div className="text-center space-y-1">
          <span className="text-sm font-bold text-white tracking-wide block">
            Zero Trust IAM Auth Gate
          </span>
          <span className="text-[11px] text-gray-500 font-semibold block">
            Verifying OIDC session credentials...
          </span>
        </div>
      </div>
    );
  }

  // Auth gate initialization error screen
  if (authError) {
    return (
      <div className="min-h-screen w-screen bg-gray-950 flex flex-col items-center justify-center space-y-4 font-sans p-6 text-center select-none">
        <ShieldAlert className="w-16 h-16 text-brand-red animate-pulse" />
        <h1 className="text-xl font-black text-white">Identity Verification Failed</h1>
        <p className="text-sm text-gray-400 max-w-sm">
          Could not establish connection to the Keycloak directory server. Please refresh your browser or check your deployment.
        </p>
        <button
          onClick={() => window.location.reload()}
          className="bg-brand-red hover:bg-red-650 text-white font-bold text-xs px-5 py-2.5 rounded-lg shadow-lg transition-all"
        >
          Retry Authentication
        </button>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        {/* Main application layouts */}
        <Route path="/" element={<Layout />}>
          {/* Publicly mapped dashboard overview (renders self-view for employee, admin view for staff) */}
          <Route index element={<Overview />} />
          
          {/* Secured routes only for security operations team */}
          <Route
            path="risk"
            element={
              <RoleGuard>
                <RiskMonitoring />
              </RoleGuard>
            }
          />
          <Route
            path="trust"
            element={
              <RoleGuard>
                <TrustScoreViz />
              </RoleGuard>
            }
          />
          <Route
            path="alerts"
            element={
              <RoleGuard>
                <AlertDashboard />
              </RoleGuard>
            }
          />
        </Route>
        
        {/* Fallback route wildcard redirection */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
export default App;
