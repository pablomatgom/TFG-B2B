"use client";

import { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import type { ReactNode } from "react";
import { ArrowRightIcon, ChevronDownIcon, ChevronRightIcon, XMarkIcon, InformationCircleIcon } from "@heroicons/react/24/outline";
import type { ExactPathRow, ForwardRow } from "@/types/analytics";
import { EUR, DOC_COLORS, ESTADO_STYLE } from "@/lib/analytics";


export function InfoTooltip({ content, direction = "up", align = "center" }: {
  content:    ReactNode;
  direction?: "up" | "down";
  align?:     "center" | "end";
}) {
  const isDown = direction === "down";
  const posX   = align === "end" ? "right-0" : "left-1/2 -translate-x-1/2";
  return (
    <div className="relative group inline-flex items-center ml-1.5">
      <InformationCircleIcon className="w-3.5 h-3.5 text-gray-400 hover:text-indigo-500 transition-colors cursor-default" />
      <div className={`pointer-events-none absolute ${posX} w-56 invisible opacity-0 group-hover:visible group-hover:opacity-100 transition-all duration-150 z-20 flex flex-col ${
        isDown ? "top-full mt-2" : "bottom-full mb-2"
      } ${isDown ? "" : "flex-col-reverse"}`}>
        <div className="bg-gray-900 text-white text-xs rounded-lg px-3 py-2.5 shadow-xl leading-relaxed text-left">
          {content}
        </div>
      </div>
    </div>
  );
}

export function SectionLabel({ index, title, subtitle, tooltip }: {
  index:    string;
  title:    string;
  subtitle: ReactNode;
  tooltip?: ReactNode;
}) {
  return (
    <div className="flex items-baseline gap-3 mb-4">
      <span className="text-indigo-400 font-mono text-xs">{index}</span>
      <div className="flex-1">
        <div className="flex items-center gap-1">
          <h3 className="text-gray-900 font-semibold text-sm">{title}</h3>
          {tooltip && <InfoTooltip content={tooltip} />}
        </div>
        <p className="text-gray-500 text-xs">{subtitle}</p>
      </div>
    </div>
  );
}

export const EMPTY = (
  <p className="text-gray-400 py-8 text-center text-sm">
    Sin datos — ejecuta el pipeline desde{" "}
    <a href="/pipeline" className="text-indigo-600 underline">Pipeline</a>.
  </p>
);

export function DocChip({ tipo, discrepancy }: { tipo: string; discrepancy: boolean }) {
  const cls = DOC_COLORS[tipo] ?? "bg-gray-100 text-gray-600 border-gray-200";
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded border text-xs font-mono ${cls}`}>
      {discrepancy && <span className="text-red-500">⚠</span>}
      {tipo}
    </span>
  );
}

export function DocChain({ chain }: { chain: ExactPathRow["cadena_completa"] }) {
  return (
    <div className="flex flex-wrap items-center gap-1">
      {chain.map((node, i) => (
        <span key={node.id} className="flex items-center gap-1">
          <DocChip tipo={node.tipo} discrepancy={node.discrepancy} />
          {i < chain.length - 1 && (
            <ArrowRightIcon className="w-3 h-3 text-gray-400 shrink-0" />
          )}
        </span>
      ))}
    </div>
  );
}

export function EstadoPill({ estado }: { estado: string }) {
  return (
    <span className={`px-2 py-0.5 rounded border text-xs font-semibold ${ESTADO_STYLE[estado] ?? "bg-gray-100 text-gray-500 border-gray-200"}`}>
      {estado}
    </span>
  );
}

export interface KpiItem {
  label:       string;
  value:       string;
  sub?:        string;
  valueClass?: string;
}

interface KpiStripProps {
  items:      KpiItem[];
  cols?:      2 | 3 | 4;
  /** "cards" = separate rounded cards with gap; "strip" = hairline-divided single block */
  variant?:   "cards" | "strip";
  valueSize?: "lg" | "xl" | "2xl";
  className?: string;
}

const COL_CLASS: Record<number, string> = {
  2: "grid-cols-2",
  3: "grid-cols-3",
  4: "grid-cols-4",
};
const SIZE_CLASS: Record<string, string> = {
  lg:  "text-lg",
  xl:  "text-xl",
  "2xl": "text-2xl",
};

export function KpiStrip({
  items,
  cols      = 3,
  variant   = "cards",
  valueSize = "lg",
  className = "",
}: KpiStripProps) {
  if (variant === "strip") {
    return (
      <div className={`grid ${COL_CLASS[cols]} gap-px bg-gray-100 border border-gray-100 rounded-xl overflow-hidden mb-4 ${className}`}>
        {items.map((kpi) => (
          <div key={kpi.label} className="bg-white px-4 py-4 text-center flex flex-col justify-center">
            <p className={`font-black tabular-nums truncate ${SIZE_CLASS[valueSize]} ${kpi.valueClass ?? "text-gray-900"}`}>
              {kpi.value}
            </p>
            {kpi.sub && (
              <p className="text-gray-400 text-xs mt-0.5 truncate">{kpi.sub}</p>
            )}
            <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-400 mt-1">{kpi.label}</p>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={`grid ${COL_CLASS[cols]} gap-4 mb-4 ${className}`}>
      {items.map((kpi) => (
        <div key={kpi.label} className="bg-white border border-gray-200 rounded-xl shadow-sm p-4 text-center flex flex-col justify-center">
          <p className="text-gray-400 text-[10px] font-semibold uppercase tracking-wide mb-1">{kpi.label}</p>
          <p className={`font-black tabular-nums ${SIZE_CLASS[valueSize]} ${kpi.valueClass ?? "text-gray-900"}`}>
            {kpi.value}
          </p>
          {kpi.sub && (
            <p className="text-gray-400 text-xs mt-1 truncate">{kpi.sub}</p>
          )}
        </div>
      ))}
    </div>
  );
}

export function ProgressBar({
  pct,
  colorClass = "bg-violet-400",
  width       = "w-full",
  transition  = false,
}: {
  pct:         number;
  colorClass?: string;
  width?:      string;
  transition?: boolean;
}) {
  return (
    <div className={`${width} h-1.5 bg-gray-100 rounded-full overflow-hidden`}>
      <div
        className={`h-full rounded-full ${transition ? "transition-[width] duration-500" : ""} ${colorClass}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

export function ShowMoreButton({ total, onClick }: { total: number; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="mt-3 w-full py-2 text-[11px] font-semibold rounded-lg border border-gray-200 text-gray-500 bg-white hover:bg-gray-50 hover:text-gray-700 active:bg-gray-100 active:scale-[0.99] transition-all duration-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
    >
      Ver todos ({total}) →
    </button>
  );
}

export function SectionModal({
  title, open, onClose, children,
}: {
  title: string; open: boolean; onClose: () => void; children: ReactNode;
}) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open || !mounted) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40" onClick={onClose}>
      <div className="relative w-auto min-w-[min(640px,90vw)] max-w-[90vw] bg-white border border-gray-200 rounded-xl shadow-xl overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <p className="text-gray-900 font-bold text-base">{title}</p>
          <button onClick={onClose} className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors">
            <XMarkIcon className="w-4 h-4" />
          </button>
        </div>
        <div className="px-6 py-5 max-h-[70vh] overflow-y-auto">{children}</div>
      </div>
    </div>,
    document.body
  );
}

