import type { Config } from "tailwindcss";
import forms from "@tailwindcss/forms";

const config: Config = {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Security-specific status hex colors matching branding rules
        brand: {
          red: "#EF4444",
          yellow: "#F59E0B",
          green: "#10B981",
        },
        severity: {
          critical: "#7C3AED",
          high: "#EF4444",
          medium: "#F59E0B",
          low: "#3B82F6",
        },
      },
    },
  },
  plugins: [forms],
};

export default config;
