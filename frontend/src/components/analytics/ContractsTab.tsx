"use client";

import { useState } from "react";
import { EyeIcon } from "@heroicons/react/24/outline";
import RingChart from "@/components/charts/RingChart";
import type { ContractProfileData, ContractDetailRow, SupplierContractRow } from "@/types/analytics";
import { reliabilityBadge, EUR, PAGE_SIZE_LG } from "@/lib/analytics";
import { EMPTY, ShowMoreButton, SectionModal, SectionLabel } from "./shared";
import { API_BASE } from "@/lib/api";

const CONTRACT_HEX: Record<string, string> = {
  FRAME:  "#3b82f6",
  ANNUAL: "#8b5cf6",
  SPOT:   "#f59e0b",
};

const CONTRACT_BADGE: Record<string, string> = {
  FRAME:  "bg-blue-50 text-blue-700 border-blue-200",
  ANNUAL: "bg-violet-50 text-violet-700 border-violet-200",
  SPOT:   "bg-amber-50 text-amber-700 border-amber-200",
};


function ContractTypeBadge({ type }: { type: string }) {
  const cls = CONTRACT_BADGE[type] ?? "bg-gray-100 text-gray-600 border-gray-200";
  return (
    <span className={`inline-flex px-1.5 py-0.5 rounded border text-xs font-mono mr-1 ${cls}`}>
      {type}
    </span>
  );
}

function formatContractAge(days: number): string {
  if (days >= 365) return `${(days / 365).toFixed(1)} años`;
  if (days >= 30)  return `${Math.round(days / 30)} meses`;
  return `${days} d`;
}

