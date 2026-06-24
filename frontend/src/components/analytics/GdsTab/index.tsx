"use client";

import { useState, useMemo } from "react";
import TreemapChart from "@/components/charts/TreemapChart";
import type { GdsData } from "@/types/analytics";
import { SectionLabel, ShowMoreButton, SectionModal } from "@/components/analytics/shared";
import { PAGE_SIZE_SM as PAGE } from "@/lib/analytics";
import { RankedBarList } from "./RankedBarList";

function cohesionColor(pct: number) {
  if (pct >= 90) return "text-emerald-600"; // near-fully connected
  if (pct >= 70) return "text-amber-600";   // moderate fragmentation
  return "text-red-600";                    // severely fragmented
}

interface Props { gds: GdsData; }

export function GdsTab({ gds }: Props) {
  const [showBottlenecks, setShowBottlenecks] = useState(false);
  const [showPagerank,    setShowPagerank]    = useState(false);

  const hasWcc         = (gds.wcc?.total_components ?? 0) > 0;
  const hasCommunities = gds.communities.length > 0;
  const hasFailPoints  = gds.bottlenecks.length > 0 || gds.pagerank.length > 0;
  const hasData        = hasWcc || hasCommunities || hasFailPoints;

  // Compute stable section indices for only visible sections
  const sectionIdx = useMemo(() => {
    const visible = [
      { key: "wcc",         show: hasWcc         },
      { key: "communities", show: hasCommunities },
      { key: "fail",        show: hasFailPoints  },
    ];
    let n = 1;
    const map: Record<string, string> = {};
    for (const s of visible) {
      if (s.show) map[s.key] = `${String(n++).padStart(2, "0")} /`;
    }
    return map;
  }, [hasWcc, hasCommunities, hasFailPoints]);

  const maxPagerank = gds.pagerank[0]?.pagerank_score ?? 1;

  // Community summary stats
  const communityTotalNodes = gds.communities.reduce((s, c) => s + c.total_empresas, 0);
  const communitySingletons = gds.communities.filter((c) => c.total_empresas === 1).length;
  const communityAvgSize    = communityTotalNodes > 0
    ? (communityTotalNodes / gds.communities.length).toFixed(1)
    : "—";
  const largestCommunityPct = communityTotalNodes > 0 && gds.communities[0]
    ? ((gds.communities[0].total_empresas / communityTotalNodes) * 100).toFixed(1)
    : "—";

  if (!hasData) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-8 text-center">
        <p className="text-gray-500 text-sm">
          GDS no ha sido ejecutado. Descomenta las llamadas en{" "}
          <code className="text-indigo-600 bg-indigo-50 px-1 py-0.5 rounded text-xs font-mono">run_analyze.py</code>{" "}
          y re-ejecuta el pipeline.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-10">

      {/* ── SALUD DE LA RED ──────────────────────────────────────── */}
      {hasWcc && (
        <section>
          <SectionLabel
            index={sectionIdx["wcc"]}
            title="Salud de la Red"
            subtitle="¿Se fragmentaría la cadena de suministro en una crisis global?"
          />
          <div className="space-y-4">

            <div className="grid grid-cols-3 gap-4">
              <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5 text-center">
                <p className="text-gray-400 text-[10px] font-semibold uppercase tracking-wide mb-1">Tasa de Cohesión</p>
                <p className={`text-2xl font-black tabular-nums ${cohesionColor(gds.wcc.main_component_pct)}`}>
                  {gds.wcc.main_component_pct.toFixed(1)}%
                </p>
                <p className="text-gray-400 text-xs mt-1">empresas en el componente principal</p>
              </div>
              <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5 text-center">
                <p className="text-gray-400 text-[10px] font-semibold uppercase tracking-wide mb-1">Componentes Totales</p>
                <p className="text-2xl font-black text-gray-900 tabular-nums">{gds.wcc.total_components}</p>
                <p className="text-gray-400 text-xs mt-1">subgrafos desconectados</p>
              </div>
              <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5 text-center">
                <p className="text-gray-400 text-[10px] font-semibold uppercase tracking-wide mb-1">Nodos Aislados</p>
                <p className="text-2xl font-black text-gray-900 tabular-nums">{gds.wcc.isolated_nodes}</p>
                <p className="text-gray-400 text-xs mt-1">empresas sin ningún enlace</p>
              </div>
            </div>

            {gds.wcc.components.length > 1 && (
              <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5">
                <p className="text-gray-600 font-semibold text-sm mb-4">
                  Distribución de tamaños — {gds.wcc.components.length} componentes
                </p>
                <div className="space-y-3">
                  {[...gds.wcc.components]
                    .sort((a, b) => b.size - a.size)
                    .slice(0, 10)
                    .map((c, i) => (
                    <div key={c.component_id} className="flex items-center gap-3">
                      <span className={`text-xs font-semibold w-22 shrink-0 ${i === 0 ? "text-indigo-600" : "text-gray-400"}`}>
                        {i === 0 ? "Red Principal" : `Red Auxiliar ${i}`}
                      </span>
                      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-[width] duration-500 ${i === 0 ? "bg-indigo-400" : "bg-gray-300"}`}
                          style={{ width: `${(c.size / gds.wcc.main_component_size) * 100}%` }}
                        />
                      </div>
                      <span className="text-gray-500 text-xs tabular-nums w-8 text-right shrink-0">{c.size}</span>
                    </div>
                  ))}
                  {gds.wcc.components.length > 10 && (
                    <p className="text-gray-400 text-xs text-center pt-1">
                      · {gds.wcc.components.length - 10} componentes menores no mostrados
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* ── ECOSISTEMAS DE MERCADO ───────────────────────────────── */}
      {hasCommunities && (
        <section>
          <SectionLabel
            index={sectionIdx["communities"]}
            title="Ecosistemas de Mercado"
            subtitle="¿Existen clusters comerciales ocultos dentro de la red de proveedores? Tamaño del bloque = nº de empresas en el cluster."
          />

          <div className="grid grid-cols-3 gap-px bg-gray-100 border border-gray-100 rounded-xl overflow-hidden mb-4">
            <div className="bg-white px-4 py-4 text-center">
              <p className="text-lg font-black tabular-nums text-gray-900">{gds.communities.length}</p>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-400 mt-1">Comunidades detectadas</p>
              {communitySingletons > 0 && (
                <p className="text-gray-400 text-[10px] mt-0.5 tabular-nums">
                  {communitySingletons} de 1 empresa
                </p>
              )}
            </div>
            {[
              { label: "Tamaño medio",  value: communityAvgSize },
              { label: "Mayor clúster", value: `${largestCommunityPct}% de la red` },
            ].map((kpi) => (
              <div key={kpi.label} className="bg-white px-4 py-4 text-center flex flex-col items-center justify-center">
                <p className="text-lg font-black tabular-nums text-gray-900">{kpi.value}</p>
                <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-400 mt-1">{kpi.label}</p>
              </div>
            ))}
          </div>

          <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5">
            {(() => {
              const filtered = [...gds.communities]
                .filter((c) => c.total_empresas > 1)
                .sort((a, b) => b.total_empresas - a.total_empresas);
              const visible  = filtered.slice(0, 10);
              const hidden   = gds.communities.length - visible.length;
              return (
                <>
                  <TreemapChart
                    data={visible.map((c, i) => ({
                      name:      `Ecosistema ${String.fromCharCode(65 + i)}`,
                      size:      c.total_empresas,
                      subtitle:  `${c.total_empresas} empresas`,
                      companies: c.ejemplos_empresas ?? [],
                    }))}
                    height={Math.max(260, Math.min(visible.length * 30, 480))}
                  />
                  {hidden > 0 && (
                    <p className="text-gray-400 text-xs mt-3 text-center">
                      · {hidden} comunidad{hidden !== 1 ? "es" : ""} menor{hidden !== 1 ? "es" : ""} no mostrada{hidden !== 1 ? "s" : ""}
                    </p>
                  )}
                </>
              );
            })()}
          </div>
        </section>
      )}

      {/* ── PUNTOS ÚNICOS DE FALLO ───────────────────────────────── */}
      {hasFailPoints && (
        <section>
          <SectionLabel
            index={sectionIdx["fail"]}
            title="Puntos Únicos de Fallo"
            subtitle="¿Qué proveedores requieren auditoría estricta porque su caída paralizaría la red?"
          />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

            {gds.bottlenecks.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5">
                <p className="text-gray-700 font-semibold text-sm mb-1">Cuellos de Botella</p>
                <p className="text-gray-400 text-xs mb-4">
                  Nodos &ldquo;puente&rdquo; que conectan comunidades distintas — alta intermediación estructural.
                </p>
                <RankedBarList
                  rows={gds.bottlenecks.slice(0, PAGE)}
                  getPct={(r) => r.normalized_pct}
                  getLabel={(r) => `${r.normalized_pct.toFixed(2)}%`}
                  color="amber"
                />
                {gds.bottlenecks.length > PAGE && (
                  <div className="mt-4">
                    <ShowMoreButton total={gds.bottlenecks.length} onClick={() => setShowBottlenecks(true)} />
                  </div>
                )}
              </div>
            )}

            {gds.pagerank.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-5">
                <p className="text-gray-700 font-semibold text-sm mb-1">Titanes Sistémicos</p>
                <p className="text-gray-400 text-xs mb-4">
                  Proveedores de alto volumen y alta conectividad — estructuralmente &ldquo;demasiado grandes para caer&rdquo;.
                </p>
                <RankedBarList
                  rows={gds.pagerank.slice(0, PAGE)}
                  getPct={(r) => (r.pagerank_score / maxPagerank) * 100}
                  getLabel={(r) => `${((r.pagerank_score / maxPagerank) * 100).toFixed(1)}%`}
                  color="indigo"
                />
                {gds.pagerank.length > PAGE && (
                  <div className="mt-4">
                    <ShowMoreButton total={gds.pagerank.length} onClick={() => setShowPagerank(true)} />
                  </div>
                )}
              </div>
            )}

          </div>
        </section>
      )}

      {/* ── MODALS ───────────────────────────────────────────────── */}
      <SectionModal
        title="Cuellos de Botella — ranking completo"
        open={showBottlenecks}
        onClose={() => setShowBottlenecks(false)}
      >
        <RankedBarList
          rows={gds.bottlenecks}
          getPct={(r) => r.normalized_pct}
          getLabel={(r) => `${r.normalized_pct.toFixed(2)}%`}
          color="amber"
        />
      </SectionModal>

      <SectionModal
        title="Titanes Sistémicos — ranking completo"
        open={showPagerank}
        onClose={() => setShowPagerank(false)}
      >
        <RankedBarList
          rows={gds.pagerank}
          getPct={(r) => (r.pagerank_score / maxPagerank) * 100}
          getLabel={(r) => `${((r.pagerank_score / maxPagerank) * 100).toFixed(1)}%`}
          color="indigo"
        />
      </SectionModal>

    </div>
  );
}