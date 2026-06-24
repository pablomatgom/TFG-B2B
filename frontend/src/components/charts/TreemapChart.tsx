"use client";

import { useState } from "react";
import { createPortal } from "react-dom";
import { Treemap, ResponsiveContainer } from "recharts";

export interface CompanyInfo {
  name:   string;
  role:   string;
  region: string;
  band:   string;
  sector: string;
}

const ROLE_STYLE: Record<string, string> = {
  SUPPLIER: "bg-indigo-50 text-indigo-600",
  BUYER:    "bg-emerald-50 text-emerald-600",
  HYBRID:   "bg-amber-50 text-amber-600",
};

const BAND_STYLE: Record<string, string> = {
  micro:      "bg-gray-100 text-gray-500",
  pyme:       "bg-blue-50 text-blue-600",
  mid:        "bg-purple-50 text-purple-600",
  enterprise: "bg-rose-50 text-rose-600",
};

// NACE division letter → readable sector name
const NACE_DIV: Record<string, string> = {
  A: "Agrícola", B: "Extractiva", C: "Manufactura", D: "Energía",
  E: "Agua/residuos", F: "Construcción", G: "Comercio mayorista",
  H: "Transporte/logística", I: "Hostelería", J: "TIC/Software",
  K: "Financiero", L: "Inmobiliario", M: "Servicios profesionales",
  N: "Servicios admin.", Q: "Sanidad", R: "Cultura/ocio", S: "Otros servicios",
};
// Specific NACE group labels for the most common codes in this dataset
const NACE_GROUP: Record<string, string> = {
  C10: "Alimentación", C13: "Textil", C20: "Química", C22: "Plástico/caucho",
  C25: "Metal fabricado", C26: "Electrónica", C28: "Maquinaria", C29: "Automoción",
  G46: "Comercio mayor.", H52: "Almacenaje/log.", J62: "Software/TI", M71: "Ingeniería",
};
function naceShort(code: string): string {
  return NACE_GROUP[code] ?? NACE_DIV[code?.charAt(0)] ?? code;
}

function freq<T>(arr: T[], key: (v: T) => string): [string, number][] {
  const map: Record<string, number> = {};
  for (const v of arr) { const k = key(v) ?? ""; if (k) map[k] = (map[k] ?? 0) + 1; }
  return Object.entries(map).sort((a, b) => b[1] - a[1]);
}

