"use client";

import {
  BuildingOffice2Icon,
  CubeIcon,
  DocumentTextIcon,
  ArrowsRightLeftIcon,
} from "@heroicons/react/24/outline";

const KPI_CONFIG = [
  { label: "Empresas Activas",   key: "Company",        icon: BuildingOffice2Icon },
  { label: "Catálogo Productos", key: "Product",        icon: CubeIcon            },
  { label: "Documentos EDI",     key: "Document",       icon: DocumentTextIcon    },
  { label: "Total Conexiones",   key: "__total_edges__", icon: ArrowsRightLeftIcon },
] as const;

const STAGGER = ["stagger-1", "stagger-2", "stagger-3", "stagger-4"] as const;

interface KpiGridProps {
  values: Record<string, number>;
  trends?: Record<string, number>;
}

export default function KpiGrid({ values, trends }: KpiGridProps) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
      {KPI_CONFIG.map((kpi, i) => {
        const delta = trends?.[kpi.key] ?? null;
        return (
          <div
            key={kpi.label}
            className={`animate-fade-up ${STAGGER[i]} bg-white rounded-xl border border-gray-200 shadow-sm p-5 hover:shadow-md hover:border-gray-300 transition-all duration-200`}
          >
            {/* Top row: icon + label + delta */}
            <div className="flex items-center gap-2">
              <kpi.icon className="w-4 h-4 text-gray-400 shrink-0" aria-hidden />
              <span className="text-xs text-gray-500 font-medium truncate flex-1">
                {kpi.label}
              </span>
              {delta !== null && (
                <span className={`text-[11px] font-semibold px-1.5 py-0.5 rounded-md shrink-0 ${
                  delta >= 0
                    ? "text-emerald-700 bg-emerald-50"
                    : "text-red-600 bg-red-50"
                }`}>
                  {delta >= 0 ? "+" : ""}{delta.toFixed(1)}%
                </span>
              )}
            </div>

            {/* Big number */}
            <p className="text-3xl font-black text-gray-900 tabular-nums leading-none mt-4">
              {(values[kpi.key] ?? 0).toLocaleString("es")}
            </p>
          </div>
        );
      })}
    </div>
  );
}