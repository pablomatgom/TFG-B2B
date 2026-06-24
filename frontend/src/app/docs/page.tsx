"use client";

import { useEffect, useState } from "react";
import {
  ServerIcon,
  CircleStackIcon,
  BeakerIcon,
  ChartBarIcon,
  CommandLineIcon,
  CodeBracketIcon,
  WrenchScrewdriverIcon,
} from "@heroicons/react/24/outline";
import Link from "next/link";

/* ── TOC sections ─────────────────────────────────────── */
const SECTIONS = [
  { id: "overview",   label: "Arquitectura",    icon: ServerIcon },
  { id: "data-model", label: "Modelo de Datos", icon: CircleStackIcon },
  { id: "pipeline",   label: "Pipeline & LFR",  icon: BeakerIcon },
  { id: "analytics",  label: "Guía Analítica",  icon: ChartBarIcon },
  { id: "api",        label: "API Reference",   icon: CommandLineIcon },
  { id: "cypher",     label: "Cypher Queries",  icon: CodeBracketIcon },
  { id: "setup",      label: "Instalación",     icon: WrenchScrewdriverIcon },
];

/* ── Helpers ──────────────────────────────────────────── */
function Code({ children }: { children: string }) {
  return (
    <pre className="bg-gray-900 text-gray-200 rounded-xl p-4 text-xs font-mono overflow-x-auto leading-relaxed border border-gray-800">
      <code>{children}</code>
    </pre>
  );
}

function SectionHeading({ id, title, subtitle }: { id: string; title: string; subtitle?: string }) {
  return (
    <div id={id} className="scroll-mt-8 mb-6">
      <h2 className="text-lg font-bold text-gray-900">{title}</h2>
      {subtitle && <p className="text-gray-500 text-sm mt-0.5">{subtitle}</p>}
      <div className="h-px bg-gray-100 mt-3" />
    </div>
  );
}

function SubHeading({ children }: { children: string }) {
  return <h3 className="text-sm font-semibold text-gray-800 mt-6 mb-3">{children}</h3>;
}

function PropRow({ name, type, desc }: { name: string; type: string; desc: string }) {
  return (
    <tr className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
      <td className="px-4 py-2 font-mono text-xs text-indigo-600 w-44 shrink-0">{name}</td>
      <td className="px-4 py-2 font-mono text-xs text-amber-600 w-24 shrink-0">{type}</td>
      <td className="px-4 py-2 text-xs text-gray-500">{desc}</td>
    </tr>
  );
}

function InfoBox({ color, children }: { color: "blue" | "amber"; children: React.ReactNode }) {
  const cls = color === "amber"
    ? "bg-amber-50 border-amber-200 text-amber-800"
    : "bg-blue-50 border-blue-200 text-blue-800";
  return (
    <div className={`mt-3 border rounded-lg px-4 py-3 text-xs ${cls}`}>{children}</div>
  );
}

