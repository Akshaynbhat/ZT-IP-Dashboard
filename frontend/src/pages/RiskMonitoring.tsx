export default function RiskMonitoring() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">
        Risk Monitoring
      </h1>

      <div className="bg-white shadow rounded-lg p-4">
        <table className="w-full">
          <thead>
            <tr className="border-b">
              <th className="text-left p-2">User</th>
              <th className="text-left p-2">Risk Score</th>
              <th className="text-left p-2">Status</th>
              <th className="text-left p-2">Last Activity</th>
            </tr>
          </thead>

          <tbody>
            <tr className="border-b">
              <td className="p-2">User001</td>
              <td className="p-2">92</td>
              <td className="p-2">High Risk</td>
              <td className="p-2">10 mins ago</td>
            </tr>

            <tr className="border-b">
              <td className="p-2">User002</td>
              <td className="p-2">78</td>
              <td className="p-2">Medium Risk</td>
              <td className="p-2">30 mins ago</td>
            </tr>

            <tr>
              <td className="p-2">User003</td>
              <td className="p-2">45</td>
              <td className="p-2">Low Risk</td>
              <td className="p-2">1 hour ago</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}