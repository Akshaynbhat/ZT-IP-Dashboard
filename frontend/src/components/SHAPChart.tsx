import React from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { SHAPFeature } from "../types";

interface SHAPChartProps {
  features: SHAPFeature[];
}

function cleanFeatureName(name: string): string {
  if (!name) return "";
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function SHAPChart({ features }: SHAPChartProps) {
  // Parse features and transform to absolute values for bar lengths
  const chartData = features.map((f) => {
    const isIncrease =
      f.direction.toLowerCase().includes("increase") || f.shap_value >= 0;
    return {
      name: cleanFeatureName(f.feature),
      abs_value: Math.abs(f.shap_value),
      raw_value: f.shap_value,
      color: isIncrease ? "#EF4444" : "#3B82F6", // red for increase, blue for decrease
      direction: isIncrease ? "Increase Risk" : "Decrease Risk",
    };
  });

  if (!features || features.length === 0) {
    return (
      <div className="h-[200px] flex items-center justify-center bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-500">
        No feature contributions available for this score.
      </div>
    );
  }

  return (
    <div className="bg-gray-800 p-2 border border-gray-700 rounded-lg">
      <h4 className="text-xs font-semibold text-gray-400 mb-2 tracking-wider uppercase">
        Risk Factor Contributions (SHAP Values)
      </h4>
      <div className="h-[180px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 5, right: 10, left: 10, bottom: 5 }}
          >
            <XAxis type="number" stroke="#6B7280" fontSize={10} tickLine={false} />
            <YAxis
              dataKey="name"
              type="category"
              stroke="#9CA3AF"
              fontSize={9}
              tickLine={false}
              width={110}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1F2937",
                borderColor: "#374151",
                borderRadius: "6px",
              }}
              labelStyle={{ color: "#9CA3AF", fontWeight: "bold" }}
              formatter={(value: any, name: any, props: any) => [
                `${props.payload.raw_value >= 0 ? "+" : ""}${props.payload.raw_value.toFixed(4)} (${props.payload.direction})`,
                "Weight",
              ]}
            />
            <Bar dataKey="abs_value" barSize={12} radius={[0, 3, 3, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
export default SHAPChart;