/* ── Page ─────────────────────────────────────────────── */
export default function DocsPage() {
  const [active, setActive] = useState("overview");

  useEffect(() => {
    const observers: IntersectionObserver[] = [];
    SECTIONS.forEach(({ id }) => {
      const el = document.getElementById(id);
      if (!el) return;
      const obs = new IntersectionObserver(
        ([entry]) => { if (entry.isIntersecting) setActive(id); },
        { rootMargin: "-20% 0px -70% 0px" }
      );
      obs.observe(el);
      observers.push(obs);
    });
    return () => observers.forEach((o) => o.disconnect());
  }, []);

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <main className="p-8 max-w-7xl mx-auto">

      {/* ── Page header ──────────────────────── */}
      <header className="animate-fade-up pb-6 border-b border-gray-200 mb-8">
        <div className="flex items-center gap-2 text-[10px] font-bold tracking-[0.10em] uppercase text-gray-400 mb-2">
          <span>Sistema</span>
          <span>/</span>
          <span className="text-gray-500">Documentación</span>
        </div>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center shrink-0">
            <CodeBracketIcon className="w-4 h-4 text-indigo-600" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-gray-900 leading-none">Documentación Técnica</h1>
            <p className="text-xs text-gray-500 mt-1">Arquitectura, modelo de datos, pipeline LFR, API REST y queries Cypher</p>
          </div>
        </div>
      </header>

      <div className="flex gap-10">

        {/* ── Left TOC ─────────────────────────── */}
        <aside className="w-52 shrink-0 hidden lg:block">
          <div className="sticky top-8 space-y-0.5">
            <p className="text-[10px] font-bold tracking-[0.10em] uppercase text-gray-400 px-3 mb-3">
              Contenidos
            </p>
            {SECTIONS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => scrollTo(id)}
                className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-left transition-colors ${
                  active === id
                    ? "bg-indigo-50 text-indigo-700 font-semibold"
                    : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                }`}
              >
                <Icon className="w-3.5 h-3.5 shrink-0" />
                {label}
              </button>
            ))}
          </div>
        </aside>

        {/* ── Main content ─────────────────────── */}
        <div className="flex-1 min-w-0 space-y-14">

          {/* ══════════════════════════════════════
              1. ARQUITECTURA DEL SISTEMA
          ══════════════════════════════════════ */}
          <section>
            <SectionHeading
              id="overview"
              title="Arquitectura del Sistema"
              subtitle="Three-tier stack: Next.js · FastAPI · Neo4j GDS"
            />
            <p className="text-sm text-gray-600 mb-4 leading-relaxed">
              <strong>TFG-B2B</strong> es un sistema de inteligencia de red logística que combina
              generación de datos sintéticos basada en el modelo LFR (Lancichinetti-Fortunato-Radicchi)
              con analítica de grafos avanzada sobre Neo4j. El frontend consume una API REST que sirve
              resultados pre-computados de queries Cypher, más consultas live para el estado de la BD y
              el mapa geográfico.
            </p>

            <Code>{`┌─────────────────────────────────────────────────────┐
│  FRONTEND  (Next.js 14 · React · Tailwind)           │
│  localhost:3000                                       │
│  Dashboard · Analytics (8 tabs) · Pipeline · Docs    │
└──────────────────────┬──────────────────────────────┘
                       │  HTTP / REST  (JSON)
┌──────────────────────▼──────────────────────────────┐
│  BACKEND API  (FastAPI · Uvicorn)                    │
│  localhost:8000                                      │
│  /api/analytics/**  /api/dashboard/**               │
│  /api/pipeline/run  /api/health                     │
└──────────────────────┬──────────────────────────────┘
                       │  Bolt Driver  (neo4j-driver)
┌──────────────────────▼──────────────────────────────┐
│  NEO4J GRAPH DATABASE  (Docker · GDS Plugin)         │
│  localhost:7687 (Bolt)  ·  localhost:7474 (Browser) │
│  4 node labels · 7 relationship types               │
└─────────────────────────────────────────────────────┘`}</Code>

            <SubHeading>Flujo de datos</SubHeading>
            <ol className="text-sm text-gray-600 space-y-2 list-decimal list-inside leading-relaxed">
              <li><strong>Generación</strong> — El sintetizador LFR produce CSVs en <code className="text-xs bg-gray-100 px-1 rounded font-mono">data/synthetic/</code></li>
              <li><strong>Carga</strong> — <code className="text-xs bg-gray-100 px-1 rounded font-mono">Neo4jBulkLoader</code> ingiere los CSVs en lotes de 10 000 filas vía UNWIND + MERGE</li>
              <li><strong>Análisis</strong> — <code className="text-xs bg-gray-100 px-1 rounded font-mono">B2BGraphAnalyzer</code> ejecuta queries Cypher y exporta JSON a <code className="text-xs bg-gray-100 px-1 rounded font-mono">data/export/</code></li>
              <li><strong>API</strong> — FastAPI sirve los JSON pre-computados; <code className="text-xs bg-gray-100 px-1 rounded font-mono">/api/health</code> y <code className="text-xs bg-gray-100 px-1 rounded font-mono">/api/network/locations</code> consultan Neo4j en vivo</li>
              <li><strong>Frontend</strong> — Next.js consume la API y renderiza las visualizaciones analíticas</li>
            </ol>
          </section>

          {/* ══════════════════════════════════════
              2. MODELO DE DATOS
          ══════════════════════════════════════ */}
          <section>
            <SectionHeading
              id="data-model"
              title="Modelo de Datos"
              subtitle="4 tipos de nodo · 7 tipos de relación · Constraints únicos + índices automáticos"
            />

            <SubHeading>Nodos</SubHeading>

            {[
              {
                label: "Company",
                badge: "bg-blue-50 text-blue-700 border-blue-200",
                count: "300–1 000 por grafo",
                props: [
                  { name: "company_id",        type: "string",  desc: "Identificador único (UUID)" },
                  { name: "legal_name",         type: "string",  desc: "Razón social de la empresa" },
                  { name: "node_role",          type: "enum",    desc: "SUPPLIER | BUYER | HYBRID" },
                  { name: "region",             type: "string",  desc: "Comunidad Autónoma española" },
                  { name: "city",               type: "string",  desc: "Municipio (datos reales de España)" },
                  { name: "industry_code",      type: "string",  desc: "Código NACE sectorial" },
                  { name: "size_band",          type: "enum",    desc: "micro | pyme | mid | enterprise" },
                  { name: "baseline_revenue",   type: "float",   desc: "Facturación base anual (€)" },
                ],
              },
              {
                label: "Product",
                badge: "bg-emerald-50 text-emerald-700 border-emerald-200",
                count: "10–20× nº de empresas",
                props: [
                  { name: "product_id",                type: "string",  desc: "Identificador único" },
                  { name: "sku",                       type: "string",  desc: "Stock Keeping Unit" },
                  { name: "hs_code",                   type: "string",  desc: "Código arancelario HS" },
                  { name: "category",                  type: "string",  desc: "Categoría de producto" },
                  { name: "base_price",                type: "float",   desc: "Precio base unitario (€)" },
                  { name: "lead_time_baseline_days",   type: "int",     desc: "Plazo de entrega estándar (días)" },
                  { name: "criticality",               type: "enum",    desc: "LOW | MEDIUM | HIGH | CRITICAL" },
                  { name: "is_substitutable",          type: "boolean", desc: "¿Tiene producto sustituto?" },
                ],
              },
              {
                label: "Document",
                badge: "bg-violet-50 text-violet-700 border-violet-200",
                count: "80–100× nº de empresas",
                props: [
                  { name: "document_id",         type: "string",  desc: "Identificador único" },
                  { name: "doc_type",            type: "enum",    desc: "ORDER | INVOICE | SHIPMENT | CREDIT_NOTE" },
                  { name: "edi_standard",        type: "string",  desc: "Estándar EDI (EDIFACT, ANSI X12…)" },
                  { name: "issue_date",          type: "date",    desc: "Fecha de emisión" },
                  { name: "due_date",            type: "date",    desc: "Fecha de vencimiento" },
                  { name: "discrepancy_flag",    type: "boolean", desc: "¿Tiene discrepancia detectada?" },
                  { name: "gross_amount",        type: "float",   desc: "Importe bruto (€)" },
                  { name: "total_amount",        type: "float",   desc: "Importe total con impuestos (€)" },
                  { name: "payment_terms_days",  type: "int",     desc: "Plazo de pago acordado (días)" },
                  { name: "contract_type",       type: "enum",    desc: "FRAME | ANNUAL | SPOT" },
                  { name: "status",              type: "string",  desc: "Estado actual del documento" },
                  { name: "lead_time_days",      type: "int",     desc: "Plazo de entrega real registrado" },
                ],
              },
              {
                label: "TimeBucket",
                badge: "bg-amber-50 text-amber-700 border-amber-200",
                count: "1 por día con actividad",
                props: [
                  { name: "date",  type: "date", desc: "Fecha única — clave de partición temporal" },
                  { name: "year",  type: "int",  desc: "Año" },
                  { name: "month", type: "int",  desc: "Mes (1–12)" },
                  { name: "day",   type: "int",  desc: "Día (1–31)" },
                ],
              },
            ].map((node) => (
              <div key={node.label} className="mb-6">
                <div className="flex items-center gap-3 mb-2">
                  <span className={`px-2 py-0.5 rounded border text-xs font-mono font-semibold ${node.badge}`}>
                    {node.label}
                  </span>
                  <span className="text-gray-400 text-xs">{node.count}</span>
                </div>
                <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                  <table className="w-full">
                    <tbody>
                      {node.props.map((p) => <PropRow key={p.name} {...p} />)}
                    </tbody>
                  </table>
                </div>
              </div>
            ))}

            <SubHeading>Relaciones</SubHeading>
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-100">
                    {["Tipo", "Desde", "Hasta", "Semántica"].map((h, i) => (
                      <th key={h} className={`px-4 py-3 text-[11px] font-semibold uppercase tracking-wide text-gray-400 text-left ${i === 0 ? "w-36" : i < 3 ? "w-28" : ""}`}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {[
                    { type: "SUPPLIES",  from: "Company",  to: "Company",    desc: "Relación proveedor→comprador — define la topología de red" },
                    { type: "SELLS",     from: "Company",  to: "Product",    desc: "Empresa vende o suministra un producto" },
                    { type: "ISSUES",    from: "Company",  to: "Document",   desc: "Empresa emisora del documento EDI" },
                    { type: "SENT_TO",   from: "Document", to: "Company",    desc: "Documento dirigido a una empresa receptora" },
                    { type: "CONTAINS",  from: "Document", to: "Product",    desc: "Líneas de pedido o factura vinculadas a un producto" },
                    { type: "FULFILLS",  from: "Document", to: "Document",   desc: "Trazabilidad documental: factura cumple un pedido previo" },
                    { type: "Issue_on",  from: "Document", to: "TimeBucket", desc: "Agrupación temporal para series cronológicas" },
                  ].map((r) => (
                    <tr key={r.type} className="hover:bg-gray-50">
                      <td className="px-4 py-2.5 font-mono text-xs text-indigo-600 font-semibold">{r.type}</td>
                      <td className="px-4 py-2.5 text-xs text-gray-500">{r.from}</td>
                      <td className="px-4 py-2.5 text-xs text-gray-500">{r.to}</td>
                      <td className="px-4 py-2.5 text-xs text-gray-500">{r.desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <SubHeading>Constraints e índices</SubHeading>
            <Code>{`-- Constraints únicos (creados automáticamente en primera carga)
CREATE CONSTRAINT IF NOT EXISTS FOR (c:Company)    REQUIRE c.company_id  IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product)    REQUIRE p.product_id  IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document)   REQUIRE d.document_id IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (t:TimeBucket) REQUIRE t.date        IS UNIQUE;

-- Índices de consulta
CREATE INDEX IF NOT EXISTS FOR (c:Company)  ON (c.node_role);
CREATE INDEX IF NOT EXISTS FOR (c:Company)  ON (c.region);
CREATE INDEX IF NOT EXISTS FOR (c:Company)  ON (c.industry_code);
CREATE INDEX IF NOT EXISTS FOR (p:Product)  ON (p.criticality);
CREATE INDEX IF NOT EXISTS FOR (d:Document) ON (d.doc_type);
CREATE INDEX IF NOT EXISTS FOR (d:Document) ON (d.contract_type);`}</Code>
          </section>

          {/* ══════════════════════════════════════
              3. PIPELINE & LFR
          ══════════════════════════════════════ */}
          <section>
            <SectionHeading
              id="pipeline"
              title="Pipeline & Algoritmo LFR"
              subtitle="Generación sintética reproducible con el modelo Lancichinetti-Fortunato-Radicchi"
            />

            <p className="text-sm text-gray-600 mb-4 leading-relaxed">
              El modelo <strong>LFR</strong> genera redes con distribución de grado <em>power-law</em>
              y estructura de comunidades realista, reproduciendo propiedades observadas en redes
              logísticas B2B reales (hubs, clústeres sectoriales, nodos puente entre comunidades).
              Un único <code className="text-xs bg-gray-100 px-1 rounded font-mono">--seed</code> garantiza
              la reproducibilidad completa de todo el grafo.
            </p>

            <SubHeading>Parámetros LFR</SubHeading>
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm mb-6">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-100">
                    {["Parámetro CLI", "Default", "Descripción"].map((h) => (
                      <th key={h} className="px-4 py-3 text-[11px] font-semibold uppercase tracking-wide text-gray-400 text-left">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {[
                    { p: "--gamma",    d: "2.4",  desc: "Exponente power-law para distribución de grado. Valores altos → más hubs dominantes" },
                    { p: "--beta",     d: "1.8",  desc: "Exponente power-law para tamaño de comunidades. Valores altos → comunidades más pequeñas" },
                    { p: "--mu",       d: "0.30", desc: "Coeficiente de mezcla — fracción de aristas inter-comunidad (0=aisladas, 1=sin comunidades)" },
                    { p: "--min_comm", d: "6",    desc: "Tamaño mínimo de comunidad (nº de empresas)" },
                    { p: "--max_comm", d: "45",   desc: "Tamaño máximo de comunidad (nº de empresas)" },
                    { p: "--rows",     d: "300",  desc: "Número de empresas objetivo en el grafo generado" },
                    { p: "--seed",     d: "42",   desc: "Semilla aleatoria — garantiza grafos idénticos en re-ejecuciones" },
                  ].map((r) => (
                    <tr key={r.p} className="hover:bg-gray-50">
                      <td className="px-4 py-2.5 font-mono text-xs text-indigo-600">{r.p}</td>
                      <td className="px-4 py-2.5 font-mono text-xs text-amber-600">{r.d}</td>
                      <td className="px-4 py-2.5 text-xs text-gray-500">{r.desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <SubHeading>Fases del pipeline</SubHeading>
            <div className="space-y-3 mb-6">
              {[
                {
                  phase: "Fase 1", label: "Generación sintética", badge: "text-blue-600 bg-blue-50 border-blue-200",
                  output: "data/synthetic/*.csv",
                  steps: [
                    "companies_synthesizer.py → Empresas con topología LFR + municipios reales de España",
                    "rel_supplies_synthesizer.py → Aristas SUPPLIES con condiciones de acuerdo comercial",
                    "products_synthesizer.py → Productos con categorías HS y criticidad por proveedor",
                    "documents_synthesizer.py → Documentos EDI con distribución temporal y flags de discrepancia",
                    "rel_contains_synthesizer.py → Líneas de pedido/factura vinculadas a productos (CONTAINS)",
                  ],
                },
                {
                  phase: "Fase 2", label: "Carga bulk en Neo4j", badge: "text-emerald-600 bg-emerald-50 border-emerald-200",
                  output: "Neo4j graph poblado",
                  steps: [
                    "Neo4jBulkLoader crea constraints únicos e índices al primer arranque",
                    "Ingesta en lotes de 10 000 filas (configurable) — evita desbordamiento de memoria",
                    "Orden garantizado: Companies → SUPPLIES → Products → Documents → CONTAINS",
                    "Huérfanos ignorados: FULFILLS sin reference_id y Issue_on sin issue_date se omiten silenciosamente",
                  ],
                },
                {
                  phase: "Fase 3", label: "Análisis y exportación", badge: "text-violet-600 bg-violet-50 border-violet-200",
                  output: "data/export/*.json",
                  steps: [
                    "B2BGraphAnalyzer ejecuta 10+ queries Cypher de analítica sobre el grafo cargado",
                    "GDS: betweenness centrality (cuellos de botella) + Louvain (comunidades) + PageRank + WCC",
                    "Cada método exporta su resultado como JSON en data/export/ para servicio sin latencia",
                    "Artefactos de auditoría en data/processed/<step>_last_run.json con métricas de ejecución",
                  ],
                },
              ].map((p) => (
                <div key={p.phase} className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
                  <div className="flex items-center gap-3 mb-3">
                    <span className={`px-2 py-0.5 rounded border text-xs font-mono font-bold ${p.badge}`}>{p.phase}</span>
                    <span className="text-gray-800 font-semibold text-sm">{p.label}</span>
                    <span className="ml-auto font-mono text-xs text-gray-400 shrink-0">{p.output}</span>
                  </div>
                  <ul className="space-y-1.5">
                    {p.steps.map((s, i) => (
                      <li key={i} className="text-xs text-gray-500 flex gap-2">
                        <span className="text-indigo-400 shrink-0 mt-0.5">·</span>
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>

            <SubHeading>Comandos CLI</SubHeading>
            <Code>{`# Pipeline completo: genera, carga y analiza
python backend/main_cli.py all --rows 300 --clear-db --seed 42

# Sólo generación con parámetros LFR personalizados
python backend/main_cli.py generate --rows 500 --gamma 2.5 --beta 1.9 --mu 0.25

# Sólo carga (CSVs ya existen en data/synthetic/)
python backend/main_cli.py load --batch_size_loader 5000

# Sólo análisis (refresca todos los JSON en data/export/)
python backend/main_cli.py analyze

# Ayuda completa
python backend/main_cli.py generate -h`}</Code>
          </section>

          {/* ══════════════════════════════════════
              4. GUÍA ANALÍTICA
          ══════════════════════════════════════ */}
          <section>
            <SectionHeading
              id="analytics"
              title="Guía de Analítica"
              subtitle="Qué mide cada pestaña, sus KPIs y cómo interpretar los resultados"
            />
            <div className="space-y-3">
              {[
                {
                  tab: "Contratos", href: "/analytics?tab=0",
                  badge: "bg-purple-50 text-purple-700 border-purple-200",
                  sections: [
                    { title: "Perfil de Contratos de Red", desc: "Distribución FRAME / ANNUAL / SPOT de acuerdos activos, % de exclusividad, fiabilidad media de la red y antigüedad media de los contratos." },
                    { title: "Desglose por Proveedor", desc: "Tipos de contrato, tasa de exclusividad y plazo de pago medio por proveedor — permite identificar dependencias contractuales de alto riesgo." },
                  ],
                },
                {
                  tab: "Riesgo", href: "/analytics?tab=1",
                  badge: "bg-red-50 text-red-700 border-red-200",
                  sections: [
                    { title: "Concentración de Proveedores", desc: "% de aristas SUPPLIES controladas por los top-N proveedores. Un valor superior al 50% indica riesgo sistémico por dependencia extrema en la red." },
                    { title: "Scoring Compuesto", desc: "Puntuación de riesgo 0–10 por proveedor, combinando tasa de discrepancias, % de entregas tardías respecto al baseline y grado de suministro en el grafo." },
                    { title: "Fragilidad de Compradores", desc: "Compradores cuyo suministro está concentrado en un único proveedor — especialmente vulnerables ante fallos o disrupciones puntuales." },
                  ],
                },
                {
                  tab: "Discrepancias", href: "/analytics?tab=2",
                  badge: "bg-orange-50 text-orange-700 border-orange-200",
                  sections: [
                    { title: "Tasa de Error por Proveedor", desc: "Ratio facturas con discrepancy_flag=true sobre el total emitido (mínimo 5 facturas). Identifica proveedores con baja calidad documental EDI." },
                    { title: "Impacto Comercial", desc: "Comparación entre importe de pedido y total facturado por acuerdo — detecta sub-facturación y sobre-facturación sistemática por proveedor." },
                  ],
                },
                {
                  tab: "Lead Time", href: "/analytics?tab=3",
                  badge: "bg-amber-50 text-amber-700 border-amber-200",
                  sections: [
                    { title: "Cumplimiento por Categoría", desc: "Demora media real vs. baseline del producto por categoría HS. El % tardío indica cuántos envíos superaron el lead_time_baseline_days acordado." },
                  ],
                },
                {
                  tab: "Exposición", href: "/analytics?tab=4",
                  badge: "bg-yellow-50 text-yellow-700 border-yellow-200",
                  sections: [
                    { title: "Cartera de Crédito Activo", desc: "Top-15 proveedores por exposición total en euros (facturas en estado PENDING o PARTIAL) — riesgo de crédito acumulado en la red." },
                    { title: "Facturas Vencidas", desc: "Documentos cuya due_date ha pasado sin cambio de estado — exposición real a impago identificada sin necesidad de sistema de cobros." },
                  ],
                },
                {
                  tab: "Trazabilidad", href: "/analytics?tab=5",
                  badge: "bg-indigo-50 text-indigo-700 border-indigo-200",
                  sections: [
                    { title: "Cadena Documental Backward", desc: "Ruta INVOICE →[FULFILLS]→ ORDER hacia atrás, mostrando todos los documentos intermedios y saltos topológicos desde la factura al pedido original." },
                    { title: "Propagación Forward", desc: "Desde un pedido, todos los documentos de cumplimiento emitidos aguas abajo — permite detectar facturas duplicadas o inconsistentes sobre el mismo pedido." },
                  ],
                },
                {
                  tab: "GDS", href: "/analytics?tab=6",
                  badge: "bg-blue-50 text-blue-700 border-blue-200",
                  sections: [
                    { title: "Betweenness Centrality", desc: "Nodos por los que pasa más tráfico de caminos mínimos en la red — los «cuellos de botella» reales cuya caída desconectaría comunidades enteras." },
                    { title: "PageRank", desc: "Influencia relativa de cada empresa basada en la importancia de sus vecinos de suministro — un proveedor de un hub pesa más que uno de un nodo periférico." },
                    { title: "Louvain Community Detection", desc: "Clústeres de empresas con alta densidad de relaciones internas — revela mercados o sectores de suministro naturales emergentes de la topología LFR." },
                    { title: "Componentes Conexos (WCC)", desc: "Subgrafos completamente aislados del grafo principal — empresas o grupos sin ningún camino hacia la red mayoritaria." },
                  ],
                },
                {
                  tab: "Síntesis", href: "/analytics?tab=7",
                  badge: "bg-fuchsia-50 text-fuchsia-700 border-fuchsia-200",
                  sections: [
                    { title: "Riesgo Geográfico", desc: "Concentración de riesgo operativo por Comunidad Autónoma: fiabilidad media de proveedores, tasa de discrepancias y volumen total de facturas por región." },
                    { title: "Cruce Multidimensional", desc: "Tabla consolidada de proveedores y compradores con risk_score, importe vencido y volumen — visión única para auditoría estratégica de la red." },
                  ],
                },
              ].map((tab) => (
                <div key={tab.tab} className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
                  <div className="flex items-center gap-3 mb-3">
                    <span className={`px-2 py-0.5 rounded border text-xs font-mono font-bold ${tab.badge}`}>{tab.tab}</span>
                    <Link href={tab.href} className="text-indigo-500 text-xs hover:underline font-mono">
                      {tab.href} →
                    </Link>
                  </div>
                  <div className="space-y-2.5">
                    {tab.sections.map((s) => (
                      <div key={s.title}>
                        <p className="text-xs font-semibold text-gray-700">{s.title}</p>
                        <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{s.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* ══════════════════════════════════════
              5. API REFERENCE
          ══════════════════════════════════════ */}
          <section>
            <SectionHeading
              id="api"
              title="API Reference"
              subtitle="FastAPI en localhost:8000 — CORS configurado para localhost:3000"
            />

            <SubHeading>GET — Endpoints de lectura</SubHeading>
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm mb-6">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-100">
                    {["Endpoint", "Fuente de datos", "Pestaña"].map((h) => (
                      <th key={h} className="px-4 py-3 text-[11px] font-semibold uppercase tracking-wide text-gray-400 text-left">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {[
                    { ep: "GET /api/health",                              src: "Neo4j live",                       tab: "DbStatusBadge (sidebar)" },
                    { ep: "GET /api/network/locations",                   src: "Neo4j live",                       tab: "SpainMap (dashboard)" },
                    { ep: "GET /api/dashboard/macro",                     src: "macro_statistics.json",            tab: "/ (Visión Global)" },
                    { ep: "GET /api/analytics/risk",                      src: "risk_concentration.json",          tab: "Riesgo" },
                    { ep: "GET /api/analytics/risk/supplier-score",       src: "supplier_risk_score.json",         tab: "Riesgo" },
                    { ep: "GET /api/analytics/risk/buyer-fragility",      src: "buyer_fragility.json",             tab: "Riesgo" },
                    { ep: "GET /api/analytics/discrepancy-suppliers",     src: "discrepancy_by_supplier.json",     tab: "Discrepancias" },
                    { ep: "GET /api/analytics/risk/commercial-impact",    src: "commercial_impact.json",           tab: "Discrepancias" },
                    { ep: "GET /api/analytics/lead-time",                 src: "lead_time_compliance.json",        tab: "Lead Time" },
                    { ep: "GET /api/analytics/payment",                   src: "payment_exposure.json",            tab: "Exposición" },
                    { ep: "GET /api/analytics/risk/overdue",              src: "overdue_exposure.json",            tab: "Exposición" },
                    { ep: "GET /api/analytics/lineage/backward",          src: "data_lineage.json",                tab: "Trazabilidad" },
                    { ep: "GET /api/analytics/lineage/exact-paths",       src: "exact_paths.json",                 tab: "Trazabilidad" },
                    { ep: "GET /api/analytics/lineage/forward",           src: "forward_lineage.json",             tab: "Trazabilidad" },
                    { ep: "GET /api/analytics/gds",                       src: "bottlenecks.json + communities.json", tab: "GDS" },
                    { ep: "GET /api/analytics/risk/contracts",            src: "contract_profile.json",            tab: "Contratos" },
                    { ep: "GET /api/analytics/risk/contracts-detail",     src: "contract_detail.json",             tab: "Contratos" },
                    { ep: "GET /api/analytics/risk/geographic",           src: "geographic_risk.json",             tab: "Síntesis" },
                    { ep: "GET /api/analytics/risk/synthesis/suppliers",  src: "cross_suppliers.json",             tab: "Síntesis" },
                    { ep: "GET /api/analytics/risk/synthesis/buyers",     src: "cross_buyers.json",                tab: "Síntesis" },
                  ].map((r) => (
                    <tr key={r.ep} className="hover:bg-gray-50">
                      <td className="px-4 py-2 font-mono text-xs text-indigo-600 whitespace-nowrap">{r.ep}</td>
                      <td className="px-4 py-2 font-mono text-xs text-gray-400 whitespace-nowrap">{r.src}</td>
                      <td className="px-4 py-2 text-xs text-gray-500">{r.tab}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <SubHeading>POST — Acción de pipeline</SubHeading>
            <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
              <div className="flex items-center gap-3 mb-3">
                <span className="px-2 py-0.5 rounded border text-xs font-mono font-bold bg-green-50 text-green-700 border-green-200">POST</span>
                <code className="text-xs font-mono text-indigo-600">/api/pipeline/run</code>
                <span className="text-xs text-gray-400">— Dispara el pipeline ETL completo o parcial</span>
              </div>
              <Code>{`{
  "rows":               300,      // Nº de empresas objetivo
  "seed":               42,       // Semilla aleatoria (reproducibilidad)
  "gamma":              2.4,      // Exponente power-law de grado
  "beta":               1.8,      // Exponente power-law de comunidades
  "mu":                 0.30,     // Coeficiente de mezcla LFR
  "min_comm":           6,        // Tamaño mínimo de comunidad
  "max_comm":           45,       // Tamaño máximo de comunidad
  "batch_size_loader":  10000,    // Filas por lote de carga Neo4j
  "clear_db":           false,    // ¿Borrar BD antes de cargar?
  "run_generate":       true,     // Ejecutar fase de generación
  "run_load":           true,     // Ejecutar fase de carga
  "run_analyze":        true      // Ejecutar fase de análisis
}`}</Code>
            </div>
          </section>

          {/* ══════════════════════════════════════
              6. CYPHER QUERIES
          ══════════════════════════════════════ */}
          <section>
            <SectionHeading
              id="cypher"
              title="Cypher Queries & Graph Analytics"
              subtitle="Las queries que sustentan el motor analítico — ejecutables directamente en Neo4j Browser (localhost:7474)"
            />

            {[
              {
                title: "Top proveedores por grado de suministro",
                desc: "Identifica los hubs logísticos con mayor número de compradores directos en la red.",
                query: `MATCH (s:Company)-[:SUPPLIES]->(b:Company)
WHERE s.node_role IN ['SUPPLIER', 'HYBRID']
RETURN s.legal_name  AS proveedor,
       s.region       AS region,
       count(b)       AS compradores
ORDER BY compradores DESC
LIMIT 10`,
              },
              {
                title: "Trazabilidad backward: factura → pedido original",
                desc: "Reconstruye la cadena documental completa desde una factura hasta el pedido que la originó, con todos los documentos intermedios.",
                query: `MATCH path = (inv:Document {doc_type: 'INVOICE'})-[:FULFILLS*1..5]->(orig:Document)
WHERE NOT (orig)-[:FULFILLS]->()
WITH inv, orig,
     length(path)  AS saltos,
     nodes(path)   AS chain
RETURN inv.document_id    AS factura_id,
       orig.document_id   AS pedido_original,
       saltos,
       [n IN chain | {id: n.document_id, tipo: n.doc_type,
                      importe: n.gross_amount}] AS cadena_completa
ORDER BY inv.gross_amount DESC
LIMIT 50`,
              },
              {
                title: "Tasa de discrepancias por proveedor",
                desc: "Calidad documental: ratio de facturas con discrepancy_flag sobre el total emitido (mínimo 5 facturas).",
                query: `MATCH (s:Company)-[:ISSUES]->(inv:Document {doc_type: 'INVOICE'})
WITH s.legal_name                                           AS proveedor,
     count(inv)                                             AS total,
     sum(CASE WHEN inv.discrepancy_flag THEN 1 ELSE 0 END) AS flagged
WHERE total >= 5
RETURN proveedor,
       total,
       flagged,
       round(flagged * 100.0 / total, 2) AS discrepancy_rate_pct
ORDER BY discrepancy_rate_pct DESC
LIMIT 20`,
              },
              {
                title: "Exposición financiera activa por proveedor",
                desc: "Total de facturas pendientes de cobro y su importe acumulado por proveedor emisor.",
                query: `MATCH (s:Company)-[:ISSUES]->(inv:Document {doc_type: 'INVOICE'})
WHERE inv.status IN ['PENDING', 'PARTIAL']
RETURN s.legal_name                AS proveedor,
       count(inv)                  AS facturas_pendientes,
       sum(inv.total_amount)       AS exposicion_total_eur,
       avg(inv.payment_terms_days) AS plazo_medio_acordado_dias
ORDER BY exposicion_total_eur DESC
LIMIT 15`,
              },
              {
                title: "Detección de cuellos de botella (GDS Betweenness Centrality)",
                desc: "Nodos con mayor betweenness centrality — puntos de fallo único cuya eliminación fragmentaría la red de suministro.",
                query: `// Paso 1 — proyectar el subgrafo en memoria GDS
CALL gds.graph.project.cypher(
  'supply_graph',
  'MATCH (n:Company) RETURN id(n) AS id',
  'MATCH (a:Company)-[:SUPPLIES]->(b:Company)
   RETURN id(a) AS source, id(b) AS target'
)

// Paso 2 — calcular betweenness
CALL gds.betweenness.stream('supply_graph')
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS n, score
RETURN n.legal_name  AS empresa,
       n.node_role   AS rol,
       score         AS betweenness_score,
       round(score * 100.0 / max(score) OVER (), 2) AS normalized_pct
ORDER BY betweenness_score DESC
LIMIT 10`,
              },
              {
                title: "Comunidades Louvain",
                desc: "Agrupa empresas en comunidades con alta densidad interna — clústeres de mercado o sectorial natural emergente de la topología LFR.",
                query: `CALL gds.louvain.stream('supply_graph')
YIELD nodeId, communityId
WITH communityId,
     collect(gds.util.asNode(nodeId).legal_name) AS empresas
RETURN communityId,
       size(empresas) AS total_empresas,
       empresas[..5]  AS ejemplos_empresas
ORDER BY total_empresas DESC
LIMIT 10`,
              },
              {
                title: "PageRank — influencia relativa",
                desc: "Influencia de cada empresa ponderada por la importancia de sus vecinos de suministro directo.",
                query: `CALL gds.pageRank.stream('supply_graph', {
  maxIterations: 20,
  dampingFactor: 0.85
})
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS n, score
RETURN n.legal_name  AS empresa,
       n.node_role   AS rol,
       round(score, 6) AS pagerank_score
ORDER BY pagerank_score DESC
LIMIT 15`,
              },
              {
                title: "Componentes Conexos (WCC) — subgrafos aislados",
                desc: "Detecta empresas o grupos sin ninguna conexión con el componente principal de la red.",
                query: `CALL gds.wcc.stream('supply_graph')
YIELD nodeId, componentId
WITH componentId, count(*) AS size,
     collect(gds.util.asNode(nodeId).legal_name)[..3] AS ejemplos
RETURN componentId,
       size,
       ejemplos
ORDER BY size DESC
LIMIT 20`,
              },
            ].map((q, i) => (
              <div key={i} className="mb-8">
                <div className="flex items-baseline gap-3 mb-2">
                  <span className="text-indigo-400 font-mono text-xs shrink-0">{String(i + 1).padStart(2, "0")} /</span>
                  <div>
                    <p className="text-sm font-semibold text-gray-800">{q.title}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{q.desc}</p>
                  </div>
                </div>
                <Code>{q.query}</Code>
              </div>
            ))}
          </section>

          {/* ══════════════════════════════════════
              7. INSTALACIÓN LOCAL
          ══════════════════════════════════════ */}
          <section>
            <SectionHeading
              id="setup"
              title="Instalación & Configuración Local"
              subtitle="Requisitos: Docker Desktop · Python 3.10+ · Node.js 18+"
            />

            <SubHeading>1. Levantar Neo4j con Docker</SubHeading>
            <Code>{`# Primera vez — descarga imagen + plugin GDS (~pocos minutos)
docker compose up -d

# Arranques posteriores (instantáneo, datos persistidos en volumen)
docker compose up -d

# Parar (datos persisten)
docker compose down

# Borrar todos los datos del grafo y empezar de cero
docker compose down -v && docker compose up -d`}</Code>
            <InfoBox color="amber">
              <strong>Neo4j Browser:</strong>&nbsp;
              <code>http://localhost:7474</code> — usuario: <code>neo4j</code>, contraseña: <code>AdminUser1234</code>.
              Esperar 20–30 s en el primer arranque mientras el plugin GDS se inicializa.
            </InfoBox>

            <SubHeading>2. Variables de entorno</SubHeading>
            <p className="text-xs text-gray-500 mb-2">
              Copia <code className="bg-gray-100 px-1 rounded font-mono">.env.example</code> a <code className="bg-gray-100 px-1 rounded font-mono">.env</code>:
            </p>
            <Code>{`NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=AdminUser1234
NEO4J_DATABASE=neo4j`}</Code>

            <SubHeading>3. Instalar dependencias</SubHeading>
            <Code>{`# Backend Python
pip install -r requirements.txt

# Frontend Next.js
cd frontend && npm install`}</Code>

            <SubHeading>4. Arrancar el sistema completo</SubHeading>
            <Code>{`# Terminal 1 — Backend FastAPI (http://localhost:8000)
python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Frontend Next.js (http://localhost:3000)
cd frontend && npm run dev`}</Code>

            <SubHeading>5. Generar datos y ejecutar análisis</SubHeading>
            <Code>{`# Pipeline completo de principio a fin (recomendado en primer uso)
python backend/main_cli.py all --rows 300 --clear-db --seed 42

# Una vez completado, dashboard y pestañas analíticas estarán operativos`}</Code>

            <InfoBox color="blue">
              <strong>Puertos del sistema:</strong><br />
              · <code>localhost:3000</code> — Frontend Next.js (este dashboard)<br />
              · <code>localhost:8000</code> — Backend FastAPI (Swagger UI en <code>/docs</code>)<br />
              · <code>localhost:7474</code> — Neo4j Browser (consultas Cypher interactivas)<br />
              · <code>localhost:7687</code> — Neo4j Bolt (driver de la API)
            </InfoBox>

            <SubHeading>Solución de problemas frecuentes</SubHeading>
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-100">
                    {["Problema", "Solución"].map((h) => (
                      <th key={h} className="px-4 py-3 text-[11px] font-semibold uppercase tracking-wide text-gray-400 text-left">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {[
                    { prob: "Connection refused en puerto 7687",   sol: "docker compose up -d — verificar que Docker Desktop está activo" },
                    { prob: "Neo4j inasequible tras arrancar",     sol: "Esperar 20–30 s; el plugin GDS se inicializa en el primer boot" },
                    { prob: "Puerto 7687 ya en uso",               sol: "Cerrar Neo4j Desktop desde la bandeja del sistema" },
                    { prob: "ValueError: gamma/beta must be > 1.0", sol: "Reducir los valores LFR: --gamma 2.2 --beta 1.5" },
                    { prob: "Error de memoria durante la carga",   sol: "Reducir batch size: --batch_size_loader 5000" },
                    { prob: "Analytics muestra «Sin datos»",       sol: "Re-ejecutar: python backend/main_cli.py analyze" },
                    { prob: "Frontend POST a API falla (CORS)",    sol: "Verificar que la API corre en el puerto 8000 y el frontend en 3000" },
                    { prob: "GDS sin resultados (bottlenecks/communities)", sol: "Verificar que la imagen Docker incluye el plugin GDS (neo4j:enterprise o imagen customizada)" },
                  ].map((r, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-xs text-gray-700 font-medium">{r.prob}</td>
                      <td className="px-4 py-3 text-xs text-gray-500">{r.sol}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

        </div>
      </div>
    </main>
  );
}