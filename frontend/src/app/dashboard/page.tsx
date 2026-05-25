"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import {
  Card, Text, Grid, AreaChart, Title,
  DonutChart, Legend, BarList,
} from "@tremor/react";
import {
  BuildingOffice2Icon,
  CubeIcon,
  DocumentTextIcon,
  ArrowsRightLeftIcon,
  ChartBarIcon,
  DocumentDuplicateIcon,
  MapPinIcon,
} from "@heroicons/react/24/outline";
import { API_BASE } from "@/lib/api";
import { LoadingState, ErrorState } from "@/components/ui/LoadingState";

const SpainMap = dynamic(() => import("@/components/charts/SpainMap"), {
  ssr: false,
  loading: () => (
    <div className="h-[450px] w-full flex items-center justify-center rounded-xl border border-slate-800 bg-[#1E212B]">
      <div className="w-8 h-8 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin" />
      <span className="ml-3 text-slate-400">Cargando motor geográfico...</span>
    </div>
  ),
});

const DOC_TYPE_COLORS: Record<string, string> = {
  INVOICE: "cyan",
  ORDER: "blue",
  SHIPMENT: "emerald",
  CREDIT_NOTE: "amber",
};

const KPI_CONFIG = [
  {
    label: "Empresas Activas",
    key: "Company" as const,
    icon: BuildingOffice2Icon,
    iconBg: "bg-blue-500/10",
    iconColor: "text-blue-400",
    border: "border-blue-500/20 hover:border-blue-500/40",
    glow: "shadow-blue-500/5",
  },
  {
    label: "Catálogo Productos",
    key: "Product" as const,
    icon: CubeIcon,
    iconBg: "bg-purple-500/10",
    iconColor: "text-purple-400",
    border: "border-purple-500/20 hover:border-purple-500/40",
    glow: "shadow-purple-500/5",
  },
  {
    label: "Documentos EDI",
    key: "Document" as const,
    icon: DocumentTextIcon,
    iconBg: "bg-amber-500/10",
    iconColor: "text-amber-400",
    border: "border-amber-500/20 hover:border-amber-500/40",
    glow: "shadow-amber-500/5",
  },
  {
    label: "Total Conexiones",
    key: "__total_edges__" as const,
    icon: ArrowsRightLeftIcon,
    iconBg: "bg-emerald-500/10",
    iconColor: "text-emerald-400",
    border: "border-emerald-500/20 hover:border-emerald-500/40",
    glow: "shadow-emerald-500/5",
  },
];

