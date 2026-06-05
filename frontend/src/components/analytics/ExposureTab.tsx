"use client";

import { useState } from "react";
import {
  Card, Title, Text, BarChart,
  Table, TableHead, TableHeaderCell, TableBody, TableRow, TableCell,
} from "@tremor/react";
import type { PaymentRow, OverdueRow } from "@/types/analytics";
import { EMPTY, EUR, ShowMoreButton, SectionModal } from "./shared";

const PAGE = 10;

function OverdueTable({ rows }: { rows: OverdueRow[] }) {
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableHeaderCell className="text-slate-400">Proveedor</TableHeaderCell>
          <TableHeaderCell className="text-slate-400">Comprador</TableHeaderCell>
          <TableHeaderCell className="text-slate-400 text-right">Facturas</TableHeaderCell>
          <TableHeaderCell className="text-slate-400 text-right">Importe Vencido (€)</TableHeaderCell>
          <TableHeaderCell className="text-slate-400 text-right">Plazo Medio (d)</TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {rows.map((row, i) => (
          <TableRow key={`${row.supplier}-${row.buyer}-${i}`}>
            <TableCell className="text-white">{row.supplier}</TableCell>
            <TableCell className="text-slate-400">{row.buyer}</TableCell>
            <TableCell className="text-right font-mono text-slate-300">{row.overdue_invoices}</TableCell>
            <TableCell className="text-right font-mono text-red-400 font-semibold">
              {EUR(row.total_overdue_eur, 2)} €
            </TableCell>
            <TableCell className="text-right font-mono text-slate-300">
              {row.avg_payment_days.toFixed(0)} d
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

interface Props {
  payment: PaymentRow[];
  overdue: OverdueRow[];
}

export function ExposureTab({ payment, overdue }: Props) {
  const [showOverdueAll, setShowOverdueAll] = useState(false);

  if (payment.length === 0 && overdue.length === 0) return EMPTY;

  return (
    <div className="space-y-10">

      {/* ── 01 · EXPOSICIÓN FINANCIERA POR PROVEEDOR ────────────── */}
      {payment.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-white mb-1">Exposición Financiera por Proveedor</h2>
          <p className="text-slate-400 text-sm mb-4">Suma total de importes de facturas emitidas (top-15).</p>
          <div className="space-y-6">
            <Card className="bg-[#1E212B] border-slate-800">
              <BarChart
                className="h-64"
                data={[...payment].reverse()}
                index="supplier"
                categories={["total_exposure_eur"]}
                colors={["violet"]}
                layout="vertical"
                valueFormatter={(n) => `${EUR(n)} €`}
                showLegend={false}
              />
            </Card>

            <Card className="bg-[#1E212B] border-slate-800">
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
                      <TableCell className="text-[var(--primary)] text-right font-mono font-semibold">
                        {EUR(row.total_exposure_eur)} €
                      </TableCell>
                      <TableCell className="text-slate-400 text-right">{row.avg_payment_days}</TableCell>
                      <TableCell className="text-slate-400 text-right">{row.invoice_count.toLocaleString()}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          </div>
        </section>
      )}

      {/* ── 02 · EXPOSICIÓN POR FACTURAS VENCIDAS ───────────────── */}
      <section>
        <h2 className="text-lg font-semibold text-white mb-1">Exposición por Facturas Vencidas</h2>
        <p className="text-slate-400 text-sm mb-4">
          Facturas en estado OVERDUE por par proveedor-comprador, ordenadas por importe vencido.
        </p>
        {overdue.length === 0 ? (
          <Card className="bg-[#1E212B] border-slate-800 text-center py-8">
            <Text className="text-emerald-400">
              Sin facturas vencidas — la red está al corriente de pago.
            </Text>
          </Card>
        ) : (
          <Card className="bg-[#1E212B] border-slate-800">
            <div className="overflow-auto">
              <OverdueTable rows={overdue.slice(0, PAGE)} />
            </div>
            {overdue.length > PAGE && (
              <ShowMoreButton total={overdue.length} onClick={() => setShowOverdueAll(true)} />
            )}
          </Card>
        )}
      </section>

      <SectionModal
        title="Facturas Vencidas — completo"
        open={showOverdueAll}
        onClose={() => setShowOverdueAll(false)}
      >
        <OverdueTable rows={overdue} />
      </SectionModal>

    </div>
  );
}