import React from "react";

interface SeverityBadgeProps {
  severity: string;
}

export function SeverityBadge({ severity }: SeverityBadgeProps) {
  const sevLower = severity.toLowerCase();

  // Pick colors from design guidelines
  let color = "#3B82F6"; // default low: blue
  if (sevLower === "critical") {
    color = "#7C3AED"; // purple
  } else if (sevLower === "high") {
    color = "#EF4444"; // red
  } else if (sevLower === "medium") {
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
      {severity}
    </span>
  );
}
