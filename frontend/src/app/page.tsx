"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import {
  ChartBarIcon,
  BeakerIcon,
  AdjustmentsHorizontalIcon,
  ArrowRightIcon,
} from "@heroicons/react/24/outline";

const SpainMap = dynamic(() => import("@/components/charts/SpainMap"), {
  ssr: false,
  loading: () => (
    <div className="h-[450px] w-full flex items-center justify-center bg-[#1E212B] rounded-xl border border-slate-800">
      <div className="w-8 h-8 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin" />
      <span className="ml-3 text-slate-400">Cargando motor geográfico...</span>
    </div>
  ),
});

const FEATURES = [
  {
    title: "Dashboard",
    href: "/dashboard",
    icon: ChartBarIcon,
    accent: "border-blue-500/30 hover:border-blue-500/60",
    iconBg: "bg-blue-500/10",
    iconColor: "text-blue-400",
    description:
      "KPIs macro de la red, distribución temporal de documentos y mapa geográfico de empresas activas.",
  },
  {
    title: "Analítica Avanzada",
    href: "/analytics",
    icon: BeakerIcon,
    accent: "border-violet-500/30 hover:border-violet-500/60",
    iconBg: "bg-violet-500/10",
    iconColor: "text-violet-400",
    description:
      "Riesgo de concentración, tasa de discrepancias, lead time compliance y exposición financiera por proveedor.",
  },
  {
    title: "Pipeline",
    href: "/pipeline",
    icon: AdjustmentsHorizontalIcon,
    accent: "border-cyan-500/30 hover:border-cyan-500/60",
    iconBg: "bg-cyan-500/10",
    iconColor: "text-cyan-400",
    description:
      "Configura parámetros LFR, lanza la generación sintética y carga el grafo en Neo4j con un clic.",
  },
];

export default function WelcomePage() {
  return (
    <main className="p-6 md:p-12 max-w-7xl mx-auto space-y-14">

      {/* HERO */}
      <section className="text-center space-y-6 pt-10">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-cyan-500/20 bg-cyan-500/5 text-cyan-400 text-xs font-medium tracking-wide uppercase mb-2">
          TFG — Master&apos;s Thesis · Neo4j + LFR Graphs
        </div>
        <h1 className="text-5xl md:text-6xl font-black text-white leading-tight">
          Inteligencia de Grafos<br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
            B2B Supply Chain
          </span>
        </h1>
        <p className="text-slate-400 text-lg md:text-xl max-w-2xl mx-auto">
          Generación y análisis de redes logísticas complejas mediante modelos LFR
          y algoritmos de Graph Data Science sobre Neo4j.
        </p>
      </section>

      {/* FEATURE CARDS */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {FEATURES.map((f) => (
          <Link key={f.href} href={f.href}>
            <div
              className={`group h-full bg-[#1E212B] rounded-2xl border ${f.accent} p-6 flex flex-col gap-4 transition-all duration-200 cursor-pointer hover:bg-[#23273A] hover:shadow-lg hover:shadow-black/30`}
            >
              <div className={`w-12 h-12 ${f.iconBg} rounded-xl flex items-center justify-center`}>
                <f.icon className={`w-6 h-6 ${f.iconColor}`} />
              </div>
              <div className="flex-1">
                <p className="text-white font-semibold text-lg">{f.title}</p>
                <p className="text-slate-400 text-sm mt-1 leading-relaxed">{f.description}</p>
              </div>
              <div className={`flex items-center gap-1 text-xs font-medium ${f.iconColor} opacity-0 group-hover:opacity-100 transition-opacity`}>
                Ir a {f.title} <ArrowRightIcon className="w-3 h-3" />
              </div>
            </div>
          </Link>
        ))}
      </section>

      {/* SPAIN MAP */}
      <section className="animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-200">
        <div className="mb-4">
          <p className="text-white font-semibold text-lg">Distribución Geográfica</p>
          <p className="text-slate-400 text-sm">Concentración de empresas activas en la red generada.</p>
        </div>
        <SpainMap />
      </section>

    </main>
  );
}