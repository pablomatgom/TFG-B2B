"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  HomeIcon,
  AdjustmentsHorizontalIcon,
  ChartBarIcon,
  BeakerIcon,
  BuildingOfficeIcon,
  ArrowRightStartOnRectangleIcon,
  UserIcon,
} from "@heroicons/react/24/solid";
import DbStatusBadge from "@/components/ui/DbStatusBadge";
import { useAuth } from "@/contexts/AuthContext";
import { useDbStatus } from "@/hooks/useDbStatus";

/* ── nav link definitions ─────────────────────────────────── */
interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  authRequired?: boolean;
  hideWhenLogged?: boolean;
  adminOnly?: boolean;
}

const NAV_LINKS: NavItem[] = [
  { name: "Inicio",     href: "/",          icon: HomeIcon },
  { name: "Dashboard",  href: "/dashboard", icon: ChartBarIcon },
  { name: "Analytics",  href: "/analytics", icon: BeakerIcon },
  { name: "Pipeline",   href: "/pipeline",  icon: AdjustmentsHorizontalIcon, adminOnly: true },
  { name: "Login",      href: "/login",     icon: UserIcon, hideWhenLogged: true },
  { name: "Mi Empresa", href: "/company",   icon: BuildingOfficeIcon, authRequired: true },
];

/* ── sub-components ───────────────────────────────────────── */
function NavLink({ item, isActive }: { item: NavItem; isActive: boolean }) {
  return (
    <Link href={item.href}>
      <div
        className={`flex items-center space-x-1.5 px-2.5 md:px-3 py-2 rounded-lg transition-colors text-sm font-medium
          ${isActive
            ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
            : "text-slate-400 hover:text-white hover:bg-slate-800 border border-transparent"
          }`}
      >
        <item.icon className="w-4 h-4 flex-shrink-0" />
        <span className="hidden md:block">{item.name}</span>
      </div>
    </Link>
  );
}

/* ── main component ───────────────────────────────────────── */
export default function Navbar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const dbStatus = useDbStatus();

  // El filtro ahora comprueba los permisos de admin
  const visibleLinks = NAV_LINKS.filter((l) => 
    (!l.authRequired || user) && 
    (!l.hideWhenLogged || !user) &&
    (!l.adminOnly || (user && user.role === "admin"))
  );

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0E1117]/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 md:px-6 h-16 flex items-center justify-between gap-4">

        {/* LOGO */}
        <Link
          href="/"
          className="flex items-center space-x-2 hover:opacity-80 transition-opacity flex-shrink-0"
        >
          <BeakerIcon className="w-6 h-6 text-cyan-500" />
          <span className="font-bold text-white text-lg tracking-wide hidden sm:block">
            B2B Graph Intel
          </span>
        </Link>

        {/* NAV LINKS */}
        <div className="flex items-center space-x-1 md:space-x-2">
          {visibleLinks.map((link) => (
            <NavLink key={link.href} item={link} isActive={pathname === link.href} />
          ))}
        </div>

        {/* RIGHT SIDE: DB badge + user info */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <div className="hidden lg:block scale-[0.8] origin-center">
            <DbStatusBadge status={dbStatus} />
          </div>

          {user && (
            <div className="flex items-center gap-2">
              <span className="hidden lg:block text-xs text-slate-400 max-w-[140px] truncate">
                {user.full_name}
              </span>
              <button
                onClick={logout}
                title="Cerrar sesión"
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/20 transition-colors text-xs font-medium"
              >
                <ArrowRightStartOnRectangleIcon className="w-4 h-4" />
                <span className="hidden md:block">Salir</span>
              </button>
            </div>
          )}
        </div>

      </div>
    </nav>
  );
}