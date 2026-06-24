"use client";

import BarChart from "@/components/charts/BarChart";
import type { LeadTimeRow } from "@/types/analytics";
import { lateBarColor, lateBadge, SIGN } from "@/lib/analytics";
import { EMPTY, SectionLabel, KpiStrip, ProgressBar } from "./shared";

function delayColor(d: number) {
  if (d >= 3) return "#ef4444";
  if (d >  0) return "#f59e0b";
  return "#10b981";
}

interface Props { leadTime: LeadTimeRow[]; }

export function LeadTimeTab({ leadTime }: Props) {
  if (leadTime.length === 0) return EMPTY;

  const overallTotal   = leadTime.reduce((s, r) => s + r.sample,     0);
  const overallLate    = leadTime.reduce((s, r) => s + r.late_count,  0);
  const overallLatePct = overallTotal > 0 ? (overallLate / overallTotal) * 100 : 0;
  const catsLate       = leadTime.filter((r) => r.sample > 0 && r.avg_delay_days > 0).length;

  return (
    <div className="space-y-10">

      {/* ── 01 · RETRASO MEDIO POR CATEGORÍA ────────────────────── */}
      <section>
        <SectionLabel
          index="01 /"
          title="Desviación de Plazos por Categoría de Producto"
          subtitle="Diferencia media en días entre la fecha de entrega real y el plazo acordado con el proveedor. Los valores negativos indican entregas anticipadas; los positivos, entregas fuera de plazo."
        />
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
          <div className="p-5">
            <BarChart
              data={leadTime.filter((r) => r.sample > 0)}
              index="category"
              category="avg_delay_days"
              layout="vertical"
              yAxisWidth={160}
              rowHeight={28}
              valueFormatter={(n) => `${SIGN(n)}${n.toFixed(1)} d`}
              colorFn={delayColor}
            />
          </div>
          {/* Legend strip */}
          <div className="px-5 pt-4 pb-3 border-b border-gray-100 flex flex-wrap items-center justify-center gap-4">
            {[
              { color: "bg-emerald-500", label: "Entregado antes del plazo" },
              { color: "bg-amber-500",   label: "Retraso leve (0 – 3 días)" },
              { color: "bg-red-500",     label: "Retraso significativo (≥ 3 días)" },
            ].map((l) => (
              <span key={l.label} className="flex items-center gap-1.5 text-xs text-gray-500">
                <span className={`w-2.5 h-2.5 rounded-sm shrink-0 ${l.color}`} />
                {l.label}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── 02 · CUMPLIMIENTO DE PLAZOS ─────────────────────────── */}
      <section>
        <SectionLabel
          index="02 /"
          title="Tasa de Incumplimiento por Categoría"
          subtitle="Proporción de pedidos que no cumplieron el plazo de entrega acordado, desglosada por categoría de producto. Una tasa elevada en una categoría indica riesgo operativo activo y puede requerir revisión contractual con el proveedor."
        />

        <KpiStrip items={[
          { label: "Pedidos analizados",    value: overallTotal.toLocaleString("es-ES") },
          { label: "Pedidos con retraso",   value: overallLate.toLocaleString("es-ES")  },
          { label: "Incumplimiento global", value: `${overallLatePct.toFixed(1)}%`      },
        ]} />

        {/* Progress rows */}
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5">
          {/* Sub-header */}
          <div className="flex items-center justify-between mb-4">
            <p className="text-gray-700 font-semibold text-sm">Tasa de incumplimiento por categoría de producto</p>
            <span className="text-xs text-gray-400">
              {catsLate} de {leadTime.length} categoría{leadTime.length !== 1 ? "s" : ""} presentan retrasos
            </span>
          </div>
          <div className="space-y-4">
            {[...leadTime].sort((a, b) => b.late_pct - a.late_pct).map((row) => (
              <div key={row.category} className={row.sample === 0 ? "opacity-40" : ""}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-gray-800 text-sm font-medium">{row.category}</span>
                  {row.sample === 0 ? (
                    <span className="text-[11px] text-gray-400 italic">Sin datos</span>
                  ) : (
                    <span className={`font-mono text-xs font-semibold px-2 py-0.5 rounded-full tabular-nums ${lateBadge(row.late_pct)}`}>
                      {row.late_pct.toFixed(1)}%
                      <span className="font-normal text-[10px] ml-1 opacity-70">
                        ({row.late_count.toLocaleString()} / {row.sample.toLocaleString()})
                      </span>
                    </span>
                  )}
                </div>
                <ProgressBar pct={row.late_pct} colorClass={lateBarColor(row.late_pct)} transition />
              </div>
            ))}
          </div>
        </div>
      </section>

    </div>
  );
}