"use client";

import { useState, useEffect } from "react";
import {
  Card, Title, Text, Metric, Grid, Flex, Badge,
  BarChart, BarList,
  Table, TableHead, TableHeaderCell, TableBody, TableRow, TableCell,
} from "@tremor/react";
import {
  ExclamationTriangleIcon,
  ShieldExclamationIcon,
  ClockIcon,
  CurrencyEuroIcon,
} from "@heroicons/react/24/outline";

const API = "http://localhost:8000";

interface RiskData {
  total_supplies_edges: number;
  top_n: number;
  concentration_pct: number;
  top_suppliers: { name: string; degree: number; share_pct: number }[];
}

interface DiscrepancyRow {
  supplier: string;
  total: number;
  flagged: number;
  discrepancy_rate_pct: number;
}

interface LeadTimeRow {
  category: string;
  avg_delay_days: number;
  sample: number;
  late_count: number;
  late_pct: number;
}

interface PaymentRow {
  supplier: string;
  total_exposure_eur: number;
  avg_payment_days: number;
  invoice_count: number;
}

interface LineageRow {
  factura_id: string;
  riesgo_economico: number;
  pedido_original: string;
  proveedor: string;
  afectado: string;
  id_productos_implicados: string[];
  saltos_topologicos: number;
}

interface GdsData {
  bottlenecks: { company_id: string; legal_name: string; role: string; betweenness_score: number }[];
  communities: { communityId: number; total_empresas: number; ejemplos_empresas: string[] }[];
}

function rateColor(rate: number): string {
  if (rate >= 20) return "text-red-400";
  if (rate >= 10) return "text-amber-400";
  return "text-emerald-400";
}

function rateBadge(rate: number): "red" | "yellow" | "emerald" {
  if (rate >= 20) return "red";
  if (rate >= 10) return "yellow";
  return "emerald";
}

