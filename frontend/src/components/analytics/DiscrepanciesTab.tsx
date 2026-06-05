"use client";

import { useState } from "react";
import {
  Card, Title, Text, Metric, Grid,
  BarChart,
  Table, TableHead, TableHeaderCell, TableBody, TableRow, TableCell,
  Badge,
} from "@tremor/react";
import type { DiscrepancyRow, CommercialImpactRow } from "@/types/analytics";
import { EMPTY, EUR, SIGN, rateBadge, EstadoPill, ShowMoreButton, SectionModal } from "./shared";

const PAGE = 10;

function CommercialTable({ rows }: { rows: CommercialImpactRow[] }) {
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell className="text-slate-400">Pedido</TableHeaderCell>
          <TableHeaderCell className="text-slate-400">Proveedor</TableHeaderCell>
          <TableHeaderCell className="text-slate-400 text-right">Pedido (€)</TableHeaderCell>
          <TableHeaderCell className="text-slate-400 text-right">Facturado (€)</TableHeaderCell>
          <TableHeaderCell className="text-slate-400 text-right">Δ €</TableHeaderCell>
          <TableHeaderCell className="text-slate-400 text-right">Δ %</TableHeaderCell>
          <TableHeaderCell className="text-slate-400 text-right">Estado</TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {rows.map((row) => (
          <TableRow key={row.pedido_id}>
            <TableCell className="text-slate-400 font-mono text-xs">{row.pedido_id}</TableCell>
            <TableCell className="text-white text-sm">{row.proveedor}</TableCell>
            <TableCell className="text-slate-300 text-right font-mono">{EUR(row.importe_pedido_eur, 2)}</TableCell>
            <TableCell className="text-slate-300 text-right font-mono">{EUR(row.total_facturado_eur, 2)}</TableCell>
            <TableCell className={`text-right font-mono font-semibold ${row.delta_eur > 0 ? "text-red-400" : row.delta_eur < 0 ? "text-amber-400" : "text-slate-400"}`}>
              {SIGN(row.delta_eur)}{EUR(row.delta_eur, 2)}
            </TableCell>
            <TableCell className={`text-right font-mono text-sm ${row.delta_pct != null && row.delta_pct > 0 ? "text-red-400" : row.delta_pct != null && row.delta_pct < 0 ? "text-amber-400" : "text-slate-400"}`}>
              {row.delta_pct != null ? `${SIGN(row.delta_pct)}${row.delta_pct}%` : "—"}
            </TableCell>
            <TableCell className="text-right"><EstadoPill estado={row.estado_comercial} /></TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

interface Props {
  discrepancy: DiscrepancyRow[];
  commercial:  CommercialImpactRow[];
}

export function DiscrepanciesTab({ discrepancy, commercial }: Props) {
  const [showCommercialAll, setShowCommercialAll] = useState(false);

  const cmSobre = commercial.filter((r) => r.estado_comercial === "SOBREFACTURADO").length;
  const cmSub   = commercial.filter((r) => r.estado_comercial === "SUBFACTURADO").length;
  const cmOk    = commercial.filter((r) => r.estado_comercial === "CONFORME").length;

  if (discrepancy.length === 0 && commercial.length === 0) return EMPTY;

  return (
    <div className="space-y-10">

      {/* ── 01 · TASA DE DISCREPANCIA POR PROVEEDOR ─────────────── */}
      {discrepancy.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-white mb-1">Tasa de Discrepancia por Proveedor</h2>
          <p className="text-slate-400 text-sm mb-4">Top-20, mínimo 5 facturas emitidas.</p>
          <div className="space-y-6">
            <Card className="bg-[#1E212B] border-slate-800">
              <BarChart
                className="h-64"
                data={[...discrepancy].reverse()}
                index="supplier"
                categories={["discrepancy_rate_pct"]}
                colors={["red"]}
                layout="vertical"
                valueFormatter={(n) => `${n}%`}
                showLegend={false}
              />
            </Card>

            <Card className="bg-[#1E212B] border-slate-800">
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
          </div>
        </section>
      )}

      {/* ── 02 · IMPACTO COMERCIAL ───────────────────────────────── */}
      {commercial.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-white mb-1">Impacto Comercial</h2>
          <p className="text-slate-400 text-sm mb-4">
            Desviación entre importe del pedido y total facturado. Tolerancia ±5%.
          </p>
          <div className="space-y-4">
            <Grid numItemsSm={3} className="gap-4">
              <Card className="bg-red-950/40 border-red-800 text-center">
                <Text className="text-red-400 text-sm">Sobrefacturados</Text>
                <Metric className="text-red-300 mt-1">{cmSobre}</Metric>
              </Card>
              <Card className="bg-amber-950/40 border-amber-800 text-center">
                <Text className="text-amber-400 text-sm">Subfacturados</Text>
                <Metric className="text-amber-300 mt-1">{cmSub}</Metric>
              </Card>
              <Card className="bg-emerald-950/40 border-emerald-800 text-center">
                <Text className="text-emerald-400 text-sm">Conformes</Text>
                <Metric className="text-emerald-300 mt-1">{cmOk}</Metric>
              </Card>
            </Grid>
            <Card className="bg-[#1E212B] border-slate-800">
              <div className="overflow-auto">
                <CommercialTable rows={commercial.slice(0, PAGE)} />
              </div>
              {commercial.length > PAGE && (
                <ShowMoreButton total={commercial.length} onClick={() => setShowCommercialAll(true)} />
              )}
            </Card>
          </div>
        </section>
      )}

      <SectionModal
        title="Impacto Comercial — completo"
        open={showCommercialAll}
        onClose={() => setShowCommercialAll(false)}
      >
        <CommercialTable rows={commercial} />
      </SectionModal>

    </div>
  );
}
