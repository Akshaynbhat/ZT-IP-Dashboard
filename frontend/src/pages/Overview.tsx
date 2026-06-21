export default function Overview() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Overview Dashboard</h1>

      <div className="grid grid-cols-4 gap-4">
        <div className="p-4 border rounded-lg">
          <h2>Total Users</h2>
          <p className="text-2xl font-bold">250</p>
        </div>

        <div className="p-4 border rounded-lg">
          <h2>High Risk Users</h2>
          <p className="text-2xl font-bold">12</p>
        </div>

        <div className="p-4 border rounded-lg">
          <h2>Active Alerts</h2>
          <p className="text-2xl font-bold">18</p>
        </div>

        <div className="p-4 border rounded-lg">
          <h2>Average Trust Score</h2>
          <p className="text-2xl font-bold">82</p>
        </div>
      </div>
    </div>
  );
}