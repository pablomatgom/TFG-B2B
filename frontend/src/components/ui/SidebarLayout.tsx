"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

const NO_SIDEBAR_ROUTES = ["/login"];

export default function SidebarLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const showSidebar = !NO_SIDEBAR_ROUTES.includes(pathname);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex min-h-screen">
      {showSidebar && (
        <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      )}
      {showSidebar && (
        <TopBar onMenuClick={() => setSidebarOpen((o) => !o)} />
      )}
      {/* Mobile backdrop */}
      {showSidebar && sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <div className={`flex-1 min-h-screen min-w-0 overflow-x-hidden ${showSidebar ? "lg:ml-60 pt-14" : ""}`}>
        {children}
      </div>
    </div>
  );
}