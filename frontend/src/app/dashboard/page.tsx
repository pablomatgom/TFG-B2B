"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import {
  Card, Metric, Text, Grid, AreaChart, Title, Flex, Badge,
  DonutChart, Legend, BarList,
  Table, TableHead, TableHeaderCell, TableBody, TableRow, TableCell,
} from "@tremor/react";
import { ServerIcon } from "@heroicons/react/24/outline";

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

export default function DashboardPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/dashboard/macro")
      .then((res) => res.json())
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Error conectando a FastAPI:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <main className="p-10 max-w-7xl mx-auto flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mb-4" />
        <Text className="text-slate-400 animate-pulse">Sincronizando con el motor Neo4j...</Text>
      </main>
    );
  }

  if (!data || !data.macro_stats) {
    return (
      <main className="p-10 max-w-7xl mx-auto text-center">
        <Title className="text-red-400 mb-2">Sin conexión de datos</Title>
        <Text className="text-slate-500">
          Asegúrate de haber ejecutado el pipeline primero o de que FastAPI esté encendido.
        </Text>
      </main>
    );
  }

  const nodes = data.macro_stats.node_counts || {};
  const relationships = data.macro_stats.relationship_counts || {};
  const totalRelaciones = Object.values(relationships).reduce(
    (acc: number, v: unknown) => acc + (v as number),
    0
  );
  const seriesTemporales = data.temporal_series || [];

  const docTypeCounts: Record<string, number> = data.macro_stats.doc_type_counts || {};
  const docTypeChartData = Object.entries(docTypeCounts).map(([name, value]) => ({
    name,
    value: value as number,
  }));
  const docTypeColors = docTypeChartData.map(
    (d) => DOC_TYPE_COLORS[d.name] ?? "slate"
  );

  const topSuppliers = (data.macro_stats.top_suppliers || []).map((s: any) => ({
    name: s.legal_name,
    value: s.supplies_out,
  }));
  const topBuyers = (data.macro_stats.top_buyers || []).map((b: any) => ({
    name: b.legal_name,
    value: b.supplies_in,
  }));

  return (
    <main className="p-6 md:p-10 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500">

      <Flex justifyContent="between" alignItems="center">
        <div>
          <Title className="text-3xl font-bold text-white">Dashboard Macroscópico</Title>
          <Text className="text-slate-400">Visión global de la red logística en base de datos de grafos.</Text>
        </div>
      </Flex>

      {/* KPI CARDS */}
      <Grid numItemsSm={2} numItemsLg={4} className="gap-6">
        <Card decoration="top" decorationColor="blue" className="bg-[#1E212B] border-slate-800">
          <Text className="text-slate-400">Empresas Activas</Text>
          <Metric className="text-white mt-2">{nodes.Company?.toLocaleString() || 0}</Metric>
        </Card>
        <Card decoration="top" decorationColor="purple" className="bg-[#1E212B] border-slate-800">
          <Text className="text-slate-400">Catálogo Productos</Text>
          <Metric className="text-white mt-2">{nodes.Product?.toLocaleString() || 0}</Metric>
        </Card>
        <Card decoration="top" decorationColor="amber" className="bg-[#1E212B] border-slate-800">
          <Text className="text-slate-400">Documentos</Text>
          <Metric className="text-white mt-2">{nodes.Document?.toLocaleString() || 0}</Metric>
        </Card>
        <Card decoration="top" decorationColor="emerald" className="bg-[#1E212B] border-slate-800">
          <Text className="text-slate-400">Total Conexiones</Text>
          <Metric className="text-white mt-2">{totalRelaciones.toLocaleString()}</Metric>
        </Card>
      </Grid>

      {/* TEMPORAL CHART */}
      <Card className="bg-[#1E212B] border-slate-800">
        <Title className="text-white">Evolución de Transacciones Documentales</Title>
        <Text className="text-slate-400 mb-6">
          Línea temporal de la generación de contratos y facturas en el sistema.
        </Text>
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
          <Title className="text-white mb-1">Tipos de Documento</Title>
          <Text className="text-slate-400 mb-4">Distribución por categoría EDI.</Text>
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
            <Text className="text-slate-500 mt-6 text-center">Sin datos — ejecuta el pipeline primero.</Text>
          )}
        </Card>

        <Card className="bg-[#1E212B] border-slate-800">
          <Title className="text-white mb-1">Top Proveedores</Title>
          <Text className="text-slate-400 mb-4">Por número de clientes abastecidos.</Text>
          {topSuppliers.length > 0 ? (
            <BarList data={topSuppliers} color="cyan" valueFormatter={(n: number) => `${n} clientes`} />
          ) : (
            <Text className="text-slate-500 mt-6 text-center">Sin datos.</Text>
          )}
        </Card>

        <Card className="bg-[#1E212B] border-slate-800">
          <Title className="text-white mb-1">Top Compradores</Title>
          <Text className="text-slate-400 mb-4">Por número de proveedores recibidos.</Text>
          {topBuyers.length > 0 ? (
            <BarList data={topBuyers} color="violet" valueFormatter={(n: number) => `${n} proveedores`} />
          ) : (
            <Text className="text-slate-500 mt-6 text-center">Sin datos.</Text>
          )}
        </Card>
      </Grid>

      {/* SPAIN MAP */}
      <Card className="bg-[#1E212B] border-slate-800 p-0 overflow-hidden">
        <div className="p-6 pb-2">
          <Title className="text-white">Distribución Geográfica</Title>
          <Text className="text-slate-400">Concentración de empresas por municipio español.</Text>
        </div>
        <SpainMap />
      </Card>

    </main>
  );
}