function SectionHeader({
  icon: Icon,
  title,
  subtitle,
  iconColor = "text-cyan-400",
  iconBg = "bg-cyan-500/10",
}: {
  icon: React.ElementType;
  title: string;
  subtitle: string;
  iconColor?: string;
  iconBg?: string;
}) {
  return (
    <div className="flex items-start gap-3 mb-6">
      <div className={`p-2 ${iconBg} rounded-lg flex-shrink-0 mt-0.5`}>
        <Icon className={`w-5 h-5 ${iconColor}`} />
      </div>
      <div>
        <Title className="text-white leading-tight">{title}</Title>
        <Text className="text-slate-400 text-sm">{subtitle}</Text>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/dashboard/macro`)
      .then((res) => res.json())
      .then((json) => { setData(json); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState text="Sincronizando con el motor Neo4j..." />;
  if (!data || !data.macro_stats) {
    return (
      <ErrorState
        title="Sin conexión de datos"
        message="Asegúrate de haber ejecutado el pipeline primero o de que FastAPI esté encendido."
      />
    );
  }

  const nodes = data.macro_stats.node_counts || {};
  const relationships = data.macro_stats.relationship_counts || {};
  const totalRelaciones = Object.values(relationships).reduce(
    (acc: number, v: unknown) => acc + (v as number),
    0
  );
  const seriesTemporales = data.temporal_series || [];

  const kpiValues: Record<string, number> = {
    ...nodes,
    __total_edges__: totalRelaciones,
  };

  const docTypeCounts: Record<string, number> = data.macro_stats.doc_type_counts || {};
  const docTypeChartData = Object.entries(docTypeCounts).map(([name, value]) => ({
    name,
    value: value as number,
  }));
  const docTypeColors = docTypeChartData.map((d) => DOC_TYPE_COLORS[d.name] ?? "slate");

  const topSuppliers = (data.macro_stats.top_suppliers || []).map((s: any) => ({
    name: s.legal_name,
    value: s.supplies_out,
  }));
  const topBuyers = (data.macro_stats.top_buyers || []).map((b: any) => ({
    name: b.legal_name,
    value: b.supplies_in,
  }));

  return (
    <main className="p-6 md:p-10 max-w-7xl mx-auto space-y-10 animate-in fade-in duration-500">

      {/* PAGE HEADER */}
      <div>
        <h1 className="text-3xl font-bold text-white">Dashboard Macroscópico</h1>
        <p className="text-slate-400 mt-1">Visión global de la red logística en base de datos de grafos.</p>
      </div>

      {/* KPI CARDS */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
        {KPI_CONFIG.map((kpi) => (
          <div
            key={kpi.label}
            className={`bg-[#1E212B] rounded-2xl border ${kpi.border} p-5 md:p-6 flex items-center gap-4 transition-all duration-200 shadow-lg ${kpi.glow}`}
          >
            <div className={`p-3 ${kpi.iconBg} rounded-xl flex-shrink-0`}>
              <kpi.icon className={`w-6 h-6 ${kpi.iconColor}`} />
            </div>
            <div>
              <p className="text-slate-400 text-xs uppercase font-medium tracking-wide leading-tight">{kpi.label}</p>
              <p className="text-white text-2xl md:text-3xl font-bold mt-0.5 tabular-nums">
                {(kpiValues[kpi.key] ?? 0).toLocaleString("es")}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* TEMPORAL CHART */}
      <Card className="bg-[#1E212B] border-slate-800">
        <SectionHeader
          icon={ChartBarIcon}
          title="Evolución de Transacciones Documentales"
          subtitle="Línea temporal de la generación de contratos y facturas en el sistema."
        />
        <AreaChart
          className="h-80"
          data={seriesTemporales}
          index="date"
          categories={["documents"]}
          colors={["cyan"]}
          valueFormatter={(n: number) => Intl.NumberFormat("es").format(n).toString()}
          showLegend={false}
          showGridLines={true}
        />
      </Card>

      {/* DOC TYPE + TOP SUPPLIERS/BUYERS */}
      <Grid numItemsSm={1} numItemsLg={3} className="gap-6">
        <Card className="bg-[#1E212B] border-slate-800">
          <SectionHeader
            icon={DocumentDuplicateIcon}
            title="Tipos de Documento"
            subtitle="Distribución por categoría EDI."
            iconColor="text-amber-400"
            iconBg="bg-amber-500/10"
          />
          {docTypeChartData.length > 0 ? (
            <>
              <DonutChart
                className="h-44"
                data={docTypeChartData}
                category="value"
                index="name"
                colors={docTypeColors}
                valueFormatter={(n: number) => Intl.NumberFormat("es").format(n).toString()}
              />
              <Legend
                className="mt-3"
                categories={docTypeChartData.map((d) => d.name)}
                colors={docTypeColors}
              />
            </>
          ) : (
            <Text className="text-slate-500 py-8 text-center">Sin datos — ejecuta el pipeline primero.</Text>
          )}
        </Card>

        <Card className="bg-[#1E212B] border-slate-800">
          <SectionHeader
            icon={BuildingOffice2Icon}
            title="Top Proveedores"
            subtitle="Por número de clientes abastecidos."
            iconColor="text-cyan-400"
            iconBg="bg-cyan-500/10"
          />
          {topSuppliers.length > 0 ? (
            <BarList data={topSuppliers} color="cyan" valueFormatter={(n: number) => `${n} clientes`} />
          ) : (
            <Text className="text-slate-500 py-8 text-center">Sin datos.</Text>
          )}
        </Card>

        <Card className="bg-[#1E212B] border-slate-800">
          <SectionHeader
            icon={BuildingOffice2Icon}
            title="Top Compradores"
            subtitle="Por número de proveedores recibidos."
            iconColor="text-violet-400"
            iconBg="bg-violet-500/10"
          />
          {topBuyers.length > 0 ? (
            <BarList data={topBuyers} color="violet" valueFormatter={(n: number) => `${n} proveedores`} />
          ) : (
            <Text className="text-slate-500 py-8 text-center">Sin datos.</Text>
          )}
        </Card>
      </Grid>

      {/* SPAIN MAP */}
      <Card className="bg-[#1E212B] border-slate-800 p-0 overflow-hidden">
        <div className="p-6 pb-2">
          <SectionHeader
            icon={MapPinIcon}
            title="Distribución Geográfica"
            subtitle="Concentración de empresas por municipio español."
            iconColor="text-emerald-400"
            iconBg="bg-emerald-500/10"
          />
        </div>
        <SpainMap />
      </Card>

    </main>
  );
}