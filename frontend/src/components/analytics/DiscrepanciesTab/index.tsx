"use client";

import { useState, useMemo } from "react";
import BarChart   from "@/components/charts/BarChart";
import RingChart  from "@/components/charts/RingChart";
import type { DiscrepancyRow, CommercialImpactRow } from "@/types/analytics";
import { EMPTY, SectionLabel, ShowMoreButton, SectionModal, KpiStrip } from "@/components/analytics/shared";
import { PAGE_SIZE as PAGE } from "@/lib/analytics";
import { DiscrepancyTable } from "./DiscrepancyTable";
import { CommercialTable }  from "./CommercialTable";

interface Props {
  discrepancy: DiscrepancyRow[];
  commercial:  CommercialImpactRow[];
}

export function DiscrepanciesTab({ discrepancy, commercial }: Props) {
  const [showCommercialAll,  setShowCommercialAll]  = useState(false);
  const [showDiscrepancyAll, setShowDiscrepancyAll] = useState(false);
  const [tolerance,          setTolerance]          = useState<number>(5);

  const hasDiscrepancy = discrepancy.length > 0;
  const hasCommercial  = commercial.length  > 0;

  // Adaptive slider bound — round up to a clean step above the largest |delta_pct|
  const toleranceMax = useMemo(() => {
    if (commercial.length === 0) return 10;
    const maxAbs = commercial.reduce(
      (m, r) => (r.delta_pct != null ? Math.max(m, Math.abs(r.delta_pct)) : m),
      0,
    );
    return Math.max(5, Math.ceil(maxAbs / 0.5) * 0.5);
  }, [commercial]);

  // Reclassify each order against the current tolerance band — preserves the
  // backend semantics (SOBRE / SUB / CONFORME) but lets the threshold flex with
  // the actual distribution instead of the hard-coded ±5 %.
  const reclassified = useMemo(() => {
    return commercial.map((r) => {
      if (r.delta_pct == null) return r;
      let estado: typeof r.estado_comercial = "CONFORME";
      if (r.delta_pct >  tolerance) estado = "SOBREFACTURADO";
      if (r.delta_pct < -tolerance) estado = "SUBFACTURADO";
      return { ...r, estado_comercial: estado };
    });
  }, [commercial, tolerance]);

  // Stable section indices — only count visible sections
  const sectionIdx = useMemo(() => {
    const visible = [
      { key: "disc", show: hasDiscrepancy },
      { key: "comm", show: hasCommercial  },
    ];
    let n = 1;
    const map: Record<string, string> = {};
    for (const s of visible) {
      if (s.show) map[s.key] = `${String(n++).padStart(2, "0")} /`;
    }
    return map;
  }, [hasDiscrepancy, hasCommercial]);

  if (!hasDiscrepancy && !hasCommercial) return EMPTY;

  const discChartData = discrepancy.slice(0, 20);

  // ── Discrepancy KPIs ─────────────────────────────────────────
  const avgRate    = discrepancy.length > 0
    ? (discrepancy.reduce((s, r) => s + r.discrepancy_rate_pct, 0) / discrepancy.length).toFixed(1)
    : "—";
  const worstRow   = discrepancy[0];

  // ── Commercial KPIs ──────────────────────────────────────────
  const cmOk    = reclassified.filter((r) => r.estado_comercial === "CONFORME").length;
  const cmSub   = reclassified.filter((r) => r.estado_comercial === "SUBFACTURADO").length;
  const cmSobre = reclassified.filter((r) => r.estado_comercial === "SOBREFACTURADO").length;
  const conformePct = reclassified.length > 0
    ? ((cmOk / reclassified.length) * 100).toFixed(1)
    : "—";
  const tolLabel = `±${tolerance.toFixed(1)}%`;

  return (
    <div className="space-y-10">

      {/* ── TASA DE DISCREPANCIA POR PROVEEDOR ──────────────────── */}
      {hasDiscrepancy && (
        <section>
          <SectionLabel
            index={sectionIdx["disc"]}
            title="Tasa de Discrepancia por Proveedor"
            subtitle="¿Qué proveedores generan más documentos erróneos sobre el total emitido? Solo se incluyen proveedores con mínimo 5 facturas para evitar sesgos estadísticos. Ordenados por tasa descendente."
          />

          <KpiStrip variant="strip" valueSize="lg" items={[
            { label: "Proveedores con historial", value: discrepancy.length.toString()                                                              },
            { label: "Tasa de discrepancia media", value: `${avgRate}%`                                                                             },
            { label: "Mayor tasa registrada",      value: worstRow ? `${worstRow.discrepancy_rate_pct}%` : "—", sub: worstRow?.supplier },
          ]} />

          <div className="space-y-4">
            <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
              <div className="px-5 pt-4 pb-3 border-b border-gray-100">
                <p className="text-gray-700 font-semibold text-sm">% de facturas con discrepancia por proveedor</p>
              </div>
              <div className="p-5">
                <BarChart
                  data={discChartData}
                  index="supplier"
                  category="discrepancy_rate_pct"
                  layout="vertical"
                  yAxisWidth={160}
                  rowHeight={22}
                  valueFormatter={(n) => `${n}%`}
                  colorFn={(v) => v >= 10 ? "#ef4444" : v >= 7.5 ? "#f59e0b" : "#6366f1"}
                />
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
              <DiscrepancyTable rows={discrepancy.slice(0, PAGE)} />
              {discrepancy.length > PAGE && (
                <div className="px-5 py-3 border-t border-gray-100 bg-gray-50">
                  <ShowMoreButton total={discrepancy.length} onClick={() => setShowDiscrepancyAll(true)} />
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* ── IMPACTO COMERCIAL ────────────────────────────────────── */}
      {hasCommercial && (
        <section>
          <SectionLabel
            index={sectionIdx["comm"]}
            title="Conciliación Pedido-Factura"
            subtitle={`¿Las facturas recibidas coinciden con los pedidos emitidos? Diferencias superiores al ${tolLabel} se clasifican como sobre o subfacturación e indican un riesgo financiero o contractual activo.`}
          />

          <div className="space-y-4">
            <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5">
              <p className="text-gray-700 font-semibold text-sm mb-1">Resultado de conciliación</p>
              <p className="text-gray-400 text-xs mb-5">
                Cada orden se clasifica comparando el importe del pedido con el total facturado. La banda de tolerancia es ajustable: por debajo se considera conforme; fuera de ella, sobre o subfacturada.
              </p>

              <div className="grid grid-cols-2 gap-6 items-center">
                {/* Left — ring chart */}
                <RingChart
                  data={[
                    { name: "Conformes",       value: cmOk,    color: "#10b981" },
                    { name: "Subfacturados",   value: cmSub,   color: "#f59e0b" },
                    { name: "Sobrefacturados", value: cmSobre, color: "#ef4444" },
                  ]}
                  centerLabel={`${conformePct}%`}
                  centerSub="conformes"
                  formatHoverValue={(v, t) =>
                    `${v} órdenes · ${t > 0 ? ((v / t) * 100).toFixed(1) : 0}%`
                  }
                />

                {/* Right — KPIs + slider */}
                <div className="space-y-4">

                  {/* KPI cards */}
                  <div className="flex flex-col">
                    {[
                      { label: "Órdenes conciliadas", value: reclassified.length.toString() },
                      { label: "Sin desviación",      value: cmOk.toString(),               },
                      { label: "Con desviación",      value: (cmSobre + cmSub).toString(),  },
                    ].map((kpi) => (
                      <div
                        key={kpi.label}
                        className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0 last:pb-0"
                      >
                        <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-500">
                          {kpi.label}
                        </p>
                        <p className={`text-lg font-bold tabular-nums leading-none text-gray-600`}>
                          {kpi.value}
                        </p>
                      </div>
                    ))}
                  </div>

                  <div className="border-t border-gray-100" />

                  {/* Custom slider */}
                  <div>
                    <div className="flex items-center justify-between gap-4 mb-4">
                      <div>
                        <p className="text-[11px] font-semibold uppercase tracking-wider text-gray-500">
                          Banda de tolerancia
                        </p>
                        <p className="text-gray-400 text-[10px] mt-0.5">
                          Órdenes fuera de este margen se clasifican como desviadas
                        </p>
                      </div>
                      {/* Valor limpio, sin caja, alineado tipográficamente con los KPIs */}
                      <div className="shrink-0 text-right">
                        <p className="text-sm font-bold tabular-nums text-gray-900 leading-none">
                          {tolLabel}
                        </p>
                      </div>
                    </div>

                    <div className="relative h-5 flex items-center">
                      {/* Track background */}
                      <div className="absolute w-full h-1.5 rounded-full bg-gray-200" />
                      {/* Filled track */}
                      <div
                        className="absolute h-1.5 rounded-full bg-indigo-500 transition-all duration-75"
                        style={{ width: `${(tolerance / toleranceMax) * 100}%` }}
                      />
                      {/* Native input — invisible but functional */}
                      <input
                        id="tolerance-slider"
                        type="range"
                        min={0}
                        max={toleranceMax}
                        step={0.1}
                        value={tolerance}
                        onChange={(e) => setTolerance(parseFloat(e.target.value))}
                        className={[
                          "absolute w-full cursor-pointer appearance-none bg-transparent",
                          "[&::-webkit-slider-thumb]:appearance-none",
                          "[&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4",
                          "[&::-webkit-slider-thumb]:rounded-full",
                          "[&::-webkit-slider-thumb]:bg-white",
                          "[&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-indigo-500",
                          "[&::-webkit-slider-thumb]:shadow-md",
                          "[&::-webkit-slider-thumb]:transition-transform",
                          "[&::-webkit-slider-thumb]:hover:scale-125",
                          "[&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:h-4",
                          "[&::-moz-range-thumb]:rounded-full",
                          "[&::-moz-range-thumb]:bg-white",
                          "[&::-moz-range-thumb]:border-2 [&::-moz-range-thumb]:border-indigo-500",
                          "[&::-moz-range-thumb]:shadow-md",
                          "[&::-moz-range-thumb]:cursor-pointer",
                          "[&::-moz-range-track]:bg-transparent",
                        ].join(" ")}
                      />
                    </div>

                    <div className="flex justify-between text-[10px] font-mono text-gray-400 mt-2 tabular-nums">
                      <span>±0%</span>
                      <span>±{toleranceMax.toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
              <CommercialTable rows={reclassified.slice(0, PAGE)} />
              {reclassified.length > PAGE && (
                <div className="px-5 py-3 border-t border-gray-100 bg-gray-50">
                  <ShowMoreButton total={reclassified.length} onClick={() => setShowCommercialAll(true)} />
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* ── MODALS ───────────────────────────────────────────────── */}
      <SectionModal
        title={`Tasa de Discrepancia — ${discrepancy.length} proveedores`}
        open={showDiscrepancyAll}
        onClose={() => setShowDiscrepancyAll(false)}
      >
        <DiscrepancyTable rows={discrepancy} />
      </SectionModal>

      <SectionModal
        title={`Impacto Comercial — banda ${tolLabel}`}
        open={showCommercialAll}
        onClose={() => setShowCommercialAll(false)}
      >
        <CommercialTable rows={reclassified} />
      </SectionModal>

    </div>
  );
}