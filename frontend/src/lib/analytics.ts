/** Pure data helpers for analytics — no React, no JSX. */

export const EUR = (n: number, dec = 0) =>
  Intl.NumberFormat("es-ES", {
    minimumFractionDigits: dec,
    maximumFractionDigits: dec,
  }).format(n);

export const SIGN = (n: number) => (n > 0 ? "+" : "");

export function rateBadge(rate: number): "red" | "yellow" | "emerald" {
  if (rate >= 20) return "red";
  if (rate >= 10) return "yellow";
  return "emerald";
}

export const DOC_COLORS: Record<string, string> = {
  INVOICE:     "bg-red-50 text-red-700 border-red-200",
  ORDER:       "bg-blue-50 text-blue-700 border-blue-200",
  SHIPMENT:    "bg-emerald-50 text-emerald-700 border-emerald-200",
  CREDIT_NOTE: "bg-amber-50 text-amber-700 border-amber-200",
};

export const ESTADO_STYLE: Record<string, string> = {
  SOBREFACTURADO: "bg-red-50 text-red-700 border-red-200",
  SUBFACTURADO:   "bg-amber-50 text-amber-700 border-amber-200",
  CONFORME:       "bg-emerald-50 text-emerald-700 border-emerald-200",
};

export const PAGE_SIZE    = 10;
export const PAGE_SIZE_LG = 15;
export const PAGE_SIZE_SM = 5;

export function lateBarColor(pct: number): string {
  if (pct >= 60) return "bg-red-500";
  if (pct >= 40) return "bg-amber-500";
  return "bg-emerald-500";
}

export function lateBadge(pct: number): string {
  if (pct >= 60) return "bg-red-50 text-red-600";
  if (pct >= 40) return "bg-amber-50 text-amber-600";
  return "bg-emerald-50 text-emerald-600";
}

export function paymentDaysBadge(days: number, agreed: number): string {
  if (days > agreed * 1.1) return "bg-red-50 text-red-600";
  if (days > agreed)       return "bg-amber-50 text-amber-600";
  return "bg-emerald-50 text-emerald-600";
}

export function reliabilityBadge(v: number): string {
  if (v >= 0.8) return "bg-emerald-50 text-emerald-600";
  if (v >= 0.6) return "bg-amber-50 text-amber-600";
  return "bg-red-50 text-red-600";
}

export function discrepancyBadge(pct: number): string {
  if (pct >= 10)  return "bg-red-50 text-red-600";
  if (pct >= 7.5) return "bg-amber-50 text-amber-600";
  return "bg-emerald-50 text-emerald-600";
}

export function riskScoreBadge(score: number): string {
  if (score >= 70) return "bg-red-50 text-red-600";
  if (score >= 40) return "bg-amber-50 text-amber-600";
  return "bg-indigo-50 text-indigo-600";
}

export function fragilityBadge(pct: number): string {
  if (pct >= 80) return "bg-red-50 text-red-600";
  if (pct >= 50) return "bg-amber-50 text-amber-600";
  return "bg-emerald-50 text-emerald-600";
}

export function deltaColor(val: number): string {
  if (val > 0) return "text-red-600";
  if (val < 0) return "text-amber-600";
  return "text-gray-400";
}