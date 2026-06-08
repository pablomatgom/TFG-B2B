"use client";

import { usePathname } from "next/navigation";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

const NO_SIDEBAR_ROUTES = ["/login"];

export default function SidebarLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const showSidebar = !NO_SIDEBAR_ROUTES.includes(pathname);

  return (
    <div className="flex min-h-screen">
      {showSidebar && <Sidebar />}
      {showSidebar && <TopBar />}
      <div className={`flex-1 min-h-screen min-w-0 overflow-x-hidden ${showSidebar ? "ml-60 pt-14" : ""}`}>
        {children}
      </div>
    </div>
  );
}