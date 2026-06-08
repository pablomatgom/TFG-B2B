"use client";

import { CpuChipIcon } from "@heroicons/react/24/outline";
import SectionHeader from "@/components/dashboard/SectionHeader";
import type { ScaleFreeMetrics } from "@/types/dashboard";

interface ScaleFreeSectionProps {
  scaleFree: Partial<ScaleFreeMetrics>;
}

export default function ScaleFreeSection({ scaleFree }: ScaleFreeSectionProps) {
  const giniVal  = scaleFree.gini_coefficient ?? null;
  const ratioVal = scaleFree.max_mean_ratio   ?? null;

  if (giniVal === null) return null;

  const meanDeg     = scaleFree.mean_degree ?? null;
  const degColor    = meanDeg === null ? "text-gray-400"
    : meanDeg < 2                      ? "text-amber-600"
    : meanDeg <= 6                     ? "text-emerald-600"
    :                                    "text-indigo-600";
  const degHint     = meanDeg === null ? "Sin datos"
    : meanDeg < 2                      ? "Red dispersa"
    : meanDeg <= 6                     ? "Conectividad típica"
    :                                    "Red densa";

  const hubCount   = scaleFree.hub_count ?? 0;
  const hubColor   = hubCount === 0     ? "text-gray-400"
    : hubCount <= 5                     ? "text-emerald-600"
    : hubCount <= 15                    ? "text-amber-600"
    :                                     "text-red-500";
  const hubHint    = hubCount === 0     ? "Sin hubs detectados"
    : hubCount <= 5                     ? "Topología saludable"
    : hubCount <= 15                    ? "Riesgo moderado"
    :                                     "Alta concentración";

  const giniColor = giniVal > 0.5 ? "text-emerald-600"
    : giniVal > 0.3               ? "text-amber-600"
    :                                "text-red-500";
  const giniHint  = giniVal > 0.5 ? "Scale-free confirmado"
    : giniVal > 0.3               ? "Desigualdad moderada"
    :                                "Distribución uniforme";

  const ratioColor = ratioVal === null ? "text-gray-400"
    : ratioVal > 5                     ? "text-emerald-600"
    : ratioVal > 3                     ? "text-amber-600"
    :                                    "text-red-500";
  const ratioHint  = ratioVal === null ? "Sin datos"
    : ratioVal > 5                     ? "Cola pesada - power-law"
    : ratioVal > 3                     ? "Cola moderada"
    :                                    "Cola ligera";

  return (
    <div className="animate-fade-up bg-white border border-gray-200 rounded-xl shadow-sm p-6">
      <SectionHeader
        icon={CpuChipIcon}
        title="Validación Topológica LFR"
        subtitle="Indicadores de distribución power-law sobre la red generada."
        iconColor="text-gray-500"
        iconBg="bg-gray-100"
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-2">

        <div className="px-4 py-4 bg-gray-50 border border-gray-200 rounded-xl">
          <p className="text-gray-500 text-[11px] font-semibold uppercase tracking-wide mb-2">
            Coef. Gini
          </p>
          <p className="text-2xl font-black tabular-nums text-gray-900">
            {giniVal.toFixed(4)}
          </p>
          <p className={`text-[11px] mt-1 font-medium ${giniColor}`}>{giniHint}</p>
          <p className="text-gray-400 text-[10px] mt-0.5">
            &gt;0.5 confirma red libre de escala
          </p>
        </div>

        <div className="px-4 py-4 bg-gray-50 border border-gray-200 rounded-xl">
          <p className="text-gray-500 text-[11px] font-semibold uppercase tracking-wide mb-2">
            Nodos Hub
          </p>
          <p className="text-2xl font-black tabular-nums text-gray-900">
            {scaleFree.hub_count ?? "—"}
          </p>
          <p className={`text-[11px] mt-1 font-medium ${hubColor}`}>{hubHint}</p>
          <p className="text-gray-400 text-[10px] mt-0.5">
            grado &gt; μ + 2σ ({scaleFree.hub_threshold ?? "—"})
          </p>
        </div>

        <div className="px-4 py-4 bg-gray-50 border border-gray-200 rounded-xl">
          <p className="text-gray-500 text-[11px] font-semibold uppercase tracking-wide mb-2">
            Ratio Max/Media
          </p>
          <p className="text-2xl font-black tabular-nums text-gray-900">
            {ratioVal !== null ? `${ratioVal}×` : "—"}
          </p>
          <p className={`text-[11px] mt-1 font-medium ${ratioColor}`}>{ratioHint}</p>
          <p className="text-gray-400 text-[10px] mt-0.5">
            &gt;5× indica distribución power-law
          </p>
        </div>

        <div className="px-4 py-4 bg-gray-50 border border-gray-200 rounded-xl">
          <p className="text-gray-500 text-[11px] font-semibold uppercase tracking-wide mb-2">
            Grado Medio
          </p>
          <p className="text-2xl font-black tabular-nums text-gray-900">
            {scaleFree.mean_degree ?? "—"}
          </p>
          <p className={`text-[11px] mt-1 font-medium ${degColor}`}>{degHint}</p>
          <p className="text-gray-400 text-[10px] mt-0.5">
            σ = {scaleFree.std_degree ?? "—"} · Máx: {scaleFree.max_degree ?? "—"} · Mín: {scaleFree.min_degree ?? "—"}
          </p>
        </div>

      </div>
    </div>
  );
}