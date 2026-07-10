import { NavLink } from "react-router-dom";
import {
  getUsername,
  hasRole,
  logout,
} from "../auth/keycloak";
import {
  LayoutDashboard,
  ShieldAlert,
  Activity,
  LineChart,
  LogOut,
  User as UserIcon,
} from "lucide-react";

export function Navbar() {
  const username = getUsername();

  // Determine user's highest role for badge display
  let primaryRole = "employee";
  let badgeColor = "bg-gray-700 text-gray-300 border-gray-600";

  if (hasRole("admin")) {
    primaryRole = "admin";
    badgeColor = "bg-purple-900/40 text-purple-300 border-purple-800";
  } else if (hasRole("analyst")) {
    primaryRole = "analyst";
    badgeColor = "bg-blue-900/40 text-blue-300 border-blue-800";
  }

  const isSecStaff = hasRole("admin") || hasRole("analyst");

  return (
    <nav className="w-64 bg-gray-900 border-r border-gray-800 h-screen flex flex-col justify-between p-6 shrink-0">
      <div className="space-y-8">
        {/* Brand Header Logo */}
        <div className="flex items-center gap-3">
          <ShieldAlert className="w-8 h-8 text-brand-red animate-pulse" />
          <span className="font-extrabold text-xl tracking-tight text-white">
            ZT Dashboard
          </span>
        </div>

        {/* Navigation Link Stack */}
        <div className="space-y-1">
          <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider block mb-2 px-3">
            Menu
          </span>

          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                isActive
                  ? "bg-gray-800 text-white border-l-4 border-brand-green"
                  : "text-gray-400 hover:text-white hover:bg-gray-800/50"
              }`
            }
          >
            <LayoutDashboard className="w-4 h-4" />
            Overview
          </NavLink>

          {isSecStaff && (
            <>
              <NavLink
                to="/risk"
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? "bg-gray-800 text-white border-l-4 border-brand-green"
                      : "text-gray-400 hover:text-white hover:bg-gray-800/50"
                  }`
                }
              >
                <Activity className="w-4 h-4" />
                Risk Monitor
              </NavLink>

              <NavLink
                to="/trust"
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? "bg-gray-800 text-white border-l-4 border-brand-green"
                      : "text-gray-400 hover:text-white hover:bg-gray-800/50"
                  }`
                }
              >
                <LineChart className="w-4 h-4" />
                Trust Scores
              </NavLink>

              <NavLink
                to="/alerts"
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? "bg-gray-800 text-white border-l-4 border-brand-green"
                      : "text-gray-400 hover:text-white hover:bg-gray-800/50"
                  }`
                }
              >
                <ShieldAlert className="w-4 h-4" />
                Alerts
              </NavLink>
            </>
          )}
        </div>
      </div>

      {/* User Session Info Box at Bottom */}
      <div className="border-t border-gray-800 pt-4 space-y-4">
        <div className="flex items-center gap-3 px-1">
          <div className="w-9 h-9 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center text-gray-300">
            <UserIcon className="w-4 h-4" />
          </div>
          <div className="overflow-hidden">
            <h4 className="text-sm font-semibold text-white truncate">
              {username}
            </h4>
            <span
              className={`inline-block text-[9px] font-extrabold uppercase border rounded-md px-1.5 py-0.5 mt-1 tracking-wider ${badgeColor}`}
            >
              {primaryRole}
            </span>
          </div>
        </div>

        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-400 hover:text-red-400 hover:bg-red-950/20 border border-transparent hover:border-red-900/30 transition-all duration-150"
        >
          <LogOut className="w-4 h-4" />
          Sign Out
        </button>
      </div>
    </nav>
  );
}
export default Navbar;
