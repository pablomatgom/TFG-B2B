"use client";

import type { SupplierScoreRow } from "@/types/analytics";
import { InfoTooltip } from "@/components/analytics/shared";
import { EUR } from "@/lib/analytics";

interface Props {
  rows:       SupplierScoreRow[];
  altoFloor:  number;
  medioFloor: number;
  view?:      "operativo" | "financiero";
}

export function ScoresTable({ rows, altoFloor, medioFloor, view = "operativo" }: Props) {
  const isFinanciero = view === "financiero";

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="bg-gray-50 border-b border-gray-100">
          <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-gray-400">#</th>
          <th className="px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-wide text-gray-400">Proveedor</th>

          {!isFinanciero && (
            <th className="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-wide text-gray-400">
              <span className="inline-flex items-center justify-end gap-1">
                Score
                <InfoTooltip direction="down" align="end" content={
                  <div className="space-y-1.5">
                    <p className="font-semibold text-white mb-2">Cálculo del Score</p>
                    <div className="flex justify-between gap-4">
                      <span className="text-gray-300">Discrepancias</span>
                      <span className="font-mono text-indigo-300">× 0.55</span>
                    </div>
                    <div className="flex justify-between gap-4">
                      <span className="text-gray-300">% Entrega tardía</span>
                      <span className="font-mono text-indigo-300">× 0.45</span>
                    </div>
                    <div className="border-t border-gray-700 pt-1.5 mt-1 flex justify-between gap-4">
                      <span className="text-gray-400 text-[10px]">Rango resultado</span>
                      <span className="font-mono text-[10px] text-gray-400">0 – 100</span>
                    </div>
                  </div>
                } />
              </span>
            </th>
          )}

          <th className="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-wide text-gray-400">Discrepancia %</th>
          <th className="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-wide text-gray-400">Entrega tardía %</th>
          <th className="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-wide text-gray-400 italic">Fiabilidad (inf.)</th>

          {isFinanciero && (
            <>
              <th className="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-wide text-gray-400">Fact. vencidas</th>
              <th className="px-4 py-3 text-right text-[11px] font-semibold uppercase tracking-wide text-gray-400">Importe vencido (€)</th>
            </>
          )}
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {rows.map((row, i) => (
          <tr key={row.supplier} className="hover:bg-gray-50 transition-colors">
            <td className="px-4 py-3 text-gray-400 text-xs tabular-nums w-8">{i + 1}</td>
            <td className="px-4 py-3 text-gray-900 font-medium max-w-[180px] truncate">{row.supplier}</td>

            {!isFinanciero && (
              <td className="px-4 py-3 text-right">
                <span className={`inline-flex justify-center px-2 py-0.5 rounded-full text-xs font-mono font-bold min-w-[3rem] ${
                  row.risk_score >= altoFloor   ? "bg-red-50 text-red-600"
                  : row.risk_score >= medioFloor ? "bg-amber-50 text-amber-600"
                  : "bg-indigo-50 text-indigo-600"
                }`}>
                  {row.risk_score.toFixed(1)}
                </span>
              </td>
            )}

            <td className="px-4 py-3 text-right font-mono text-gray-600 tabular-nums">
              {row.discrepancy_pct.toFixed(1)}%
            </td>
            <td className="px-4 py-3 text-right font-mono text-gray-600 tabular-nums">
              {row.late_pct.toFixed(1)}%
            </td>
            <td className="px-4 py-3 text-right font-mono text-gray-600 tabular-nums">
              {(row.avg_reliability * 100).toFixed(1)}%
            </td>

            {isFinanciero && (
              <>
                <td className={`px-4 py-3 text-right font-mono font-semibold tabular-nums ${row.overdue_count > 0 ? "text-red-600" : "text-gray-400"}`}>
                  {row.overdue_count ?? 0}
                </td>
                <td className={`px-4 py-3 text-right font-mono tabular-nums ${(row.overdue_eur ?? 0) > 0 ? "text-red-600" : "text-gray-400"}`}>
                  {(row.overdue_eur ?? 0) > 0 ? `${EUR(row.overdue_eur, 2)} €` : "—"}
                </td>
              </>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );
}