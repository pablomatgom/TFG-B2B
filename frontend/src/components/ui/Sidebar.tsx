"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import {
  ChartBarIcon,
  ShieldExclamationIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  CurrencyEuroIcon,
  DocumentTextIcon,
  LinkIcon,
  CpuChipIcon,
  SparklesIcon,
  AdjustmentsHorizontalIcon,
  BookOpenIcon,
  ArrowRightStartOnRectangleIcon,
} from "@heroicons/react/24/outline";
import { useAuth } from "@/contexts/AuthContext";
import { useDbStatus } from "@/hooks/useDbStatus";
import { BRAND } from "@/lib/brand";

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  tab?: number;
  adminOnly?: boolean;
}

const MAIN_ITEMS: NavItem[] = [
  { name: "Visión Global", href: "/", icon: ChartBarIcon },
];

const ANALYTICS_ITEMS: NavItem[] = [
  { name: "Contratos",     href: "/analytics?tab=0", icon: DocumentTextIcon,       tab: 0 },
  { name: "Riesgo",        href: "/analytics?tab=1", icon: ShieldExclamationIcon,  tab: 1 },
  { name: "Discrepancias", href: "/analytics?tab=2", icon: ExclamationTriangleIcon, tab: 2 },
  { name: "Lead Time",     href: "/analytics?tab=3", icon: ClockIcon,              tab: 3 },
  { name: "Exposición",    href: "/analytics?tab=4", icon: CurrencyEuroIcon,       tab: 4 },
  { name: "Trazabilidad",  href: "/analytics?tab=5", icon: LinkIcon,               tab: 5 },
  { name: "GDS",           href: "/analytics?tab=6", icon: CpuChipIcon,            tab: 6 },
];

const SYSTEM_ITEMS: NavItem[] = [
  { name: "Pipeline", href: "/pipeline", icon: AdjustmentsHorizontalIcon, adminOnly: true },
];

/* ── Single nav link ──────────────────────────────────── */
function NavLink({ item, isActive }: { item: NavItem; isActive: boolean }) {
  return (
    <Link
      href={item.href}
      className={`
        flex items-center gap-2.5 px-3 py-[7px] rounded-md text-sm transition-colors duration-150 border
        ${isActive
          ? "bg-indigo-600 text-white border-indigo-500"
          : "text-gray-400 hover:text-white hover:bg-gray-800 border-transparent"
        }
      `}
    >
      <item.icon className="w-4 h-4 shrink-0" />
      <span className="font-medium">{item.name}</span>
      {isActive && (
        <span className="ml-auto w-1 h-1 rounded-full bg-indigo-300 shrink-0" />
      )}
    </Link>
  );
}

/* ── Section label ────────────────────────────────────── */
function SectionLabel({ children }: { children: string }) {
  return (
    <p className="px-3 mb-1.5 text-[10px] font-bold tracking-[0.10em] uppercase text-gray-500 select-none">
      {children}
    </p>
  );
}

/* ── Nav content (uses useSearchParams — needs Suspense) ── */
function NavContent() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { user, logout } = useAuth();

  const currentTab = searchParams.get("tab");

  function isActive(item: NavItem): boolean {
    if (item.tab !== undefined) {
      const tabStr = currentTab ?? "0";
      return pathname === "/analytics" && tabStr === String(item.tab);
    }
    return pathname === item.href;
  }

  const visibleSystem = SYSTEM_ITEMS.filter(
    (i) => !i.adminOnly || user?.role === "admin"
  );

  return (
    <nav className="flex-1 overflow-y-auto py-3 px-3 space-y-5 min-h-0">
      {/* Main */}
      <div className="space-y-0.5">
        {MAIN_ITEMS.map((item) => (
          <NavLink key={item.href} item={item} isActive={isActive(item)} />
        ))}
      </div>

      {/* Analytics */}
      <div>
        <SectionLabel>Analytics</SectionLabel>
        <div className="space-y-0.5">
          {ANALYTICS_ITEMS.map((item) => (
            <NavLink key={item.href} item={item} isActive={isActive(item)} />
          ))}
        </div>
      </div>

      {/* System — admin only */}
      {visibleSystem.length > 0 && (
        <div>
          <SectionLabel>Sistema</SectionLabel>
          <div className="space-y-0.5">
            {visibleSystem.map((item) => (
              <NavLink key={item.href} item={item} isActive={isActive(item)} />
            ))}
          </div>
        </div>
      )}

      {/* Secondary links */}
      <div className="border-t border-gray-800 pt-3 space-y-0.5">
        <Link
          href="/docs"
          className={`flex items-center gap-2.5 px-3 py-[7px] rounded-md text-sm transition-colors duration-150 border ${
            pathname === "/docs"
              ? "bg-indigo-600 text-white border-indigo-500"
              : "text-gray-400 hover:text-white hover:bg-gray-800 border-transparent"
          }`}
        >
          <BookOpenIcon className="w-4 h-4 shrink-0" />
          <span className="font-medium">Documentación</span>
          {pathname === "/docs" && (
            <span className="ml-auto w-1 h-1 rounded-full bg-indigo-300 shrink-0" />
          )}
        </Link>
      </div>

      {/* User section */}
      {user && (
        <div className="border-t border-gray-800 pt-3">
          <div className="px-3 mb-2.5">
            <p className="text-xs font-medium text-gray-200 truncate leading-none">{user.full_name}</p>
            <p className="text-[10px] text-gray-500 truncate mt-0.5">{user.email}</p>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center gap-2.5 px-3 py-[7px] rounded-md text-sm text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors duration-150 border border-transparent"
          >
            <ArrowRightStartOnRectangleIcon className="w-4 h-4 shrink-0" />
            <span className="font-medium">Cerrar sesión</span>
          </button>
        </div>
      )}
    </nav>
  );
}

