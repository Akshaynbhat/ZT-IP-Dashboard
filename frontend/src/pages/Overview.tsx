import TrustScoreCard from "../components/TrustScoreCard";
import AlertsTable from "../components/AlertsTable";

export default function Overview() {
  return (
    <div className="p-6 bg-gray-50 min-h-screen space-y-6">

      {/* Title */}
      <h1 className="text-2xl font-bold">Overview Dashboard</h1>

      {/* Top Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <TrustScoreCard score={85} />
      </div>

      {/* Alerts */}
      <AlertsTable />

    </div>
  );
}