export function ForwardRowItem({ row }: { row: ForwardRow }) {
  const [open, setOpen] = useState(false);
  const allClean = row.docs_con_discrepancia === 0;
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen((p) => !p)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-3 min-w-0">
          {open
            ? <ChevronDownIcon  className="w-4 h-4 text-gray-400 shrink-0" />
            : <ChevronRightIcon className="w-4 h-4 text-gray-400 shrink-0" />
          }
          <span className="font-mono text-xs text-gray-400 shrink-0">{row.pedido_id}</span>
          <span className="text-gray-900 text-sm truncate">{row.proveedor}</span>
          <span className="text-gray-400 text-xs">→ {row.comprador}</span>
        </div>
        <div className="flex items-center gap-3 shrink-0 ml-4">
          <span className="text-gray-500 text-xs">{row.total_docs_cumplimiento} docs</span>
          {allClean
            ? <span className="px-2 py-0.5 rounded border text-xs font-semibold bg-emerald-50 text-emerald-700 border-emerald-200">Sin conflictos</span>
            : <span className="px-2 py-0.5 rounded border text-xs font-semibold bg-red-50 text-red-700 border-red-200">{row.docs_con_discrepancia} conflicto{row.docs_con_discrepancia > 1 ? "s" : ""}</span>
          }
          <span className="text-indigo-600 font-mono text-sm">{EUR(row.importe_pedido_eur, 2)} €</span>
        </div>
      </button>
      {open && (
        <div className="px-4 py-3 bg-white border-t border-gray-100 flex flex-wrap gap-2">
          {row.documentos_cumplimiento.map((doc) => (
            <DocChip key={doc.id} tipo={doc.tipo} discrepancy={doc.discrepancy} />
          ))}
        </div>
      )}
    </div>
  );
}