function CommunityProfile({ companies }: { companies: CompanyInfo[] }) {
  if (companies.length === 0) return null;
  const total = companies.length;

  // Role counts
  const roles = { SUPPLIER: 0, BUYER: 0, HYBRID: 0 } as Record<string, number>;
  for (const c of companies) roles[c.role] = (roles[c.role] ?? 0) + 1;

  // Sector concentration
  const sectorFreq  = freq(companies, (c) => c.sector);
  const topSector   = sectorFreq[0];
  const sectorPct   = topSector ? Math.round((topSector[1] / total) * 100) : 0;
  const sectorCount = sectorFreq.length;

  // Geographic cohesion
  const regionFreq    = freq(companies, (c) => c.region);
  const topRegion     = regionFreq[0];
  const topRegionPct  = topRegion ? Math.round((topRegion[1] / total) * 100) : 0;
  const regionCount   = regionFreq.length;
  const top3Regions   = regionFreq.slice(0, 3).map(([k]) => k);
  const secondRegion  = regionFreq[1];
  const secondRegionPct = secondRegion ? Math.round((secondRegion[1] / total) * 100) : 0;
  const top2Pct       = topRegionPct + secondRegionPct;

  // Size band distribution
  const bandFreq = freq(companies, (c) => c.band);
  const enterprisePct = Math.round(((bandFreq.find(([k]) => k === "enterprise")?.[1] ?? 0) / total) * 100);

  // ── Derived archetypes ─────────────────────────────────────
  const hybridPct   = Math.round((roles.HYBRID / total) * 100);
  const supplierPct = Math.round((roles.SUPPLIER / total) * 100);
  const buyerPct    = Math.round((roles.BUYER / total) * 100);

  const roleArchetype =
    hybridPct  >= 50                  ? { label: "Hub intermediario", color: "bg-amber-50 text-amber-700 border-amber-200" }
  : supplierPct >= buyerPct + 12      ? { label: "Hub productor",     color: "bg-indigo-50 text-indigo-700 border-indigo-200" }
  : buyerPct   >= supplierPct + 12    ? { label: "Centro comprador",  color: "bg-emerald-50 text-emerald-700 border-emerald-200" }
  :                                     { label: "Ecosistema mixto",  color: "bg-gray-100 text-gray-600 border-gray-200" };

  // Short region name (drop /secondary name like "Valencia/València")
  const shortRegion = (r: string) => r.split("/")[0].trim();
  const geoArchetype =
    topRegionPct >= 30
      ? { label: `Anclado en ${shortRegion(topRegion[0])} · ${topRegionPct}%`, color: "bg-blue-50 text-blue-700 border-blue-200" }
  : top2Pct >= 30 && secondRegionPct >= 10
      ? { label: `Corredor ${shortRegion(topRegion[0])}–${shortRegion(secondRegion[0])} · ${top2Pct}%`, color: "bg-sky-50 text-sky-700 border-sky-200" }
  : regionCount <= 5
      ? { label: `${regionCount} regiones`,    color: "bg-sky-50 text-sky-700 border-sky-200" }
  :   { label: `Disperso (${regionCount}r)`,   color: "bg-gray-100 text-gray-500 border-gray-200" };

  // Sector groups as fallback when no single code dominates
  const SECTOR_GROUPS: [string, string[]][] = [
    ["Tech/Digital",     ["J62", "C26"]],
    ["Manufactura ind.", ["C20", "C25", "C22", "C28"]],
    ["Alim./Textil",     ["C10", "C13"]],
    ["Logística",        ["H52", "G46"]],
  ];
  const sectorMap = Object.fromEntries(sectorFreq);
  const bestGroup = SECTOR_GROUPS
    .map(([name, codes]) => ({ name, pct: Math.round(codes.reduce((s, c) => s + (sectorMap[c] ?? 0), 0) / total * 100) }))
    .filter((g) => g.pct >= 30)
    .sort((a, b) => b.pct - a.pct)[0];

  const sectorArchetype =
    sectorPct  >= 30
      ? { label: `Esp. ${naceShort(topSector[0])} · ${sectorPct}%`,    color: "bg-teal-50 text-teal-700 border-teal-200" }
  : sectorPct  >= 20
      ? { label: `Tend. ${naceShort(topSector[0])} · ${sectorPct}%`,   color: "bg-violet-50 text-violet-700 border-violet-200" }
  : bestGroup
      ? { label: `Grupo ${bestGroup.name} · ${bestGroup.pct}%`,        color: "bg-violet-50 text-violet-700 border-violet-200" }
  :   { label: `Diversificado (${sectorCount} sectores)`,               color: "bg-gray-100 text-gray-500 border-gray-200" };

  // Fragility tag: no enterprise anchors in a large community is a risk signal
  const fragilityTag = total >= 40 && enterprisePct === 0
    ? { label: "Sin anclaje enterprise", color: "bg-red-50 text-red-600 border-red-200" }
    : enterprisePct >= 15
    ? { label: `Enterprise ${enterprisePct}% · robusto`, color: "bg-rose-50 text-rose-700 border-rose-200" }
    : null;

  const archetypes = [roleArchetype, geoArchetype, sectorArchetype, ...(fragilityTag ? [fragilityTag] : [])];

  // Band order for bar
  const BAND_ORDER  = ["micro", "pyme", "mid", "enterprise"];
  const BAND_COLORS = ["bg-gray-300", "bg-blue-300", "bg-purple-300", "bg-rose-400"];

  return (
    <div className="px-4 py-3.5 bg-gray-50/60 border-b border-gray-100 space-y-3">

      {/* ── Insight tags ─────────────────────────────────────── */}
      <div className="flex flex-wrap gap-1.5">
        {archetypes.map((a) => (
          <span key={a.label} className={`inline-flex items-center px-2 py-0.5 rounded-full border text-[10px] font-semibold tracking-wide ${a.color}`}>
            {a.label}
          </span>
        ))}
      </div>

      {/* ── Role distribution bar ─────────────────────────────── */}
      <div className="space-y-1">
        <div className="flex items-center gap-2 text-[10px] text-gray-400 font-semibold uppercase tracking-wide">
          <span className="w-14 shrink-0">Roles</span>
          <div className="flex items-center gap-2 flex-wrap">
            {(["SUPPLIER","BUYER","HYBRID"] as const).map((r) => roles[r] > 0 && (
              <span key={r} className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded ${ROLE_STYLE[r]}`}>
                {r === "SUPPLIER" ? "SUP" : r === "BUYER" ? "BUY" : "HYB"}
                <span className="font-mono">{roles[r]}</span>
                <span className="opacity-50">({Math.round(roles[r]/total*100)}%)</span>
              </span>
            ))}
          </div>
        </div>
        <div className="flex h-1.5 rounded-full overflow-hidden bg-gray-200 ml-16">
          {(["SUPPLIER","BUYER","HYBRID"] as const).map((r, i) => roles[r] > 0 && (
            <div key={r} className={["bg-indigo-400","bg-emerald-400","bg-amber-400"][i]}
              style={{ width: `${(roles[r] / total) * 100}%` }} />
          ))}
        </div>
      </div>

      {/* ── Size band bar ─────────────────────────────────────── */}
      <div className="space-y-1">
        <div className="flex items-center gap-2 text-[10px] text-gray-400 font-semibold uppercase tracking-wide">
          <span className="w-14 shrink-0">Tamaño</span>
          <div className="flex items-center gap-2 flex-wrap">
            {bandFreq.map(([band, count]) => (
              <span key={band} className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded ${BAND_STYLE[band] ?? "bg-gray-100 text-gray-500"}`}>
                {band} <span className="font-mono">{count}</span>
              </span>
            ))}
          </div>
        </div>
        <div className="flex h-1.5 rounded-full overflow-hidden bg-gray-200 ml-16">
          {BAND_ORDER.map((b, i) => {
            const count = bandFreq.find(([k]) => k === b)?.[1] ?? 0;
            return count > 0 ? (
              <div key={b} className={BAND_COLORS[i]} style={{ width: `${(count / total) * 100}%` }} />
            ) : null;
          })}
        </div>
      </div>

      {/* ── Geography + Sector detail ─────────────────────────── */}
      <div className="flex flex-col gap-1 text-xs ml-16">
        <div className="flex items-baseline gap-1.5 text-gray-500">
          <span className="text-gray-400 text-[10px] font-semibold uppercase tracking-wide">Regiones</span>
          {top3Regions.join(" · ")}
          {regionCount > 3 && <span className="text-gray-400">+{regionCount - 3}</span>}
        </div>
        <div className="flex items-baseline gap-1.5 text-gray-500">
          <span className="text-gray-400 text-[10px] font-semibold uppercase tracking-wide">Sector top</span>
          {topSector
            ? <>{naceShort(topSector[0])} <span className="font-mono text-gray-400">{sectorPct}%</span>
                {bestGroup && sectorPct < 20 && (
                  <span className="text-gray-400 ml-1">· grupo {bestGroup.name} {bestGroup.pct}%</span>
                )}
              </>
            : "—"
          }
        </div>
      </div>
    </div>
  );
}

