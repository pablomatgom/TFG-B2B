"use client";

import { useState, useEffect } from "react";
import {
  Card, Title, Text, Metric, Grid, Flex, Badge,
  BarChart, BarList,
  Table, TableHead, TableHeaderCell, TableBody, TableRow, TableCell,
  Tab, TabGroup, TabList, TabPanel, TabPanels,
} from "@tremor/react";
import {
  ExclamationTriangleIcon,
  ShieldExclamationIcon,
  ClockIcon,
  CurrencyEuroIcon,
  LinkIcon,
  CpuChipIcon,
} from "@heroicons/react/24/outline";
import { API_BASE } from "@/lib/api";
import { LoadingState } from "@/components/ui/LoadingState";
import type {
  RiskData, DiscrepancyRow, LeadTimeRow,
  PaymentRow, LineageRow, GdsData,
} from "@/types/analytics";

function rateBadge(rate: number): "red" | "yellow" | "emerald" {
  if (rate >= 20) return "red";
  if (rate >= 10) return "yellow";
  return "emerald";
}

const EUR = (n: number, dec = 0) =>
  Intl.NumberFormat("es", { minimumFractionDigits: dec, maximumFractionDigits: dec }).format(n);

const EMPTY = (
  <Text className="text-slate-500 py-8 text-center">
    Sin datos — ejecuta el pipeline desde{" "}
    <a href="/pipeline" className="text-cyan-400 underline">Pipeline</a>.
  </Text>
);

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
      fetch(`${API_BASE}/api/dashboard/risk`).then((r) => r.json()),
      fetch(`${API_BASE}/api/dashboard/discrepancy-suppliers`).then((r) => r.json()),
      fetch(`${API_BASE}/api/dashboard/lead-time`).then((r) => r.json()),
      fetch(`${API_BASE}/api/dashboard/payment`).then((r) => r.json()),
      fetch(`${API_BASE}/api/dashboard/lineage`).then((r) => r.json()),
      fetch(`${API_BASE}/api/dashboard/gds`).then((r) => r.json()),
    ])
      .then(([riskData, discData, ltData, payData, linData, gdsData]) => {
        setRisk(riskData?.total_supplies_edges ? riskData : null);
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
    return <LoadingState text="Cargando analítica avanzada..." />;
  }

  return (
    <main className="p-6 md:p-10 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500">

      <div>
        <Title className="text-3xl font-bold text-white">Analítica Avanzada de Red</Title>
        <Text className="text-slate-400">
          Riesgo de concentración, calidad documental, cumplimiento operativo y exposición financiera.
        </Text>
      </div>

      <TabGroup>
        <TabList className="border-b border-slate-800 mb-6">
          <Tab icon={ShieldExclamationIcon}>Riesgo</Tab>
          <Tab icon={ExclamationTriangleIcon}>Discrepancias</Tab>
          <Tab icon={ClockIcon}>Lead Time</Tab>
          <Tab icon={CurrencyEuroIcon}>Exposición</Tab>
          <Tab icon={LinkIcon}>Trazabilidad</Tab>
          <Tab icon={CpuChipIcon}>GDS</Tab>
        </TabList>

        <TabPanels>

          {/* TAB 1 — RISK CONCENTRATION */}
          <TabPanel>
            {!risk ? EMPTY : (
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
                    data={(risk.top_suppliers ?? []).map((s) => ({
                      name: s.name,
                      value: s.share_pct,
                    }))}
                    color="red"
                    valueFormatter={(n) => `${n}%`}
                  />
                </Card>
              </Grid>
            )}
          </TabPanel>

          {/* TAB 2 — DISCREPANCY BY SUPPLIER */}
          <TabPanel>
            {discrepancy.length === 0 ? EMPTY : (
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
            )}
          </TabPanel>

          {/* TAB 3 — LEAD TIME */}
          <TabPanel>
            {leadTime.length === 0 ? EMPTY : (
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
                  valueFormatter={(n) => `${n} d`}
                  showLegend={false}
                />
                <div className="mt-6 overflow-auto">
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
            )}
          </TabPanel>

          {/* TAB 4 — PAYMENT EXPOSURE */}
          <TabPanel>
            {payment.length === 0 ? EMPTY : (
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
                          {EUR(row.total_exposure_eur)} €
                        </TableCell>
                        <TableCell className="text-slate-400 text-right">{row.avg_payment_days}</TableCell>
                        <TableCell className="text-slate-400 text-right">{row.invoice_count.toLocaleString()}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Card>
            )}
          </TabPanel>

          {/* TAB 5 — DATA LINEAGE */}
          <TabPanel>
            {lineage.length === 0 ? EMPTY : (
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
                            {EUR(row.riesgo_economico, 2)} €
                          </TableCell>
                          <TableCell className="text-slate-300">{row.proveedor}</TableCell>
                          <TableCell className="text-slate-300">{row.afectado}</TableCell>
                          <TableCell className="text-slate-400 text-right">{row.saltos_topologicos}</TableCell>
                          <TableCell className="text-slate-400 text-right">
                            {row.id_productos_implicados?.length ?? 0}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </Card>
            )}
          </TabPanel>

          {/* TAB 6 — GDS */}
          <TabPanel>
            {gds.bottlenecks.length === 0 && gds.communities.length === 0 ? (
              <Card className="bg-[#1E212B] border-slate-800 text-center py-12">
                <Text className="text-slate-500">
                  GDS no ha sido ejecutado. Descomenta las llamadas en{" "}
                  <code className="text-cyan-400">run_analyze.py</code> y re-ejecuta el pipeline.
                </Text>
              </Card>
            ) : (
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
                              {(row.ejemplos_empresas ?? []).join(", ")}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </Card>
                )}
              </Grid>
            )}
          </TabPanel>

        </TabPanels>
      </TabGroup>

    </main>
  );
}