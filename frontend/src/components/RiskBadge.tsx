import React from "react";

interface RiskBadgeProps {
  riskClass: string;
}

export function RiskBadge({ riskClass }: RiskBadgeProps) {
  const riskLower = riskClass.toLowerCase();

  // Pick colors from design guidelines
  let color = "#10B981"; // default low: green
  if (riskLower === "high") {
    color = "#EF4444"; // red
  } else if (riskLower === "medium") {
    color = "#F59E0B"; // yellow
  }

  return (
    <span
      className="inline-block rounded-full px-2.5 py-0.5 text-xs font-bold uppercase tracking-wider border"
      style={{
        color: color,
        borderColor: color,
        backgroundColor: `${color}1A`, // 10% opacity in Hex
      }}
    >
      {riskClass}
    </span>
  );
}