function CompanyTable({ companies }: { companies: CompanyInfo[] }) {
  return (
    <table className="w-full text-sm">
      <thead className="sticky top-0 bg-gray-50 border-b border-gray-100">
        <tr>
          <th className="px-4 py-2.5 text-left text-gray-400 text-[10px] font-semibold uppercase tracking-wide w-8">#</th>
          <th className="px-4 py-2.5 text-left text-gray-400 text-[10px] font-semibold uppercase tracking-wide">Empresa</th>
          <th className="px-4 py-2.5 text-left text-gray-400 text-[10px] font-semibold uppercase tracking-wide">Rol</th>
          <th className="px-4 py-2.5 text-left text-gray-400 text-[10px] font-semibold uppercase tracking-wide">Región</th>
          <th className="px-4 py-2.5 text-left text-gray-400 text-[10px] font-semibold uppercase tracking-wide">Tamaño</th>
          <th className="px-4 py-2.5 text-left text-gray-400 text-[10px] font-semibold uppercase tracking-wide">Sector</th>
        </tr>
      </thead>
      <tbody>
        {companies.map((c, i) => (
          <tr key={i} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
            <td className="px-4 py-2.5 text-gray-400 font-mono text-xs">{i + 1}</td>
            <td className="px-4 py-2.5 text-gray-900 font-medium">{c.name}</td>
            <td className="px-4 py-2.5">
              <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide ${ROLE_STYLE[c.role] ?? "bg-gray-100 text-gray-500"}`}>
                {c.role}
              </span>
            </td>
            <td className="px-4 py-2.5 text-gray-500 text-xs">{c.region ?? "—"}</td>
            <td className="px-4 py-2.5">
              <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-semibold ${BAND_STYLE[c.band] ?? "bg-gray-100 text-gray-500"}`}>
                {c.band ?? "—"}
              </span>
            </td>
            <td className="px-4 py-2.5 text-gray-400 text-xs font-mono">{c.sector ?? "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export interface TreemapItem {
  name:       string;
  size:       number;
  fill?:      string;
  subtitle?:  string;
  companies?: CompanyInfo[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  [key: string]: any;
}

interface TreemapChartProps {
  data:         TreemapItem[];
  height?:      number;
  aspectRatio?: number;
  showLegend?:  boolean;
  colors?:      string[];
}

const DEFAULT_COLORS = [
  "#6366f1","#8b5cf6","#14b8a6","#3b82f6","#ec4899",
  "#f97316","#10b981","#f59e0b","#ef4444","#06b6d4",
];

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function Cell({ x, y, width, height, name, size, total, fill, depth, companies, onCellClick }: any) {
  if (depth === 0) return null;

  const pct      = total > 0 ? ((size / total) * 100).toFixed(1) : null;
  const heroSize = Math.min(Math.max(Math.floor(Math.sqrt(width * height) / 5), 13), 32);
  const showHero = width > 44 && height > 30;
  const showName = width > 72 && height > 58;
  const showPct  = width > 84 && height > 78 && pct;

  const centerY = y + height / 2;
  const nameY   = centerY - heroSize / 2 - 7;
  const heroY   = centerY + (showName ? 12 : 0) - (showPct ? heroSize / 4 : 0);
  const pctY    = centerY + heroSize / 2 + 10;

  const clickable = !!onCellClick;

  return (
    <g
      onClick={() => clickable && onCellClick({ name, size, companies })}
      style={{ cursor: clickable ? "pointer" : "default" }}
    >
      <rect
        x={x + 1} y={y + 1} width={width - 2} height={height - 2}
        fill={fill} stroke="white" strokeWidth={2} rx={6}
      />
      {showName && (
        <text
          x={x + width / 2} y={nameY}
          textAnchor="middle" dominantBaseline="middle"
          fill="white" fillOpacity={0.75} fontSize={10} fontWeight={600}
        >
          {name}
        </text>
      )}
      {showHero && (
        <text
          x={x + width / 2} y={heroY}
          textAnchor="middle" dominantBaseline="middle"
          fill="white" fontSize={heroSize} fontWeight={800}
        >
          {size}
        </text>
      )}
      {showPct && (
        <text
          x={x + width / 2} y={pctY}
          textAnchor="middle" dominantBaseline="middle"
          fill="white" fillOpacity={0.6} fontSize={9} fontWeight={500}
        >
          {pct}%
        </text>
      )}
    </g>
  );
}

export default function TreemapChart({
  data,
  height = 280,
  aspectRatio = 4 / 3,
  showLegend = true,
  colors = DEFAULT_COLORS,
}: TreemapChartProps) {
  const [selected,  setSelected]  = useState<TreemapItem | null>(null);
  const [showModal, setShowModal] = useState(false);

  const total = data.reduce((s, d) => s + d.size, 0);
  const enriched = data.map((item, i) => ({
    ...item,
    fill:     item.fill ?? colors[i % colors.length],
    subtitle: item.subtitle ?? `${item.size} elementos`,
    total,
  }));

  function handleCellClick(item: TreemapItem) {
    if (selected?.name === item.name) {
      setSelected(null);
    } else {
      setSelected(item);
      setShowModal(false);
    }
  }

  const companies: CompanyInfo[] = selected?.companies ?? [];

  return (
    <div>
      <ResponsiveContainer width="100%" height={height}>
        <Treemap
          data={enriched}
          dataKey="size"
          aspectRatio={aspectRatio}
          isAnimationActive={false}
          content={<Cell onCellClick={handleCellClick} />}
        />

      </ResponsiveContainer>

      {showLegend && (
        <div className="flex flex-wrap justify-center gap-x-4 gap-y-1.5 mt-4 pt-4 border-t border-gray-100">
          {enriched.map((d) => (
            <span key={d.name} className="flex items-center gap-1.5 text-xs text-gray-500">
              <span className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ backgroundColor: d.fill }} />
              {d.name}
              <span className="text-gray-400 font-mono">
                ({d.size} · {total > 0 ? ((d.size / total) * 100).toFixed(1) : 0}%)
              </span>
            </span>
          ))}
        </div>
      )}

      {/* ── Inline company panel ─────────────────────────────────── */}
      {selected && (
        <div className="mt-4 border border-gray-200 rounded-xl overflow-hidden">

          {/* Panel header */}
          <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-200">
            <div>
              <p className="font-semibold text-gray-900 text-sm">{selected.name}</p>
              <p className="text-gray-400 text-xs mt-0.5">{selected.size} empresas en este ecosistema</p>
            </div>
            <button
              onClick={() => setSelected(null)}
              className="text-gray-400 hover:text-gray-600 transition-colors text-xl leading-none px-1"
              aria-label="Cerrar"
            >
              ×
            </button>
          </div>

          <CommunityProfile companies={companies} />
          <CompanyTable companies={companies.slice(0, 10)} />

          {companies.length > 10 && (
            <div className="px-4 py-3 border-t border-gray-100 bg-gray-50">
              <button
                onClick={() => setShowModal(true)}
                className="text-indigo-600 hover:text-indigo-700 text-sm font-medium transition-colors"
              >
                Ver todas ({companies.length} empresas) →
              </button>
            </div>
          )}
        </div>
      )}

      {/* ── Modal — full company list ─────────────────────────── */}
      {showModal && selected && createPortal(
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/40" onClick={() => setShowModal(false)} />
          <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 shrink-0">
              <div>
                <p className="font-semibold text-gray-900">{selected.name}</p>
                <p className="text-gray-400 text-xs mt-0.5">{companies.length} empresas en este ecosistema</p>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors text-xl leading-none px-1"
                aria-label="Cerrar"
              >
                ×
              </button>
            </div>
            <div className="overflow-y-auto">
              <CommunityProfile companies={companies} />
              <CompanyTable companies={companies} />
            </div>
          </div>
        </div>,
        document.body,
      )}
    </div>
  );
}