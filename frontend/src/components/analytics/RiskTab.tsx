"use client";

import { useState } from "react";
import {
  Card, Title, Text, Metric, Grid, Flex,
  DonutChart, CategoryBar, BarList, ProgressBar,
  Table, TableHead, TableHeaderCell, TableBody, TableRow, TableCell,
} from "@tremor/react";
import type { RiskData, SupplierScoreRow, BuyerFragilityRow } from "@/types/analytics";
import { EMPTY, EUR, ShowMoreButton, SectionModal } from "./shared";

const PAGE = 10;

function riskBarColor(score: number): "red" | "yellow" | "emerald" {
  if (score >= 70) return "red";
  if (score >= 40) return "yellow";
  return "emerald";
}

function riskTextColor(score: number): string {
  if (score >= 70) return "text-red-400";
  if (score >= 40) return "text-amber-400";
  return "text-emerald-400";
}

function fragilityBarColor(pct: number): "red" | "yellow" | "emerald" {
  if (pct >= 80) return "red";
  if (pct >= 50) return "yellow";
  return "emerald";
}

function fragilityTextColor(pct: number): string {
  if (pct >= 80) return "text-red-400";
  if (pct >= 50) return "text-amber-400";
  return "text-emerald-400";
}

function SectionLabel({ index, title, subtitle }: { index: string; title: string; subtitle: string }) {
  return (
    <div className="flex items-baseline gap-3 mb-4">
      <span className="text-[var(--primary)] font-mono text-xs opacity-60">{index}</span>
      <div>
        <h3 className="text-white font-semibold text-sm">{title}</h3>
        <p className="text-slate-500 text-xs">{subtitle}</p>
      </div>
    </div>
  );
}

