import { BrowserRouter, Routes, Route, Link } from "react-router-dom";

import Overview from "./pages/Overview";
import RiskMonitoring from "./pages/RiskMonitoring";
import TrustScore from "./pages/TrustScore";
import AlertManagement from "./pages/AlertManagement";

function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen">
        <aside className="w-64 bg-gray-800 text-white p-4">
          <h2 className="text-xl font-bold mb-6"> Dashboard</h2>

          <nav className="flex flex-col gap-4">
            <Link to="/">Overview</Link>
            <Link to="/risk-monitoring">Risk Monitoring</Link>
            <Link to="/trust-score">Trust Score</Link>
            <Link to="/alerts">Alert Management</Link>
          </nav>
        </aside>

        <main className="flex-1 p-6">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/risk-monitoring" element={<RiskMonitoring />} />
            <Route path="/trust-score" element={<TrustScore />} />
            <Route path="/alerts" element={<AlertManagement />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;