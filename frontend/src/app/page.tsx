"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import WelcomeHeader   from "@/components/dashboard/WelcomeHeader";
import SectionHeader   from "@/components/dashboard/SectionHeader";
import KpiGrid         from "@/components/dashboard/KpiGrid";
import HealthStrip     from "@/components/dashboard/HealthStrip";
import TemporalSection from "@/components/dashboard/TemporalSection";
import ScaleFreeSection from "@/components/dashboard/ScaleFreeSection";
import RankingsGrid    from "@/components/dashboard/RankingsGrid";
import { MapPinIcon }  from "@heroicons/react/24/outline";
import { API_BASE }    from "@/lib/api";
import { LoadingState, ErrorState, EmptyState } from "@/components/ui/LoadingState";
import { useAuth }     from "@/contexts/AuthContext";
import type { DashboardResponse } from "@/types/dashboard";

const SpainMap = dynamic(() => import("@/components/charts/SpainMap"), {
  ssr: false,
  loading: () => (
    <div className="h-[450px] w-full flex items-center justify-center rounded-xl border border-gray-200 bg-gray-50">
      <div className="w-7 h-7 border-[3px] border-indigo-500 border-t-transparent rounded-full animate-spin" />
      <span className="ml-3 text-gray-500 text-sm">Cargando motor geográfico...</span>
    </div>
  ),
});

export default function DashboardPage() {
  const { user }              = useAuth();
  const [data, setData]       = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/dashboard/macro`)
      .then((r) => r.json())
      .then((json) => { setData(json); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState text="Sincronizando con el motor Neo4j..." />;
  if (!data?.macro_stats) {
    return (
      <ErrorState
        title="Sin conexión de datos"
        message="Asegúrate de haber ejecutado el pipeline primero o de que FastAPI esté encendido."
      />
    );
  }

  const nodes         = data.macro_stats.node_counts         ?? {};
  const relationships = data.macro_stats.relationship_counts ?? {};
  const totalNodes    = Object.values(nodes).reduce((acc, v) => acc + v, 0);

  if (totalNodes === 0) {
    return <EmptyState isAdmin={user?.role === "admin"} />;
  }

  const totalRelaciones = Object.values(relationships).reduce((acc, v) => acc + v, 0);
  const kpiValues: Record<string, number> = { ...nodes, __total_edges__: totalRelaciones };

  const docTypeChartData = Object.entries(data.macro_stats.doc_type_counts ?? {}).map(
    ([name, value]) => ({ name, value })
  );
  const topSuppliers = (data.macro_stats.top_suppliers ?? []).map((s) => ({
    name: s.legal_name, value: s.supplies_out,
  }));
  const topBuyers = (data.macro_stats.top_buyers ?? []).map((b) => ({
    name: b.legal_name, value: b.supplies_in,
  }));
  const seriesTemporales = (data.temporal_series ?? []).map((row) => ({
    ...row,
    date: `${row.year}-${String(row.month).padStart(2, "0")}`,
  }));

  return (
    <main className="p-6 max-w-7xl mx-auto space-y-6">

      <WelcomeHeader />

      <KpiGrid
        values={kpiValues}
        trends={(() => {
          if (seriesTemporales.length < 2) return undefined;
          const prev = seriesTemporales[seriesTemporales.length - 2];
          const last = seriesTemporales[seriesTemporales.length - 1];
          const delta = (p: number, l: number) =>
            p > 0 ? ((l - p) / p) * 100 : null;
          const trends: Record<string, number> = {};
          const doc  = delta(prev.documents,          last.documents);
          const comp = delta(prev.active_companies,  last.active_companies);
          const prod = delta(prev.active_products,   last.active_products);
          const conn = delta(prev.active_connections, last.active_connections);
          if (doc  !== null) trends["Document"]        = doc;
          if (comp !== null) trends["Company"]         = comp;
          if (prod !== null) trends["Product"]         = prod;
          if (conn !== null) trends["__total_edges__"] = conn;
          return Object.keys(trends).length ? trends : undefined;
        })()}
      />

      <HealthStrip
        econVol={data.macro_stats.economic_volume ?? {
          invoice_count: 0, total_gross_eur: 0, total_tax_eur: 0, total_net_eur: 0,
        }}
        docHealth={data.macro_stats.document_health ?? {
          total_documents: 0, flagged_documents: 0, overall_discrepancy_rate_pct: 0,
        }}
        sparkVol={seriesTemporales.map((r) => r.total_gross_eur)}
        sparkDisc={seriesTemporales.map((r) => r.flagged)}
        sparkRate={seriesTemporales.map((r) =>
          r.documents > 0 ? (r.flagged / r.documents) * 100 : 0
        )}
      />

      <TemporalSection data={seriesTemporales} />

      <RankingsGrid
        docTypes={docTypeChartData}
        suppliers={topSuppliers}
        buyers={topBuyers}
      />

      <ScaleFreeSection scaleFree={data.macro_stats.scale_free_metrics ?? {}} />

      {/* <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
        <SectionHeader
          icon={MapPinIcon}
          title="Distribución Geográfica"
          subtitle="Concentración de empresas por municipio español."
          iconColor="text-emerald-600"
          iconBg="bg-emerald-50"
        />
        <SpainMap />
      </div> */}

    </main>
  );
}