function ScoresTable({ rows }: { rows: SupplierScoreRow[] }) {
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell className="text-slate-400">#</TableHeaderCell>
          <TableHeaderCell className="text-slate-400">Proveedor</TableHeaderCell>
          <TableHeaderCell className="text-slate-400 text-right">Fiabilidad</TableHeaderCell>
          <TableHeaderCell className="text-slate-400 text-right">Discrepancia %</TableHeaderCell>
          <TableHeaderCell className="text-slate-400 text-right">Retraso (d)</TableHeaderCell>
          <TableHeaderCell className="text-slate-400 text-right">Score</TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {rows.map((row, i) => (
          <TableRow key={row.supplier}>
            <TableCell className="text-slate-500 text-xs">{i + 1}</TableCell>
            <TableCell className="text-white">{row.supplier}</TableCell>
            <TableCell className="text-right font-mono text-slate-300">
              {(row.avg_reliability * 100).toFixed(1)}%
            </TableCell>
            <TableCell className="text-right font-mono text-slate-300">
              {row.discrepancy_pct.toFixed(1)}%
            </TableCell>
            <TableCell className="text-right font-mono text-slate-300">
              {row.avg_delay_days.toFixed(1)} d
            </TableCell>
            <TableCell className={`text-right font-mono font-bold ${riskTextColor(row.risk_score)}`}>
              {row.risk_score.toFixed(1)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function FragilityTable({ rows }: { rows: BuyerFragilityRow[] }) {
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell className="text-slate-400">Comprador</TableHeaderCell>
          <TableHeaderCell className="text-slate-400">Región</TableHeaderCell>
          <TableHeaderCell className="text-slate-400 text-right">Proveedores</TableHeaderCell>
          <TableHeaderCell className="text-slate-400 text-right">Dependencia Top %</TableHeaderCell>
          <TableHeaderCell className="text-slate-400 text-right">Volumen Total (€)</TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {rows.map((row) => (
          <TableRow key={row.buyer}>
            <TableCell className="text-white">{row.buyer}</TableCell>
            <TableCell className="text-slate-400">{row.region}</TableCell>
            <TableCell className="text-right font-mono text-slate-300">{row.supplier_count}</TableCell>
            <TableCell className={`text-right font-mono font-semibold ${fragilityTextColor(row.top_supplier_pct)}`}>
              {row.top_supplier_pct.toFixed(1)}%
            </TableCell>
            <TableCell className="text-right font-mono text-slate-300">
              {EUR(row.total_volume_eur, 0)} €
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

interface Props {
  risk:      RiskData | null;
  scores:    SupplierScoreRow[];
  fragility: BuyerFragilityRow[];
}

export function RiskTab({ risk, scores, fragility }: Props) {
  const [showScoresAll,    setShowScoresAll]    = useState(false);
  const [showFragilityAll, setShowFragilityAll] = useState(false);

  const restPct   = risk ? Math.max(0, 100 - risk.concentration_pct) : 0;
  const donutData = risk
    ? [
        { name: `Top-${risk.top_n} proveedores`, value: risk.concentration_pct },
        { name: "Resto de la red",               value: restPct },
      ]
    : [];
  const maxScore = scores.length > 0 ? Math.max(...scores.map((r) => r.risk_score), 1) : 100;

  return (
    <div className="space-y-10">

      {/* ── 01 · CONCENTRACIÓN DE RIESGO ────────────────────────── */}
      <section>
        <SectionLabel
          index="01 /"
          title="Concentración de Riesgo"
          subtitle={`% de enlaces SUPPLIES acaparados por los top-${risk?.top_n ?? 10} proveedores. Un valor alto indica dependencia peligrosa de pocos actores.`}
        />
        {!risk ? EMPTY : (
          <Grid numItemsSm={1} numItemsLg={3} className="gap-6">
            <Card decoration="top" decorationColor="red" className="bg-[#1E212B] border-slate-800 flex flex-col justify-between">
              <Text className="text-slate-400">Concentración Top-{risk.top_n}</Text>
              <Metric className="text-white mt-2">{risk.concentration_pct}%</Metric>
              <Text className="text-slate-500 text-sm mt-1">
                de {risk.total_supplies_edges.toLocaleString()} enlaces SUPPLIES
              </Text>
              <div className="mt-4">
                <CategoryBar
                  values={[risk.concentration_pct, restPct]}
                  colors={["red", "slate"]}
                  className="mt-2"
                />
                <Flex className="mt-1">
                  <Text className="text-red-400 text-xs">Top-{risk.top_n}</Text>
                  <Text className="text-slate-500 text-xs">Resto</Text>
                </Flex>
              </div>
            </Card>

            <Card className="bg-[#1E212B] border-slate-800 flex flex-col items-center justify-center">
              <Title className="text-white mb-2">Distribución de red</Title>
              <DonutChart
                data={donutData}
                category="value"
                index="name"
                colors={["red", "slate"]}
                valueFormatter={(n) => `${n.toFixed(1)}%`}
                className="h-40"
              />
            </Card>

            <Card className="bg-[#1E212B] border-slate-800">
              <Title className="text-white mb-3">Cuota individual por proveedor</Title>
              <BarList
                data={(risk.top_suppliers ?? []).map((s) => ({
                  name: s.name,
                  value: s.share_pct,
                }))}
                color="red"
                valueFormatter={(n: number) => `${n}%`}
              />
            </Card>
          </Grid>
        )}
      </section>

      {/* ── 02 · ÍNDICE DE RIESGO DE PROVEEDOR ──────────────────── */}
      {scores.length > 0 && (
        <section>
          <SectionLabel
            index="02 /"
            title="Índice de Riesgo de Proveedor"
            subtitle="Score 0–100 combinando fiabilidad (40 %), discrepancias (35 %) y retraso de entrega (25 %). Mayor score = mayor riesgo."
          />
          <Card className="bg-[#1E212B] border-slate-800">
            <div className="space-y-3 mb-4">
              {scores.slice(0, PAGE).map((row, i) => (
                <div key={row.supplier}>
                  <Flex className="mb-1">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-slate-500 text-xs w-5 shrink-0">{i + 1}</span>
                      <span className="text-white text-sm truncate">{row.supplier}</span>
                      <span className="text-slate-600 text-xs shrink-0">({row.supply_degree} links)</span>
                    </div>
                    <span className={`font-mono font-bold text-sm shrink-0 ${riskTextColor(row.risk_score)}`}>
                      {row.risk_score.toFixed(1)}
                    </span>
                  </Flex>
                  <ProgressBar
                    value={(row.risk_score / maxScore) * 100}
                    color={riskBarColor(row.risk_score)}
                    className="h-1.5"
                  />
                </div>
              ))}
            </div>
            {scores.length > PAGE && (
              <ShowMoreButton total={scores.length} onClick={() => setShowScoresAll(true)} />
            )}
          </Card>
        </section>
      )}

      {/* ── 03 · FRAGILIDAD DEL COMPRADOR ───────────────────────── */}
      {fragility.length > 0 && (
        <section>
          <SectionLabel
            index="03 /"
            title="Fragilidad del Comprador"
            subtitle="% del volumen total de compra controlado por un único proveedor. Valores altos indican dependencia crítica."
          />
          <Card className="bg-[#1E212B] border-slate-800">
            <div className="space-y-3 mb-4">
              {fragility.slice(0, PAGE).map((row, i) => (
                <div key={row.buyer}>
                  <Flex className="mb-1">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-slate-500 text-xs w-5 shrink-0">{i + 1}</span>
                      <span className="text-white text-sm truncate">{row.buyer}</span>
                      <span className="text-slate-500 text-xs shrink-0">{row.region}</span>
                      <span className="text-slate-600 text-xs shrink-0">({row.supplier_count} provs.)</span>
                    </div>
                    <span className={`font-mono text-sm shrink-0 ${fragilityTextColor(row.top_supplier_pct)}`}>
                      {row.top_supplier_pct.toFixed(1)}%
                    </span>
                  </Flex>
                  <ProgressBar
                    value={row.top_supplier_pct}
                    color={fragilityBarColor(row.top_supplier_pct)}
                    className="h-1.5"
                  />
                </div>
              ))}
            </div>
            {fragility.length > PAGE && (
              <ShowMoreButton total={fragility.length} onClick={() => setShowFragilityAll(true)} />
            )}
          </Card>
        </section>
      )}

      {/* ── MODALS ──────────────────────────────────────────────── */}
      <SectionModal
        title="Índice de Riesgo — todos los proveedores"
        open={showScoresAll}
        onClose={() => setShowScoresAll(false)}
      >
        <ScoresTable rows={scores} />
      </SectionModal>

      <SectionModal
        title="Fragilidad del Comprador — completo"
        open={showFragilityAll}
        onClose={() => setShowFragilityAll(false)}
      >
        <FragilityTable rows={fragility} />
      </SectionModal>

    </div>
  );
}