export default function AnalyticsPage() {
  const [risk, setRisk] = useState<RiskData | null>(null);
  const [discrepancy, setDiscrepancy] = useState<DiscrepancyRow[]>([]);
  const [leadTime, setLeadTime] = useState<LeadTimeRow[]>([]);
  const [payment, setPayment] = useState<PaymentRow[]>([]);
  const [lineage, setLineage] = useState<LineageRow[]>([]);
  const [gds, setGds] = useState<GdsData>({ bottlenecks: [], communities: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/dashboard/risk`).then((r) => r.json()),
      fetch(`${API}/api/dashboard/discrepancy-suppliers`).then((r) => r.json()),
      fetch(`${API}/api/dashboard/lead-time`).then((r) => r.json()),
      fetch(`${API}/api/dashboard/payment`).then((r) => r.json()),
      fetch(`${API}/api/dashboard/lineage`).then((r) => r.json()),
      fetch(`${API}/api/dashboard/gds`).then((r) => r.json()),
    ])
      .then(([riskData, discData, ltData, payData, linData, gdsData]) => {
        setRisk(riskData && riskData.total_supplies_edges ? riskData : null);
        setDiscrepancy(Array.isArray(discData) ? discData : []);
        setLeadTime(Array.isArray(ltData) ? ltData : []);
        setPayment(Array.isArray(payData) ? payData : []);
        setLineage(Array.isArray(linData) ? linData : []);
        setGds(gdsData || { bottlenecks: [], communities: [] });
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <main className="p-10 max-w-7xl mx-auto flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mb-4" />
        <Text className="text-slate-400 animate-pulse">Cargando analítica avanzada...</Text>
      </main>
    );
  }

  const noData = !risk && discrepancy.length === 0 && leadTime.length === 0 && payment.length === 0;

  return (
    <main className="p-6 md:p-10 max-w-7xl mx-auto space-y-10 animate-in fade-in duration-500">

      <div>
        <Title className="text-3xl font-bold text-white">Analítica Avanzada de Red</Title>
        <Text className="text-slate-400">
          Riesgo de concentración, calidad documental, cumplimiento operativo y exposición financiera.
        </Text>
      </div>

      {noData && (
        <Card className="bg-[#1E212B] border-slate-800 text-center py-12">
          <Text className="text-slate-500">
            No hay datos. Ejecuta primero el pipeline completo desde{" "}
            <a href="/pipeline" className="text-cyan-400 underline">Pipeline</a>.
          </Text>
        </Card>
      )}

      {/* SECTION 1: RISK CONCENTRATION */}
      {risk && (
        <section className="space-y-4">
          <Flex alignItems="center" className="gap-2">
            <ShieldExclamationIcon className="w-5 h-5 text-red-400" />
            <Title className="text-white">Concentración de Riesgo en Red</Title>
          </Flex>
          <Grid numItemsSm={1} numItemsLg={3} className="gap-6">
            <Card decoration="top" decorationColor="red" className="bg-[#1E212B] border-slate-800">
              <Text className="text-slate-400">Concentración Top-{risk.top_n}</Text>
              <Metric className="text-white mt-2">{risk.concentration_pct}%</Metric>
              <Text className="text-slate-500 text-sm mt-1">
                de {risk.total_supplies_edges.toLocaleString()} enlaces SUPPLIES
              </Text>
            </Card>
            <Card className="bg-[#1E212B] border-slate-800 lg:col-span-2">
              <Title className="text-white mb-3">Reparto por proveedor</Title>
              <BarList
                data={(risk.top_suppliers || []).map((s) => ({
                  name: s.name,
                  value: s.share_pct,
                }))}
                color="red"
                valueFormatter={(n: number) => `${n}%`}
              />
            </Card>
          </Grid>
        </section>
      )}

      {/* SECTION 2: DISCREPANCY BY SUPPLIER */}
      {discrepancy.length > 0 && (
        <section className="space-y-4">
          <Flex alignItems="center" className="gap-2">
            <ExclamationTriangleIcon className="w-5 h-5 text-amber-400" />
            <Title className="text-white">Tasa de Discrepancias por Proveedor</Title>
          </Flex>
          <Card className="bg-[#1E212B] border-slate-800">
            <Text className="text-slate-400 mb-4">
              Proveedores ordenados por % de facturas con discrepancia (mín. 5 facturas).
            </Text>
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell className="text-slate-400">Proveedor</TableHeaderCell>
                  <TableHeaderCell className="text-slate-400 text-right">Facturas</TableHeaderCell>
                  <TableHeaderCell className="text-slate-400 text-right">Con error</TableHeaderCell>
                  <TableHeaderCell className="text-slate-400 text-right">Tasa</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {discrepancy.map((row) => (
                  <TableRow key={row.supplier}>
                    <TableCell className="text-white font-medium">{row.supplier}</TableCell>
                    <TableCell className="text-slate-400 text-right">{row.total.toLocaleString()}</TableCell>
                    <TableCell className="text-slate-400 text-right">{row.flagged.toLocaleString()}</TableCell>
                    <TableCell className="text-right">
                      <Badge color={rateBadge(row.discrepancy_rate_pct)}>
                        {row.discrepancy_rate_pct}%
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </section>
      )}

      {/* SECTION 3: LEAD TIME COMPLIANCE */}
      {leadTime.length > 0 && (
        <section className="space-y-4">
          <Flex alignItems="center" className="gap-2">
            <ClockIcon className="w-5 h-5 text-blue-400" />
            <Title className="text-white">Cumplimiento de Lead Time por Categoría</Title>
          </Flex>
          <Card className="bg-[#1E212B] border-slate-800">
            <Text className="text-slate-400 mb-4">
              Retraso medio (días) respecto al baseline del producto. Negativo = adelantado.
            </Text>
            <BarChart
              className="h-72"
              data={leadTime}
              index="category"
              categories={["avg_delay_days"]}
              colors={["blue"]}
              valueFormatter={(n: number) => `${n} d`}
              showLegend={false}
            />
            <div className="mt-4 overflow-auto">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableHeaderCell className="text-slate-400">Categoría</TableHeaderCell>
                    <TableHeaderCell className="text-slate-400 text-right">Retraso medio</TableHeaderCell>
                    <TableHeaderCell className="text-slate-400 text-right">Muestras</TableHeaderCell>
                    <TableHeaderCell className="text-slate-400 text-right">% tardíos</TableHeaderCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {leadTime.map((row) => (
                    <TableRow key={row.category}>
                      <TableCell className="text-white">{row.category}</TableCell>
                      <TableCell className={`text-right font-mono ${row.avg_delay_days > 0 ? "text-red-400" : "text-emerald-400"}`}>
                        {row.avg_delay_days > 0 ? "+" : ""}{row.avg_delay_days} d
                      </TableCell>
                      <TableCell className="text-slate-400 text-right">{row.sample.toLocaleString()}</TableCell>
                      <TableCell className="text-right">
                        <Badge color={row.late_pct >= 60 ? "red" : row.late_pct >= 40 ? "yellow" : "emerald"}>
                          {row.late_pct}%
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </Card>
        </section>
      )}

      {/* SECTION 4: PAYMENT EXPOSURE */}
      {payment.length > 0 && (
        <section className="space-y-4">
          <Flex alignItems="center" className="gap-2">
            <CurrencyEuroIcon className="w-5 h-5 text-emerald-400" />
            <Title className="text-white">Exposición Financiera por Proveedor</Title>
          </Flex>
          <Card className="bg-[#1E212B] border-slate-800">
            <Text className="text-slate-400 mb-4">
              Suma total de importes de facturas emitidas (top-15 por exposición).
            </Text>
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeaderCell className="text-slate-400">Proveedor</TableHeaderCell>
                  <TableHeaderCell className="text-slate-400 text-right">Exposición (€)</TableHeaderCell>
                  <TableHeaderCell className="text-slate-400 text-right">Pago medio (d)</TableHeaderCell>
                  <TableHeaderCell className="text-slate-400 text-right">Nº Facturas</TableHeaderCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {payment.map((row, i) => (
                  <TableRow key={row.supplier}>
                    <TableCell className="text-white font-medium">
                      {i === 0 && <span className="mr-2 text-amber-400">★</span>}
                      {row.supplier}
                    </TableCell>
                    <TableCell className="text-cyan-400 text-right font-mono font-semibold">
                      {Intl.NumberFormat("es", { minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(row.total_exposure_eur)} €
                    </TableCell>
                    <TableCell className="text-slate-400 text-right">{row.avg_payment_days}</TableCell>
                    <TableCell className="text-slate-400 text-right">{row.invoice_count.toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </section>
      )}

      {/* SECTION 5: DATA LINEAGE */}
      {lineage.length > 0 && (
        <section className="space-y-4">
          <Flex alignItems="center" className="gap-2">
            <ExclamationTriangleIcon className="w-5 h-5 text-red-400" />
            <Title className="text-white">Trazabilidad de Discrepancias</Title>
          </Flex>
          <Card className="bg-[#1E212B] border-slate-800">
            <Text className="text-slate-400 mb-4">
              Top-{lineage.length} facturas con discrepancia trazadas hasta su pedido original (ordenadas por riesgo €).
            </Text>
            <div className="overflow-auto">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableHeaderCell className="text-slate-400">Factura</TableHeaderCell>
                    <TableHeaderCell className="text-slate-400 text-right">Riesgo (€)</TableHeaderCell>
                    <TableHeaderCell className="text-slate-400">Proveedor</TableHeaderCell>
                    <TableHeaderCell className="text-slate-400">Afectado</TableHeaderCell>
                    <TableHeaderCell className="text-slate-400 text-right">Saltos</TableHeaderCell>
                    <TableHeaderCell className="text-slate-400 text-right">Productos</TableHeaderCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {lineage.map((row) => (
                    <TableRow key={row.factura_id}>
                      <TableCell className="text-white font-mono text-xs">{row.factura_id}</TableCell>
                      <TableCell className="text-red-400 text-right font-mono font-semibold">
                        {Intl.NumberFormat("es", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(row.riesgo_economico)} €
                      </TableCell>
                      <TableCell className="text-slate-300">{row.proveedor}</TableCell>
                      <TableCell className="text-slate-300">{row.afectado}</TableCell>
                      <TableCell className="text-slate-400 text-right">{row.saltos_topologicos}</TableCell>
                      <TableCell className="text-slate-400 text-right">{row.id_productos_implicados?.length ?? 0}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </Card>
        </section>
      )}

      {/* SECTION 6: GDS */}
      {(gds.bottlenecks.length > 0 || gds.communities.length > 0) && (
        <section className="space-y-4">
          <Title className="text-white">Graph Data Science (GDS)</Title>
          <Grid numItemsSm={1} numItemsLg={2} className="gap-6">
            {gds.bottlenecks.length > 0 && (
              <Card className="bg-[#1E212B] border-slate-800">
                <Title className="text-white mb-1">Cuellos de Botella</Title>
                <Text className="text-slate-400 mb-4">Top-10 por centralidad de intermediación.</Text>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableHeaderCell className="text-slate-400">#</TableHeaderCell>
                      <TableHeaderCell className="text-slate-400">Empresa</TableHeaderCell>
                      <TableHeaderCell className="text-slate-400">Rol</TableHeaderCell>
                      <TableHeaderCell className="text-slate-400 text-right">Score</TableHeaderCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {gds.bottlenecks.map((row, i) => (
                      <TableRow key={row.company_id}>
                        <TableCell className="text-slate-500">{i + 1}</TableCell>
                        <TableCell className="text-white font-medium">{row.legal_name}</TableCell>
                        <TableCell>
                          <Badge color={row.role === "SUPPLIER" ? "cyan" : row.role === "BUYER" ? "violet" : "blue"}>
                            {row.role}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-amber-400 text-right font-mono">
                          {row.betweenness_score.toFixed(4)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Card>
            )}

            {gds.communities.length > 0 && (
              <Card className="bg-[#1E212B] border-slate-800">
                <Title className="text-white mb-1">Comunidades Louvain</Title>
                <Text className="text-slate-400 mb-4">Ecosistemas logísticos detectados.</Text>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableHeaderCell className="text-slate-400">Cluster</TableHeaderCell>
                      <TableHeaderCell className="text-slate-400 text-right">Empresas</TableHeaderCell>
                      <TableHeaderCell className="text-slate-400">Ejemplos</TableHeaderCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {gds.communities.map((row) => (
                      <TableRow key={row.communityId}>
                        <TableCell className="text-cyan-400 font-mono">#{row.communityId}</TableCell>
                        <TableCell className="text-white text-right">{row.total_empresas}</TableCell>
                        <TableCell className="text-slate-400 text-xs">
                          {(row.ejemplos_empresas || []).join(", ")}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Card>
            )}
          </Grid>
        </section>
      )}

    </main>
  );
}
