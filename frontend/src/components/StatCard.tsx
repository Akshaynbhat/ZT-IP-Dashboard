import React from "react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: string; // Optional custom text color for emphasis
}

export function StatCard({ title, value, subtitle, color }: StatCardProps) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-xl shadow-lg p-6 flex flex-col justify-between transition-all duration-200 hover:border-gray-600">
      <div>
        <span className="text-xs font-semibold tracking-wider text-gray-400 uppercase">
          {title}
        </span>
        <h3
          className="text-3xl font-extrabold mt-2 tracking-tight"
          style={{ color: color || "#FFFFFF" }}
        >
          {value}
        </h3>
      </div>
      {subtitle && (
        <span className="text-xs text-gray-400 mt-4 block font-medium">
          {subtitle}
        </span>
      )}
    </div>
  );
}
