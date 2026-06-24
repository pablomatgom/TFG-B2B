"use client";

import { useState } from "react";
import { EyeIcon } from "@heroicons/react/24/outline";
import BarChart from "@/components/charts/BarChart";
import type { PaymentRow, OverdueRow, SupplierInvoiceRow } from "@/types/analytics";
import { paymentDaysBadge, PAGE_SIZE, EUR } from "@/lib/analytics";
import { EMPTY, ShowMoreButton, SectionModal, SectionLabel, KpiStrip, ProgressBar, InfoTooltip } from "./shared";
import { API_BASE } from "@/lib/api";

const STATUS_BADGE: Record<string, string> = {
  PAID:    "bg-emerald-50 text-emerald-700 border-emerald-200",
  PENDING: "bg-indigo-50  text-indigo-700  border-indigo-200",
  PARTIAL: "bg-amber-50   text-amber-700   border-amber-200",
  OVERDUE: "bg-red-50     text-red-700     border-red-200",
};

function SupplierInvoicesTable({ rows }: { rows: SupplierInvoiceRow[] }) {
  if (rows.length === 0) return (
    <p className="text-center text-gray-400 text-sm py-10">Sin facturas disponibles.</p>
  );
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="bg-gray-50 border-b border-gray-100">
          {(["Documento", "Comprador", "Importe (€)", "Estado", "Plazo (d)", "Vencimiento", "Emisión", "Discrepancia"] as const).map((h, i) => (
            <th key={h} className={`px-4 py-3 text-[11px] font-semibold uppercase tracking-wide text-gray-400 ${i >= 2 ? "text-right" : "text-left"}`}>
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {rows.map((row) => (
          <tr key={row.document_id} className="hover:bg-gray-50 transition-colors">
            <td className="px-4 py-3 font-mono text-xs text-gray-600">{row.document_id}</td>
            <td className="px-4 py-3 text-gray-900 font-medium max-w-[160px] truncate">{row.buyer}</td>
            <td className="px-4 py-3 text-right font-mono font-semibold text-gray-700 tabular-nums">
              {EUR(row.gross_amount, 2)} €
            </td>
            <td className="px-4 py-3 text-right">
              <span className={`inline-flex justify-center px-2 py-0.5 rounded border text-xs font-semibold ${STATUS_BADGE[row.status] ?? "bg-gray-50 text-gray-500 border-gray-200"}`}>
                {row.status}
              </span>
            </td>
            <td className="px-4 py-3 text-right font-mono text-gray-600 tabular-nums">
              {row.payment_terms_days} d
            </td>
            <td className="px-4 py-3 text-right text-xs text-gray-500 tabular-nums">
              {row.due_date ?? "—"}
            </td>
            <td className="px-4 py-3 text-right text-xs text-gray-500 tabular-nums">
              {row.issue_date ?? "—"}
            </td>
            <td className="px-4 py-3 text-right">
              {row.discrepancy_flag ? (
                <span className="inline-flex justify-center px-2 py-0.5 rounded border text-xs font-semibold bg-red-50 text-red-700 border-red-200">Sí</span>
              ) : (
                <span className="inline-flex justify-center px-2 py-0.5 rounded border text-xs font-semibold bg-gray-50 text-gray-400 border-gray-200">No</span>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function OverdueTable({ rows, onViewInvoices }: { rows: OverdueRow[]; onViewInvoices?: (supplier: string, buyer: string) => void }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="bg-gray-50 border-b border-gray-100">
          {([
            { label: "Proveedor" },
            { label: "Comprador" },
            { label: "Facturas" },
            { label: "Importe Vencido (€)" },
            { label: "Plazo Medio", tooltip: "Plazo de pago medio escrito en las facturas vencidas, comparado con el plazo acordado en el contrato SUPPLIES. Verde = el comprador incumplió dentro del plazo acordado (breach claro) · Ámbar = el proveedor dio hasta +10% extra, el comprador igualmente no pagó · Rojo = el proveedor fue significativamente más generoso que el contrato y aun así no se cobró." },
            { label: "" },
          ] as { label: string; tooltip?: string }[]).map(({ label, tooltip }, i) => (
            <th
              key={label + i}
              className={`px-4 py-3 text-[11px] font-semibold uppercase tracking-wide text-gray-400 ${i > 1 && i < 5 ? "text-right" : "text-left"}`}
            >
              <span className={`inline-flex items-center gap-0.5 ${i > 1 && i < 5 ? "justify-end w-full" : ""}`}>
                {label}
                {tooltip && <InfoTooltip content={tooltip} direction="down" align={i > 1 ? "end" : "center"} />}
              </span>
            </th>
          ))}
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {rows.map((row, i) => (
          <tr key={`${row.supplier}-${row.buyer}-${i}`} className="hover:bg-gray-50 transition-colors">
            <td className="px-4 py-3 text-gray-900 font-medium max-w-[160px] truncate">{row.supplier}</td>
            <td className="px-4 py-3 text-gray-500 text-xs max-w-[160px] truncate">{row.buyer}</td>
            <td className="px-4 py-3 text-right font-mono text-gray-600 tabular-nums">{row.overdue_invoices}</td>
            <td className="px-4 py-3 text-right font-mono font-semibold text-red-600 tabular-nums">
              {EUR(row.total_overdue_eur, 2)} €
            </td>
            <td className="px-4 py-3 text-right">
              <span className={`inline-flex justify-center px-2 py-0.5 rounded-full text-xs font-mono font-semibold min-w-[3.5rem] ${paymentDaysBadge(row.avg_payment_days, row.avg_agreed_days)}`}>
                {row.avg_payment_days.toFixed(0)} d
              </span>
            </td>
            <td className="px-4 py-3 text-right">
              {onViewInvoices && (
                <button
                  onClick={() => onViewInvoices(row.supplier, row.buyer)}
                  title="Ver facturas vencidas"
                  className="p-1.5 rounded-lg text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
                >
                  <EyeIcon className="w-4 h-4" />
                </button>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

interface Props {
  payment: PaymentRow[];
  overdue: OverdueRow[];
}

export function ExposureTab({ payment, overdue }: Props) {
  const [showOverdueAll,   setShowOverdueAll]   = useState(false);
  const [showPaymentAll,   setShowPaymentAll]   = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState<string | null>(null);
  const [supplierInvoices, setSupplierInvoices] = useState<SupplierInvoiceRow[]>([]);
  const [loadingInvoices,  setLoadingInvoices]  = useState(false);

  const [overduePair,         setOverduePair]         = useState<{ supplier: string; buyer: string } | null>(null);
  const [overduePairInvoices, setOverduePairInvoices] = useState<SupplierInvoiceRow[]>([]);
  const [loadingOverdue,      setLoadingOverdue]      = useState(false);

  async function openSupplierInvoices(supplier: string) {
    setSelectedSupplier(supplier);
    setSupplierInvoices([]);
    setLoadingInvoices(true);
    try {
      const res = await fetch(`${API_BASE}/api/analytics/risk/supplier-invoices?supplier=${encodeURIComponent(supplier)}`);
      if (res.ok) setSupplierInvoices(await res.json());
    } finally {
      setLoadingInvoices(false);
    }
  }

  async function openOverduePairInvoices(supplier: string, buyer: string) {
    setOverduePair({ supplier, buyer });
    setOverduePairInvoices([]);
    setLoadingOverdue(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/analytics/risk/supplier-pair-overdue?supplier=${encodeURIComponent(supplier)}&buyer=${encodeURIComponent(buyer)}`
      );
      if (res.ok) setOverduePairInvoices(await res.json());
    } finally {
      setLoadingOverdue(false);
    }
  }

  if (payment.length === 0 && overdue.length === 0) return EMPTY;

  const totalExposure  = payment.reduce((s, r) => s + r.total_exposure_eur, 0);
  const avgPaymentDays = payment.length > 0
    ? payment.reduce((s, r) => s + r.avg_payment_days, 0) / payment.length
    : 0;
  const totalInvoices  = payment.reduce((s, r) => s + r.invoice_count, 0);
  const totalOverdue   = overdue.reduce((s, r) => s + r.total_overdue_eur, 0);
  const overduePct     = totalExposure > 0 ? (totalOverdue / totalExposure) * 100 : 0;
  const paymentChartData = payment.slice(0, 20);

  return (
    <div className="space-y-10">

      {/* ── 01 · EXPOSICIÓN FINANCIERA POR PROVEEDOR ────────────── */}
      {payment.length > 0 && (
        <section>
          <SectionLabel
            index="01 /"
            title="Exposición Financiera por Proveedor"
            subtitle="Volumen total de facturas emitidas agrupado por proveedor. Identifica qué proveedores concentran mayor carga financiera en la red y dónde se acumula el riesgo de impago en caso de incumplimiento."
          />
          <div className="space-y-4">

            <KpiStrip className="mb-0" items={[
              { label: "Exposición total",    value: `${EUR(totalExposure, 0)} €`          },
              { label: "Pago medio global",   value: `${avgPaymentDays.toFixed(0)} d`       },
              { label: "Facturas analizadas", value: totalInvoices.toLocaleString("es-ES") },
            ]} />

            {/* Bar chart with Top N selector */}
            <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
              <div className="px-5 pt-4 pb-3 border-b border-gray-100">
                <p className="text-gray-700 font-semibold text-sm">Exposición por proveedor</p>
              </div>
              <div className="p-5">
                <BarChart
                  data={paymentChartData}
                  index="supplier"
                  category="total_exposure_eur"
                  layout="vertical"
                  yAxisWidth={160}
                  rowHeight={24}
                  valueFormatter={(n) => `${EUR(n, 0)} €`}
                  color="#8b5cf6"
                />
              </div>
            </div>

            {/* Payment table — paginated */}
            <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-100">
                    {([
                      { label: "#" },
                      { label: "Proveedor" },
                      { label: "Exposición (€)" },
                      { label: "% del total" },
                      { label: "Pago medio (d)", tooltip: "Media de payment_terms_days en las facturas emitidas, comparada con el plazo acordado contractualmente (SUPPLIES). Verde = respeta el contrato · Ámbar = hasta +10% · Rojo = supera el contrato." },
                      { label: "Nº Facturas" },
                      { label: "" },
                    ] as { label: string; tooltip?: string }[]).map(({ label, tooltip }, i) => (
                      <th
                        key={label + i}
                        className={`px-4 py-3 text-[11px] font-semibold uppercase tracking-wide text-gray-400 ${i > 1 && i < 5 ? "text-right" : "text-left"}`}
                      >
                        <span className={`inline-flex items-center gap-0.5 ${i > 1 && i < 5 ? "justify-end w-full" : ""}`}>
                          {label}
                          {tooltip && <InfoTooltip content={tooltip} direction="down" align={i > 1 ? "end" : "center"} />}
                        </span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {payment.slice(0, PAGE_SIZE).map((row, i) => (
                    <tr key={row.supplier} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 text-gray-400 text-xs tabular-nums w-8">{i + 1}</td>
                      <td className="px-4 py-3 text-gray-900 font-medium max-w-[200px] truncate">
                        {row.supplier}
                      </td>
                      <td className="px-4 py-3 text-right font-mono font-semibold text-gray-600 tabular-nums">
                        {EUR(row.total_exposure_eur, 0)} €
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <ProgressBar
                            pct={totalExposure > 0 ? (row.total_exposure_eur / totalExposure) * 100 : 0}
                            width="w-14"
                          />
                          <span className="font-mono text-xs text-gray-500 tabular-nums w-10 text-right">
                            {totalExposure > 0 ? ((row.total_exposure_eur / totalExposure) * 100).toFixed(1) : "0.0"}%
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className={`inline-flex justify-center px-2 py-0.5 rounded-full text-xs font-mono font-semibold min-w-[3.5rem] ${paymentDaysBadge(row.avg_payment_days, row.avg_agreed_days)}`}>
                          {row.avg_payment_days} d
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-gray-600 tabular-nums">
                        {row.invoice_count.toLocaleString("es-ES")}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => openSupplierInvoices(row.supplier)}
                          title="Ver facturas individuales"
                          className="p-1.5 rounded-lg text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
                        >
                          <EyeIcon className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {payment.length > PAGE_SIZE && (
                <div className="px-5 py-3 border-t border-gray-100 bg-gray-50">
                  <ShowMoreButton total={payment.length} onClick={() => setShowPaymentAll(true)} />
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* ── 02 · EXPOSICIÓN POR FACTURAS VENCIDAS ───────────────── */}
      <section>
        <SectionLabel
          index="02 /"
          title="Exposición por Facturas Vencidas"
          subtitle="Facturas impagadas una vez superada su fecha de vencimiento, desglosadas por par proveedor-comprador y ordenadas por importe. Un volumen elevado indica riesgo de liquidez activo en la red."
        />
        {overdue.length === 0 ? (
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-6 text-center">
            <p className="text-emerald-700 text-sm font-semibold">Sin facturas vencidas</p>
            <p className="text-emerald-500 text-xs mt-1">La red está al corriente de pago.</p>
          </div>
        ) : (
          <>
            <KpiStrip items={[
              { label: "Importe total vencido",    value: `${EUR(totalOverdue, 0)} €`                             },
              { label: "Pares con deuda vencida",  value: overdue.length.toString()                               },
              { label: "% sobre exposición total", value: totalExposure > 0 ? `${overduePct.toFixed(1)}%` : "—"  },
            ]} />

            <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
              <OverdueTable rows={overdue.slice(0, PAGE_SIZE)} onViewInvoices={openOverduePairInvoices} />
              {overdue.length > PAGE_SIZE && (
                <div className="px-5 pb-4">
                  <ShowMoreButton total={overdue.length} onClick={() => setShowOverdueAll(true)} />
                </div>
              )}
            </div>
          </>
        )}
      </section>

      <SectionModal
        title={`Exposición Financiera — ${payment.length} proveedores`}
        open={showPaymentAll}
        onClose={() => setShowPaymentAll(false)}
      >
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-100">
              {([
                { label: "#" },
                { label: "Proveedor" },
                { label: "Exposición (€)" },
                { label: "% del total" },
                { label: "Pago medio (d)", tooltip: "Media de payment_terms_days en las facturas emitidas, comparada con el plazo acordado contractualmente (SUPPLIES). Verde = respeta el contrato · Ámbar = hasta +10% · Rojo = supera el contrato." },
                { label: "Nº Facturas" },
                { label: "" },
              ] as { label: string; tooltip?: string }[]).map(({ label, tooltip }, i) => (
                <th key={label + i} className={`px-4 py-3 text-[11px] font-semibold uppercase tracking-wide text-gray-400 ${i > 1 && i < 5 ? "text-right" : "text-left"}`}>
                  <span className={`inline-flex items-center gap-0.5 ${i > 1 && i < 5 ? "justify-end w-full" : ""}`}>
                    {label}
                    {tooltip && <InfoTooltip content={tooltip} direction="down" align={i > 1 ? "end" : "center"} />}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {payment.map((row, i) => (
              <tr key={row.supplier} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-gray-400 text-xs tabular-nums w-8">{i + 1}</td>
                <td className="px-4 py-3 text-gray-900 font-medium max-w-[200px] truncate">{row.supplier}</td>
                <td className="px-4 py-3 text-right font-mono font-semibold text-indigo-600 tabular-nums">{EUR(row.total_exposure_eur, 0)} €</td>
                <td className="px-4 py-3 text-right font-mono text-xs text-gray-500 tabular-nums">
                  {totalExposure > 0 ? ((row.total_exposure_eur / totalExposure) * 100).toFixed(1) : "0.0"}%
                </td>
                <td className="px-4 py-3 text-right">
                  <span className={`inline-flex justify-center px-2 py-0.5 rounded-full text-xs font-mono font-semibold min-w-[3.5rem] ${paymentDaysBadge(row.avg_payment_days, row.avg_agreed_days)}`}>
                    {row.avg_payment_days} d
                  </span>
                </td>
                <td className="px-4 py-3 text-right font-mono text-gray-600 tabular-nums">{row.invoice_count.toLocaleString("es-ES")}</td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => openSupplierInvoices(row.supplier)}
                    title="Ver facturas individuales"
                    className="p-1.5 rounded-lg text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
                  >
                    <EyeIcon className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </SectionModal>

      <SectionModal
        title="Facturas Vencidas — completo"
        open={showOverdueAll}
        onClose={() => setShowOverdueAll(false)}
      >
        <OverdueTable rows={overdue} onViewInvoices={openOverduePairInvoices} />
      </SectionModal>

      <SectionModal
        title={selectedSupplier ? `Facturas de ${selectedSupplier}` : ""}
        open={selectedSupplier !== null}
        onClose={() => setSelectedSupplier(null)}
      >
        {loadingInvoices ? (
          <p className="text-center text-gray-400 text-sm py-10">Cargando facturas...</p>
        ) : (
          <SupplierInvoicesTable rows={supplierInvoices} />
        )}
      </SectionModal>

      <SectionModal
        title={overduePair ? `Facturas vencidas — ${overduePair.supplier} → ${overduePair.buyer}` : ""}
        open={overduePair !== null}
        onClose={() => setOverduePair(null)}
      >
        {loadingOverdue ? (
          <p className="text-center text-gray-400 text-sm py-10">Cargando facturas...</p>
        ) : (
          <SupplierInvoicesTable rows={overduePairInvoices} />
        )}
      </SectionModal>

    </div>
  );
}