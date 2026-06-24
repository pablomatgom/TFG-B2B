"use client";

import { EyeIcon } from "@heroicons/react/24/outline";
import type { BuyerFragilityRow } from "@/types/analytics";
import { EUR, fragilityBadge } from "@/lib/analytics";

interface Props {
  rows:             BuyerFragilityRow[];
  onViewSuppliers?: (buyer: string) => void;
}

export function FragilityTable({ rows, onViewSuppliers }: Props) {
  const headers = ["Comprador", "Región", "Proveedores", "Dependencia Top %", "Volumen Total (€)", "Fact. vencidas", "Exposición vencida (€)", "Recomendaciones"];

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="bg-gray-50 border-b border-gray-100">
          {headers.map((h, i) => (
            <th
              key={h + i}
              className={`px-4 py-3 text-[11px] font-semibold uppercase tracking-wide text-gray-400 ${i > 1 && i < 7 ? "text-right" : "text-left"}`}
            >
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {rows.map((row) => {
          const dualRisk = row.top_supplier_pct >= 50 && (row.overdue_received ?? 0) > 0;
          return (
            <tr key={row.buyer} className={`transition-colors ${dualRisk ? "bg-amber-50/40 hover:bg-amber-50" : "hover:bg-gray-50"}`}>
              <td className="px-4 py-3 text-gray-900 font-medium max-w-[180px] truncate">
                {dualRisk && <span className="mr-1 text-amber-500 text-xs">⚠</span>}
                {row.buyer}
              </td>
              <td className="px-4 py-3 text-gray-500 text-xs">{row.region}</td>
              <td className="px-4 py-3 text-right font-mono text-gray-600 tabular-nums">{row.supplier_count}</td>
              <td className="px-4 py-3 text-right">
                <span className={`inline-flex justify-center px-2 py-0.5 rounded-full text-xs font-mono font-semibold min-w-[3rem] ${fragilityBadge(row.top_supplier_pct)}`}>
                  {row.top_supplier_pct.toFixed(1)}%
                </span>
              </td>
              <td className="px-4 py-3 text-right font-mono text-gray-600 tabular-nums">
                {EUR(row.total_volume_eur, 0)} €
              </td>
              <td className={`px-4 py-3 text-right font-mono font-semibold tabular-nums ${(row.overdue_received ?? 0) > 0 ? "text-red-600" : "text-gray-400"}`}>
                {row.overdue_received ?? 0}
              </td>
              <td className={`px-4 py-3 text-right font-mono tabular-nums ${(row.overdue_eur ?? 0) > 0 ? "text-red-600" : "text-gray-400"}`}>
                {(row.overdue_eur ?? 0) > 0 ? `${EUR(row.overdue_eur, 2)} €` : "—"}
              </td>
              <td className="px-4 py-3 text-left">
                {onViewSuppliers && (
                  <button
                    onClick={() => onViewSuppliers(row.buyer)}
                    title="Ver proveedores recomendados para este comprador"
                    className="p-1.5 rounded-lg text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
                  >
                    <EyeIcon className="w-4 h-4" />
                  </button>
                )}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}