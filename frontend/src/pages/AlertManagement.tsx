const alertsData = [
  {
    id: 1,
    user: "User A",
    type: "Suspicious Login",
    risk: "High",
    time: "2 min ago",
    status: "Blocked",
  },
  {
    id: 2,
    user: "User B",
    type: "Multiple Failed Attempts",
    risk: "Medium",
    time: "10 min ago",
    status: "Under Review",
  },
  {
    id: 3,
    user: "User C",
    type: "New Device Login",
    risk: "Low",
    time: "30 min ago",
    status: "Allowed",
  },
  {
    id: 4,
    user: "User D",
    type: "Unusual Location",
    risk: "High",
    time: "1 hr ago",
    status: "Blocked",
  },
];

const getRiskColor = (risk: string) => {
  switch (risk) {
    case "High":
      return "text-red-600 bg-red-100";
    case "Medium":
      return "text-yellow-600 bg-yellow-100";
    case "Low":
      return "text-green-600 bg-green-100";
    default:
      return "text-gray-600 bg-gray-100";
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case "Blocked":
      return "text-red-600 bg-red-100";
    case "Under Review":
      return "text-yellow-600 bg-yellow-100";
    case "Allowed":
      return "text-green-600 bg-green-100";
    default:
      return "text-gray-600 bg-gray-100";
  }
};

export default function AlertsTable() {
  return (
    <div className="bg-white shadow rounded-xl p-4 mt-6">
      <h2 className="text-xl font-semibold mb-4">Recent Alerts</h2>

      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead>
            <tr className="border-b text-gray-500">
              <th className="p-2">User</th>
              <th className="p-2">Alert Type</th>
              <th className="p-2">Risk</th>
              <th className="p-2">Time</th>
              <th className="p-2">Status</th>
            </tr>
          </thead>

          <tbody>
            {alertsData.map((alert) => (
              <tr key={alert.id} className="border-b hover:bg-gray-50">
                <td className="p-2 font-medium">{alert.user}</td>
                <td className="p-2">{alert.type}</td>

                <td className="p-2">
                  <span
                    className={`px-2 py-1 rounded-full text-xs ${getRiskColor(
                      alert.risk
                    )}`}
                  >
                    {alert.risk}
                  </span>
                </td>

                <td className="p-2 text-gray-500">{alert.time}</td>

                <td className="p-2">
                  <span
                    className={`px-2 py-1 rounded-full text-xs ${getStatusColor(
                      alert.status
                    )}`}
                  >
                    {alert.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}