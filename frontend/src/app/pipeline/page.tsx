// app/pipeline/page.tsx
"use client";

import { toast } from 'sonner';
import React, { useState, useEffect } from "react";
import { Title, Text, Flex } from "@tremor/react";
import { AdjustmentsHorizontalIcon } from "@heroicons/react/24/outline";

// Importación de componentes
import TopologySection from "@/components/forms/TopologySection";
import InfrastructureSection from "@/components/forms/InfrastructureSection";
import ConnectivitySection from "@/components/forms/ConnectivitySection";
import DbStatusBadge from "@/components/ui/DbStatusBadge"; // <-- Importamos nuestro nuevo UI Component
import { PipelineFormData, StatusState } from "@/types/pipeline";

export default function PipelinePage() {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<StatusState>({ type: null, msg: "" });
  
  // El estado y la lógica se quedan aquí porque la página los necesita para autorizar el pipeline
  const [dbStatus, setDbStatus] = useState<"checking" | "connected" | "disconnected">("checking");

  const [formData, setFormData] = useState<PipelineFormData>({
    rows: 200,
    avg_degree_supplies: 7,
    avg_degree_documents: 5,
    gamma: 2.4,
    beta: 1.8,
    mu: 0.30,
    min_comm: 6,
    max_comm: 45,
    avg_degree_products: 25,
    batch_size: 10000,
    clear_db: true,
    use_random_seed: true,
    seed_value: 42
  });

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); 

        const res = await fetch("http://127.0.0.1:8000/api/health", {
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);

        if (res.ok) {
          setDbStatus("connected");
        } else {
          setDbStatus("disconnected");
        }
      } catch (error) {
        setDbStatus("disconnected");
      }
    };

    checkConnection();
    // Revisamos cada 10 segundos para detectar cambios en el estado de la base de datos
    const intervalId = setInterval(checkConnection, 10000);
    return () => clearInterval(intervalId);
  }, []);

  const runPipeline = async () => {
    if (dbStatus === "disconnected") {
      toast.error("No se puede ejecutar. La base de datos Neo4j no está conectada.");
      return;
    }

    setLoading(true);
    try {
      const finalData = { ...formData, rows: Math.max(2, Number(formData.rows) || 2) };
      const response = await fetch("http://127.0.0.1:8000/api/pipeline/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(finalData),
      });
      
      if (response.ok) {
        toast.success('¡Pipeline completado con éxito!');
      } else {
        const data = await response.json();
        throw new Error(data.detail || "Error en el servidor");
      }
    } catch (error: any) {
      console.error("Error técnico del pipeline:", error);
      toast.error(
        <div className="flex flex-col gap-1">
          <span className="font-bold">Error de ejecución</span>
          <span className="text-slate-400 text-xs">Ha ocurrido un error al ejecutar el pipeline. Ponte en contacto con el Administrador.</span>
        </div>
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="p-8 bg-[#0B0E14] min-h-screen">
      {/* HEADER */}
      <div className="max-w-7xl mx-auto mb-10">
        <Flex justifyContent="between" alignItems="center">
          <div>
            <Title className="text-white text-4xl font-bold tracking-tight flex items-center gap-3">
              <span className="p-2 bg-cyan-500/10 rounded-xl border border-cyan-500/20 inline-flex">
                <AdjustmentsHorizontalIcon className="w-8 h-8 text-cyan-400" />
              </span>
              Control de Pipeline
            </Title>
            <Text className="text-slate-400 mt-2">Configuración del modelo sintético y orquestación Neo4j</Text>
          </div>

          {/* Usamos el componente modular pasando la prop status */}
          <DbStatusBadge status={dbStatus} />
        </Flex>
      </div>

      {/* GRID PRINCIPAL CON LOS 3 COMPONENTES */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
        <TopologySection formData={formData} setFormData={setFormData} />
        <InfrastructureSection 
          formData={formData} 
          setFormData={setFormData} 
          loading={loading} 
          status={status} 
          runPipeline={runPipeline} 
        />
        <ConnectivitySection formData={formData} setFormData={setFormData} />
      </div>
    </main>
  );
}