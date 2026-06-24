import type { GeographicRiskRow } from "@/types/analytics";
import { reliabilityBadge, discrepancyBadge } from "@/lib/analytics";

interface Props {
  rows: GeographicRiskRow[];
}

export function GeographicTable({ rows }: Props) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="bg-gray-50 border-b border-gray-100">
          {["Región", "Proveedores", "Facturas", "Fiabilidad media", "Tasa discrepancia"].map((h, i) => (
            <th
              key={h}
              className={`px-4 py-3 text-[11px] font-semibold uppercase tracking-wide text-gray-400 ${i > 0 ? "text-right" : "text-left"}`}
            >
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {rows.map((row) => (
          <tr key={row.region} className="hover:bg-gray-50 transition-colors">
            <td className="px-4 py-3 text-gray-900 font-medium">{row.region}</td>
            <td className="px-4 py-3 text-right font-mono text-gray-600 tabular-nums">{row.supplier_count}</td>
            <td className="px-4 py-3 text-right font-mono text-gray-600 tabular-nums">{row.total_invoices.toLocaleString("es-ES")}</td>
            <td className="px-4 py-3 text-right">
              <span className={`inline-flex justify-center px-2 py-0.5 rounded-full text-xs font-mono font-semibold min-w-[3.5rem] ${reliabilityBadge(row.avg_reliability)}`}>
                {(row.avg_reliability * 100).toFixed(1)}%
              </span>
            </td>
            <td className="px-4 py-3 text-right">
              <span className={`inline-flex justify-center px-2 py-0.5 rounded-full text-xs font-mono font-semibold min-w-[3.5rem] ${discrepancyBadge(row.discrepancy_pct)}`}>
                {row.discrepancy_pct}%
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}