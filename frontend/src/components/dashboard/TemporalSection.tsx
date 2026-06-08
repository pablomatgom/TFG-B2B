"use client";

import {
  ChartBarIcon,
  HashtagIcon,
  ArrowTrendingUpIcon,
  CalendarDaysIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";
import SectionHeader     from "@/components/dashboard/SectionHeader";
import TemporalAreaChart from "@/components/dashboard/TemporalAreaChart";

interface TemporalRow {
  date:      string;
  documents: number;
  flagged:   number;
}

interface TemporalSectionProps {
  data: TemporalRow[];
}

export default function TemporalSection({ data }: TemporalSectionProps) {
  const totalDocs    = data.reduce((s, r) => s + r.documents, 0);
  const totalFlagged = data.reduce((s, r) => s + r.flagged,   0);
  const peakRow      = data.reduce(
    (max, r) => r.documents > (max?.documents ?? 0) ? r : max,
    data[0] ?? null
  );
  const firstDate = data[0]?.date ?? "—";
  const lastDate  = data[data.length - 1]?.date ?? "—";
  const spanLabel = firstDate !== "—" ? `${firstDate} → ${lastDate}` : "—";

  const stats = [
    {
      icon:       HashtagIcon,
      label:      "Total documentos",
      value:      totalDocs > 0 ? totalDocs.toLocaleString("es") : "—",
      sub:        "en toda la serie",
    },
    {
      icon:       ArrowTrendingUpIcon,
      label:      "Mes pico",
      value:      peakRow ? peakRow.documents.toLocaleString("es") : "—",
      sub:        peakRow?.date ?? "—",
    },
    {
      icon:       CalendarDaysIcon,
      label:      "Período activo",
      value:      data.length > 0 ? `${data.length} meses` : "—",
      sub:        spanLabel,
    },
    {
      icon:       ExclamationTriangleIcon,
      label:      "Docs irregulares",
      value:      totalFlagged > 0 ? totalFlagged.toLocaleString("es") : "—",
      sub:        totalDocs > 0
        ? `${((totalFlagged / totalDocs) * 100).toFixed(1)}% del total`
        : "—",
    },
  ];

  return (
    <div className="animate-fade-up stagger-1 bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">

      {/* Header */}
      <div className="px-6 pt-6 pb-2">
        <SectionHeader
          icon={ChartBarIcon}
          title="Evolución de Transacciones Documentales"
          subtitle="Documentos totales e irregulares (discrepancia) por mes."
          iconColor="text-gray-500"
          iconBg="bg-gray-100"
        />
      </div>

      {data.length > 0 ? (
        <>
          {/* Stats strip — gap-px + bg-gray-100 creates 1px dividers */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-px bg-gray-100 border-y border-gray-100">
            {stats.map((s) => (
              <div key={s.label} className="bg-white px-5 py-4">
                <div className="flex items-center gap-1.5 mb-2">
                  <s.icon className="w-3.5 h-3.5 text-gray-400 shrink-0" aria-hidden />
                  <span className="text-[10px] font-bold uppercase tracking-[0.08em] text-gray-400 truncate">
                    {s.label}
                  </span>
                </div>
                <p className={`text-xl font-black tabular-nums leading-none text-gray-900`}>
                  {s.value}
                </p>
                <p className="text-[10px] font-mono text-gray-400 mt-1 truncate">
                  {s.sub}
                </p>
              </div>
            ))}
          </div>

          {/* Chart */}
          <div className="px-6 py-6">
            <TemporalAreaChart data={data} />
          </div>
        </>
      ) : (
        <div className="h-72 flex flex-col items-center justify-center px-6 pb-6 text-center">
          <ChartBarIcon className="w-8 h-8 text-gray-300 mb-3" />
          <p className="text-gray-500 text-sm font-medium">Sin datos temporales</p>
          <p className="text-gray-400 text-xs mt-1">
            Ejecuta el pipeline para visualizar el flujo de documentos.
          </p>
        </div>
      )}
    </div>
  );
}