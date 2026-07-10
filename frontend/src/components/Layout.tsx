import { Outlet } from "react-router-dom";
import { Navbar } from "./Navbar";

export function Layout() {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-gray-950 text-gray-100 font-sans">
      {/* Fixed Left Navigation Sidebar */}
      <Navbar />

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto bg-gray-950 p-8">
        <div className="max-w-7xl mx-auto space-y-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
export default Layout;
