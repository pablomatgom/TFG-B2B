"use client";

import { useState } from "react";
import {
  BanknotesIcon,
  ExclamationTriangleIcon,
  SignalIcon,
} from "@heroicons/react/24/outline";
import type { MacroStats } from "@/types/dashboard";
import MiniSparkline from "./MiniSparkline";

type Props = {
  econVol:    MacroStats["economic_volume"];
  docHealth:  MacroStats["document_health"];
  sparkVol?:  number[];
  sparkDisc?: number[];
  sparkRate?: number[];
};

const formatEUR = (n: number) =>
  Intl.NumberFormat("es-ES", {
    style: "currency", currency: "EUR",
    notation: "compact", maximumFractionDigits: 1,
  }).format(n);

function trendPct(data: number[]): number | null {
  if (data.length < 2) return null;
  const prev = data[data.length - 2];
  const last = data[data.length - 1];
  if (prev === 0) return null;
  return ((last - prev) / prev) * 100;
}

function StatCard({
  icon, label, value, sub,
  sparkData, sparkId, formatHover, invertTrend,
}: {
  icon:         React.ReactNode;
  label:        string;
  value:        string;
  sub:          string;
  sparkData?:   number[];
  sparkId:      string;
  formatHover:  (v: number) => string;
  invertTrend?: boolean;
}) {
  const [hovered, setHovered] = useState<number | null>(null);
  const trend = sparkData ? trendPct(sparkData) : null;
  const isGood = trend === null ? null : (invertTrend ? trend <= 0 : trend >= 0);
  const sparkColor = isGood === null ? "#9ca3af" : isGood ? "#10b981" : "#ef4444";

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 hover:shadow-md hover:border-gray-300 transition-all duration-200">
      {/* Header: icon + label */}
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-xs text-gray-500 font-medium truncate">{label}</span>
      </div>

      {/* Sparkline — full width */}
      <div className="h-14 w-full mt-2 -mx-1">
        {sparkData?.length ? (
          <MiniSparkline
            data={sparkData}
            color={sparkColor}
            id={sparkId}
            onHoverValue={setHovered}
          />
        ) : null}
      </div>

      {/* Value + trend + hovered point */}
      <div className="mt-2 flex items-end justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-baseline gap-2 flex-wrap">
            <span className="text-2xl font-black text-gray-900 tabular-nums leading-none">
              {value}
            </span>
            {trend !== null && (
              <span className={`text-[11px] font-semibold ${
                (invertTrend ? trend <= 0 : trend >= 0) ? "text-emerald-600" : "text-red-500"
              }`}>
                {trend >= 0 ? "↑" : "↓"} {Math.abs(trend).toFixed(1)}%
              </span>
            )}
          </div>
          <p className="text-gray-400 text-[10px] font-mono mt-1">{sub}</p>
        </div>

        <div className="shrink-0 text-right h-4">
          {hovered !== null && (
            <span className="text-xs font-mono font-semibold text-gray-500">
              {formatHover(hovered)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

export default function HealthStrip({ econVol, docHealth, sparkVol, sparkDisc, sparkRate }: Props) {
  return (
    <div className="animate-fade-up grid grid-cols-1 sm:grid-cols-3 gap-3 md:gap-4">
      <StatCard
        icon={<BanknotesIcon className="w-4 h-4 text-gray-400 shrink-0" aria-hidden />}
        label="Volumen Bruto Total"
        value={econVol.total_gross_eur != null ? formatEUR(econVol.total_gross_eur) : "—"}
        sub={econVol.invoice_count != null ? `${econVol.invoice_count.toLocaleString("es")} facturas emitidas` : ""}
        sparkData={sparkVol}
        sparkId="spark-health-vol"
        formatHover={formatEUR}
      />
      <StatCard
        icon={<ExclamationTriangleIcon className="w-4 h-4 text-gray-400 shrink-0" aria-hidden />}
        label="Docs con Discrepancia"
        value={docHealth.flagged_documents.toLocaleString("es")}
        sub={`de ${docHealth.total_documents.toLocaleString("es")} documentos totales`}
        sparkData={sparkDisc}
        sparkId="spark-health-disc"
        formatHover={(v) => `${Math.round(v).toLocaleString("es")} docs`}
        invertTrend
      />
      <StatCard
        icon={<SignalIcon className="w-4 h-4 text-gray-400 shrink-0" aria-hidden />}
        label="Tasa Global Discrepancia"
        value={`${docHealth.overall_discrepancy_rate_pct}%`}
        sub="sobre el total de documentos"
        sparkData={sparkRate}
        sparkId="spark-health-rate"
        formatHover={(v) => `${v.toFixed(1)}%`}
        invertTrend
      />
    </div>
  );
}