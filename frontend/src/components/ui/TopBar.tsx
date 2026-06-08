import { BRAND } from "@/lib/brand";

export default function TopBar() {
  return (
    <div className="fixed top-0 left-60 right-0 h-14 bg-white border-b border-gray-200 z-30 flex items-center px-6 gap-4">
      <div className="flex items-center gap-3 min-w-0">
        <span className="text-sm font-semibold text-gray-900 whitespace-nowrap">{BRAND.name}</span>
        <span className="text-gray-300 select-none">·</span>
        <span className="text-xs text-gray-500 truncate hidden lg:block">{BRAND.description}</span>
      </div>
      <div className="ml-auto flex items-center gap-2 shrink-0">
        {BRAND.capabilities.map((cap) => (
          <span
            key={cap}
            className="px-2.5 py-1 bg-indigo-50 text-indigo-700 text-xs font-semibold rounded-full"
          >
            {cap}
          </span>
        ))}
      </div>
    </div>
  );
}