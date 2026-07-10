import React from "react";

interface TrustScoreBadgeProps {
  score: number | null;
  size?: "sm" | "md" | "lg";
}

export function TrustScoreBadge({ score, size = "md" }: TrustScoreBadgeProps) {
  // Determine size classes
  const sizeClasses = {
    sm: "w-10 h-10 text-xs",
    md: "w-14 h-14 text-sm",
    lg: "w-20 h-20 text-lg",
  }[size];

  // If the score has not been calculated yet
  if (score === null || score === undefined) {
    return (
      <div
        className={`${sizeClasses} flex items-center justify-center rounded-full font-bold border border-gray-600 bg-gray-800 text-gray-400`}
        title="Score not computed yet"
      >
        —
      </div>
    );
  }

  // Determine hex color based on ZT-IP parameters
  let color = "#10B981"; // green
  if (score < 40) {
    color = "#EF4444"; // red
  } else if (score < 70) {
    color = "#F59E0B"; // yellow
  }

  // Render badge with custom inline opacity styles to support hex specifications
  return (
    <div
      className={`${sizeClasses} flex items-center justify-center rounded-full font-bold border transition-colors duration-200`}
      style={{
        borderColor: color,
        color: color,
        backgroundColor: `${color}33`, // 20% Opacity in Hex: 0.2 * 255 = 51 = 0x33
      }}
    >
      {Math.round(score)}
    </div>
  );
}
