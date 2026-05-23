"use client"; // <-- ¡Añade esta línea aquí arriba del todo!

import { Title, Text, Button, Grid } from "@tremor/react";
import Link from "next/link";
import { RocketLaunchIcon, ChartBarIcon } from "@heroicons/react/24/outline";
import dynamic from "next/dynamic";

// Ahora Next.js sí te dejará usar ssr: false
const SpainMap = dynamic(() => import("@/components/charts/SpainMap"), { 
  ssr: false,
  loading: () => (
    <div className="h-[450px] w-full flex items-center justify-center bg-[#1E212B] rounded-xl border border-slate-800">
      <div className="w-8 h-8 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
      <span className="ml-3 text-slate-400">Cargando motor geográfico...</span>
    </div>
  )
});

export default function WelcomePage() {
  return (
    <main className="p-6 md:p-12 max-w-7xl mx-auto space-y-12">
      
      {/* SECCIÓN HERO */}
      <section className="text-center space-y-6 pt-10">
        <Title className="text-6xl font-black text-white">
          Inteligencia de Grafos <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-600">
            B2B Supply Chain
          </span>
        </Title>
        <Text className="text-slate-400 text-xl max-w-2xl mx-auto">
          Generación y análisis de redes logísticas complejas mediante modelos LFR 
          y algoritmos de Graph Data Science sobre Neo4j.
        </Text>
      </section>

      {/* SECCIÓN DEL MAPA (Ahora cargado dinámicamente) */}
      <section className="animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-200">
        <SpainMap />
      </section>

    </main>
  );
}