"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  HomeIcon, 
  AdjustmentsHorizontalIcon, 
  ChartBarIcon, 
  BeakerIcon 
} from "@heroicons/react/24/solid";

export default function Navbar() {
  const pathname = usePathname();

  const navLinks = [
    { name: "Inicio", href: "/", icon: HomeIcon },
    { name: "Dashboard", href: "/dashboard", icon: ChartBarIcon },
    { name: "Analytics GDS", href: "/analytics", icon: BeakerIcon },
    { name: "Pipeline", href: "/pipeline", icon: AdjustmentsHorizontalIcon },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0E1117]/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        
        {/* LOGO INTERACTIVO: Ahora envuelto en un Link */}
        <Link 
          href="/" 
          className="flex items-center space-x-2 hover:opacity-80 transition-opacity cursor-pointer"
        >
          <BeakerIcon className="w-6 h-6 text-cyan-500" />
          <span className="font-bold text-white text-lg tracking-wide hidden sm:block">
            B2B Graph Intel
          </span>
        </Link>

        {/* Enlaces de Navegación */}
        <div className="flex space-x-2 md:space-x-4">
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link key={link.name} href={link.href}>
                <div className={`flex items-center space-x-2 px-3 py-2 rounded-lg transition-colors text-sm font-medium
                  ${isActive 
                    ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20" 
                    : "text-slate-400 hover:text-white hover:bg-slate-800"
                  }`}
                >
                  <link.icon className="w-5 h-5" />
                  <span className="hidden md:block">{link.name}</span>
                </div>
              </Link>
            );
          })}
        </div>

      </div>
    </nav>
  );
}