function DetailTable({
  rows,
  onViewContracts,
}: {
  rows: ContractDetailRow[];
  onViewContracts: (supplier: string) => void;
}) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="bg-gray-50 border-b border-gray-100">
          {["Proveedor", "Región", "Contratos", "Tipos", "Exclusividad", "Fiabilidad", "Plazo Pago", ""].map((h, i) => (
            <th
              key={h + i}
              className={`px-4 py-3 text-[11px] font-semibold uppercase tracking-wide text-gray-400 ${i >= 4 && i <= 6 ? "text-right" : "text-left"}`}
            >
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {rows.map((row) => (
          <tr key={row.supplier} className="hover:bg-gray-50 transition-colors">
            <td className="px-4 py-3 text-gray-900 font-medium max-w-[180px] truncate">{row.supplier}</td>
            <td className="px-4 py-3 text-gray-500 text-xs">{row.region ?? "—"}</td>
            <td className="px-4 py-3 font-mono text-gray-600 tabular-nums">{row.total_contracts}</td>
            <td className="px-4 py-3">
              {(row.contract_types ?? []).map((t) => (
                <ContractTypeBadge key={t} type={t} />
              ))}
            </td>
            <td className="px-4 py-3 text-right">
              <span className={`inline-flex justify-center px-2 py-0.5 rounded-full text-xs font-mono font-semibold min-w-[3rem] ${
                row.exclusive_pct >= 50 ? "bg-amber-50 text-amber-600" : "bg-gray-50 text-gray-500"
              }`}>
                {row.exclusive_pct.toFixed(0)}%
              </span>
            </td>
            <td className="px-4 py-3 text-right">
              <span className={`inline-flex justify-center px-2 py-0.5 rounded-full text-xs font-mono font-semibold min-w-[3rem] ${reliabilityBadge(row.avg_reliability)}`}>
                {(row.avg_reliability * 100).toFixed(1)}%
              </span>
            </td>
            <td className="px-4 py-3 text-right font-mono text-gray-600 tabular-nums">
              {row.avg_payment_terms_days} d
            </td>
            <td className="px-4 py-3 text-right">
              <button
                onClick={() => onViewContracts(row.supplier)}
                title="Ver contratos individuales"
                className="p-1.5 rounded-lg text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
              >
                <EyeIcon className="w-4 h-4" />
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function SupplierContractsTable({ rows }: { rows: SupplierContractRow[] }) {
  if (rows.length === 0) return (
    <p className="text-center text-gray-400 text-sm py-10">Sin contratos individuales disponibles.</p>
  );
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="bg-gray-50 border-b border-gray-100">
          {["Comprador", "Región", "Tipo", "Exclusivo", "Fiabilidad", "Plazo Pago", "Volumen", "Vigente desde"].map((h, i) => (
            <th
              key={h}
              className={`px-4 py-3 text-[11px] font-semibold uppercase tracking-wide text-gray-400 ${i >= 4 ? "text-right" : "text-left"}`}
            >
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody className="divide-y divide-gray-100">
        {rows.map((row, idx) => (
          <tr key={idx} className="hover:bg-gray-50 transition-colors">
            <td className="px-4 py-3 text-gray-900 font-medium max-w-[160px] truncate">{row.buyer}</td>
            <td className="px-4 py-3 text-gray-500 text-xs">{row.buyer_region ?? "—"}</td>
            <td className="px-4 py-3">
              <ContractTypeBadge type={row.contract_type} />
            </td>
            <td className="px-4 py-3">
              {row.is_exclusive ? (
                <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">Sí</span>
              ) : (
                <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-gray-50 text-gray-400 border border-gray-200">No</span>
              )}
            </td>
            <td className="px-4 py-3 text-right">
              <span className={`inline-flex justify-center px-2 py-0.5 rounded-full text-xs font-mono font-semibold min-w-[3rem] ${reliabilityBadge(row.reliability_score)}`}>
                {(row.reliability_score * 100).toFixed(1)}%
              </span>
            </td>
            <td className="px-4 py-3 text-right font-mono text-gray-600 tabular-nums">
              {row.payment_terms_days} d
            </td>
            <td className="px-4 py-3 text-right font-mono text-gray-600 tabular-nums">
              {EUR(row.agreed_volume_eur)}
            </td>
            <td className="px-4 py-3 text-right text-xs text-gray-500 tabular-nums">
              {row.since_date ?? "—"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

interface Props {
  contracts:      ContractProfileData | null;
  contractDetail: ContractDetailRow[];
}

export function ContractsTab({ contracts, contractDetail }: Props) {
  const [showDetailAll, setShowDetailAll]             = useState(false);
  const [selectedSupplier, setSelectedSupplier]       = useState<string | null>(null);
  const [supplierContracts, setSupplierContracts]     = useState<SupplierContractRow[]>([]);
  const [loadingContracts, setLoadingContracts]       = useState(false);

  async function openSupplierContracts(supplier: string) {
    setSelectedSupplier(supplier);
    setSupplierContracts([]);
    setLoadingContracts(true);
    try {
      const res = await fetch(`${API_BASE}/api/analytics/risk/supplier-contracts?supplier=${encodeURIComponent(supplier)}`);
      if (res.ok) setSupplierContracts(await res.json());
    } finally {
      setLoadingContracts(false);
    }
  }

  if (!contracts && contractDetail.length === 0) return EMPTY;

  const ringData = contracts
    ? Object.entries(contracts.contract_type_distribution).map(([name, value]) => ({
        name,
        value,
        color: CONTRACT_HEX[name] ?? "#6b7280",
      }))
    : [];

  const totalContracts = ringData.reduce((s, r) => s + r.value, 0);

  return (
    <div className="space-y-10">

      {/* ── 01 · PERFIL DE CONTRATOS DE RED ─────────────────────── */}
      {contracts && (
        <section>
          <SectionLabel
            index="01 /"
            title="Perfil de Contratos de Red"
            subtitle="Distribución de tipos de contrato, exclusividad y condiciones de pago en los acuerdos de suministro activos de la red. Permite identificar el grado de dependencia estructural y la estabilidad de las relaciones comerciales."
          />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

            {/* Donut card */}
            <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5">
              <p className="text-gray-700 font-semibold text-sm mb-4">Distribución por tipo</p>
              {ringData.length > 0 ? (
                <RingChart
                  data={ringData}
                  centerLabel={totalContracts.toLocaleString("es-ES")}
                  centerSub="contratos"
                  formatHoverValue={(v, t) => `${v.toLocaleString()} (${((v / t) * 100).toFixed(1)}%)`}
                />
              ) : (
                <p className="text-gray-400 text-sm text-center py-8">Sin datos</p>
              )}
            </div>

            {/* KPI grid */}
            <div className="grid grid-cols-2 gap-4 h-full">
              {[
                {
                  label: "Exclusividad",
                  value: `${contracts.exclusivity_pct.toFixed(1)}%`,
                  sub:   "relaciones exclusivas",
                },
                {
                  label: "Fiabilidad Red",
                  value: `${(contracts.avg_reliability_score * 100).toFixed(1)}%`,
                  sub:   "media global",
                },
                {
                  label: "Plazo de Pago",
                  value: `${contracts.avg_payment_terms_days.toFixed(0)} d`,
                  sub:   "media acordada",
                },
                {
                  label: "Antigüedad",
                  value: formatContractAge(contracts.avg_contract_age_days),
                  sub:   "media contratos",
                },
              ].map((s) => (
                <div key={s.label} className="bg-white border border-gray-200 rounded-xl shadow-sm p-4 flex flex-col justify-between">
                  <p className="text-gray-400 text-[10px] font-semibold uppercase tracking-wide mb-1">{s.label}</p>
                  <p className={`text-2xl font-black tabular-nums text-gray-900`}>{s.value}</p>
                  <p className="text-gray-400 text-xs mt-1">{s.sub}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ── 02 · DESGLOSE POR PROVEEDOR ──────────────────────────── */}
      {contractDetail.length > 0 && (
        <section>
          <SectionLabel
            index="02 /"
            title="Desglose por Proveedor"
            subtitle="Tipos de contrato activos, tasa de exclusividad y fiabilidad media por proveedor, ordenados por volumen de contratos. Los proveedores con alta exclusividad y baja fiabilidad representan un riesgo de dependencia prioritario."
          />
          <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
            <DetailTable rows={contractDetail.slice(0, PAGE_SIZE_LG)} onViewContracts={openSupplierContracts} />
            {contractDetail.length > PAGE_SIZE_LG && (
              <div className="px-5 pb-4">
                <ShowMoreButton total={contractDetail.length} onClick={() => setShowDetailAll(true)} />
              </div>
            )}
          </div>
        </section>
      )}

      {/* ── Modal: full supplier list ─────────────────────────────── */}
      <SectionModal
        title="Desglose por Proveedor — completo"
        open={showDetailAll}
        onClose={() => setShowDetailAll(false)}
      >
        <DetailTable rows={contractDetail} onViewContracts={openSupplierContracts} />
      </SectionModal>

      {/* ── Modal: individual contracts for a supplier ────────────── */}
      <SectionModal
        title={selectedSupplier ? `Contratos de ${selectedSupplier}` : ""}
        open={selectedSupplier !== null}
        onClose={() => setSelectedSupplier(null)}
      >
        {loadingContracts ? (
          <p className="text-center text-gray-400 text-sm py-10">Cargando contratos...</p>
        ) : (
          <SupplierContractsTable rows={supplierContracts} />
        )}
      </SectionModal>

    </div>
  );
}