/* ── Nav skeleton while Suspense loads ────────────────── */
function NavSkeleton() {
  return (
    <div className="flex-1 px-3 py-3 space-y-1.5">
      {Array.from({ length: 10 }).map((_, i) => (
        <div key={i} className="h-8 rounded bg-gray-800 shimmer" />
      ))}
    </div>
  );
}

/* ── Main sidebar component ───────────────────────────── */
export default function Sidebar({ open, onClose }: { open?: boolean; onClose?: () => void }) {
  const dbStatus = useDbStatus();

  const dotColor =
    dbStatus === "connected"    ? "#34D399" :
    dbStatus === "disconnected" ? "#EF4444" :
    "#9ca3af";

  const statusLabel =
    dbStatus === "connected"    ? "Online" :
    dbStatus === "disconnected" ? "Offline" :
    "Checking";

  return (
    <aside className={`fixed left-0 top-0 h-screen w-60 flex flex-col bg-gray-900 border-r border-gray-800 z-40 transition-transform duration-300 ease-in-out lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}>

      {/* ── Logo + status ──────────────────────────────── */}
      <div className="px-4 pt-4 pb-3 border-b border-gray-800 shrink-0">
        {/* Wordmark */}
        <Link href="/" className="flex items-center gap-2.5 mb-3 group">
          <div className="w-7 h-7 rounded-lg bg-indigo-600 border border-indigo-500 flex items-center justify-center shrink-0">
            <svg viewBox="0 0 16 16" fill="none" className="w-3.5 h-3.5" aria-hidden>
              <circle cx="8" cy="8" r="2.5" fill="white" />
              <line x1="8" y1="1" x2="8" y2="5" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
              <line x1="8" y1="11" x2="8" y2="15" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
              <line x1="1" y1="8" x2="5" y2="8" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
              <line x1="11" y1="8" x2="15" y2="8" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
              <line x1="3.1" y1="3.1" x2="5.9" y2="5.9" stroke="white" strokeWidth="1" strokeLinecap="round" opacity="0.6" />
              <line x1="10.1" y1="10.1" x2="12.9" y2="12.9" stroke="white" strokeWidth="1" strokeLinecap="round" opacity="0.6" />
              <line x1="12.9" y1="3.1" x2="10.1" y2="5.9" stroke="white" strokeWidth="1" strokeLinecap="round" opacity="0.6" />
              <line x1="5.9" y1="10.1" x2="3.1" y2="12.9" stroke="white" strokeWidth="1" strokeLinecap="round" opacity="0.6" />
            </svg>
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-white leading-none truncate">{BRAND.name}</p>
            <p className="text-[9px] font-bold tracking-[0.12em] uppercase text-gray-500 mt-0.5">
              {BRAND.subtitle}
            </p>
          </div>
        </Link>

        {/* DB status pill */}
        <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-md bg-gray-800 border border-gray-700">
          <span
            className={`w-1.5 h-1.5 rounded-full shrink-0 ${dbStatus === "connected" ? "animate-pulse" : ""}`}
            style={{ backgroundColor: dotColor }}
          />
          <span
            className="text-[10px] font-bold tracking-[0.08em] uppercase"
            style={{ color: dotColor }}
          >
            {statusLabel}
          </span>
          <span className="ml-auto text-[10px] text-gray-500 font-medium">Neo4j</span>
        </div>
      </div>

      {/* ── Nav (Suspense for useSearchParams) ─────────── */}
      <Suspense fallback={<NavSkeleton />}>
        <NavContent />
      </Suspense>
    </aside>
  );
}