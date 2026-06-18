import { Bars3Icon } from "@heroicons/react/24/outline";
import { BRAND } from "@/lib/brand";

export default function TopBar({ onMenuClick }: { onMenuClick?: () => void }) {
  return (
    <div className="fixed top-0 left-0 lg:left-60 right-0 h-14 bg-white border-b border-gray-200 z-30 flex items-center px-4 lg:px-6 gap-3">
      {/* Hamburger — mobile only */}
      <button
        onClick={onMenuClick}
        className="lg:hidden p-1.5 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors shrink-0"
        aria-label="Abrir menú"
      >
        <Bars3Icon className="w-5 h-5" />
      </button>

      <div className="flex items-center gap-3 min-w-0">
        <span className="text-sm font-semibold text-gray-900 whitespace-nowrap">{BRAND.name}</span>
        <span className="text-gray-300 select-none hidden sm:inline">·</span>
        <span className="text-xs text-gray-500 truncate hidden lg:block">{BRAND.description}</span>
      </div>
      <div className="ml-auto flex items-center gap-2 shrink-0">
        {BRAND.capabilities.map((cap) => (
          <span
            key={cap}
            className="px-2.5 py-1 bg-indigo-50 text-indigo-700 text-xs font-semibold rounded-full hidden sm:inline-flex"
          >
            {cap}
          </span>
        ))}
      </div>
    </div>
  );
}