export default function TrustScore() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">
        Trust Score Visualization
      </h1>

      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">
          Organization Trust Score
        </h2>

        <div className="w-full bg-gray-200 rounded-full h-6">
          <div
            className="bg-green-500 h-6 rounded-full"
            style={{ width: "82%" }}
          ></div>
        </div>

        <p className="mt-3 text-lg font-bold">
          Current Trust Score: 82%
        </p>
      </div>

      <div className="mt-6 bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">
          Department Scores
        </h2>

        <ul className="space-y-3">
          <li>IT Department - 88%</li>
          <li>Finance Department - 75%</li>
          <li>HR Department - 81%</li>
          <li>Operations Department - 79%</li>
        </ul>
      </div>
    </div>
  );
}