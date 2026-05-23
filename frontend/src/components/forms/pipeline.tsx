"use client";

import React, { useState } from "react";
import {
  Card,
  Title,
  Text,
  Button,
  NumberInput,
  Switch,
  Flex,
  Badge,
} from "@tremor/react";
import Slider from '@mui/material/Slider';
import { 
  RocketLaunchIcon, 
  CircleStackIcon, 
  AdjustmentsHorizontalIcon,
  InformationCircleIcon
} from "@heroicons/react/24/outline";

export default function PipelinePage() {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{ type: "success" | "error" | null; msg: string }>({ type: null, msg: "" });

  const [formData, setFormData] = useState({
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

  const runPipeline = async () => {
    setLoading(true);
    setStatus({ type: null, msg: "" });
    try {
      const finalData = { ...formData, rows: Math.max(2, Number(formData.rows) || 2) };
      const response = await fetch("http://127.0.0.1:8000/api/pipeline/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(finalData),
      });
      const data = await response.json();
      if (response.ok) {
        setStatus({ type: "success", msg: "¡Pipeline completado con éxito!" });
      } else {
        throw new Error(data.detail || "Error en el servidor");
      }
    } catch (error: any) {
      setStatus({ type: "error", msg: error.message });
    } finally {
      setLoading(false);
    }
  };

  const getSliderStyle = (color: string) => ({
    color: color,
    height: 6,
    '& .MuiSlider-thumb': {
      height: 18,
      width: 18,
      backgroundColor: '#fff',
      border: `2px solid ${color}`,
      '&:hover': { boxShadow: `0 0 0 8px ${color}33` },
    },
    '& .MuiSlider-rail': { color: '#334155', opacity: 1 },
  });

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
        </Flex>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
        
        {/* SECCIÓN 1: TOPOLOGÍA */}
        <div className="lg:col-span-2 h-full">
          <Card className="bg-[#161B22] border-slate-800 shadow-2xl h-full">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-2 bg-pink-500/10 rounded-lg">
                <RocketLaunchIcon className="w-5 h-5 text-pink-500" />
              </div>
              <Title className="text-white text-xl tracking-wide font-semibold italic">Generador LFR (Topología)</Title>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
              
              {/* ESCALA DE RED */}
              <div className="lg:col-span-2">
                <div className="h-full flex flex-col justify-between bg-gradient-to-b from-[#0B0E14] to-[#080a0f] p-6 rounded-3xl border border-slate-800/60 shadow-2xl group hover:border-cyan-500/30 transition-all duration-500 relative overflow-hidden">
                  <div className="absolute -right-4 -top-4 w-24 h-24 bg-cyan-500/5 blur-3xl rounded-full group-hover:bg-cyan-500/10 transition-colors pointer-events-none" />

                  <div>
                    <Flex justifyContent="between" alignItems="center" className="mb-10">
                      <div className="space-y-1">
                        <Flex justifyContent="start" alignItems="center" className="gap-2">
                          <div className="w-1 h-3 bg-cyan-500 rounded-full shadow-[0_0_8px_rgba(6,182,212,0.8)]" />
                          <Text className="text-cyan-500/90 text-[10px] font-black uppercase tracking-[0.4em]">Numero de Compañias</Text>
                        </Flex>
                        <div className="flex items-baseline gap-3 mt-2">
                          <span className="text-white text-5xl font-extralight tracking-tighter tabular-nums leading-none">
                            {(Number(formData.rows) || 2).toLocaleString()}
                          </span>
                          <span className="text-slate-500 text-[11px] font-bold uppercase tracking-widest opacity-70">
                            Nodos 
                          </span>
                        </div>
                      </div>

                      {/* Botón Reset */}
                      <button 
                        type="button"
                        onClick={(e) => { e.preventDefault(); setFormData({...formData, rows: 200}); }}
                        className="p-2.5 rounded-xl bg-slate-900/80 text-slate-500 hover:text-cyan-400 hover:bg-cyan-500/10 border border-slate-800 transition-all active:scale-90 group/reset shadow-lg"
                        title="Resetear a 200"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 group-hover/reset:rotate-[-90deg] transition-transform duration-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                      </button>
                    </Flex>

                    {/* Casilla Introducción Manual (Siempre visible) */}
                    <div className="mb-6 space-y-3 p-4 bg-slate-950/40 rounded-2xl border border-slate-800/50 backdrop-blur-sm">
                      <Text className="text-[11px] text-slate-400 uppercase font-bold tracking-widest opacity-80">Valor manual:</Text>
                      <div className="relative">
                        <NumberInput 
                          min={2} 
                          enableStepper={true}
                          value={formData.rows} 
                          onValueChange={(v) => {
                            let val = Number(v);
                            if (Number.isNaN(val) || v === undefined) {
                              setFormData({...formData, rows: 2});
                            } else {
                              setFormData({...formData, rows: Math.max(2, val)});
                            }
                          }}
                          className="bg-slate-950/50 border-slate-800/80 text-cyan-400 text-sm h-11 rounded-xl focus:border-cyan-500/50 transition-all text-center font-mono shadow-inner [&_input::-webkit-outer-spin-button]:appearance-none [&_input::-webkit-inner-spin-button]:appearance-none [&_input]:[-moz-appearance:textfield]" 
                        />
                        <div className="absolute inset-x-0 -bottom-px h-px bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent" />
                      </div>
                    </div>
                  </div>

                  <div className="bg-slate-950/40 p-4 rounded-2xl border border-slate-800/40 backdrop-blur-sm">
                    <Text className="text-[11px] text-slate-400 uppercase font-black tracking-[0.25em] text-center mb-4 opacity-80">Ajuste rápido</Text>
                    <div className="flex flex-col gap-3">
                      <div className="flex gap-2">
                        {[10, 50, 100].map((value) => (
                          <button
                            type="button" key={`plus-${value}`}
                            onClick={() => setFormData({...formData, rows: (Number(formData.rows) || 2) + value})}
                            className="flex-1 flex flex-col items-center py-2.5 rounded-xl bg-slate-900/50 text-slate-400 border border-slate-800/60 hover:border-emerald-500/40 hover:bg-emerald-500/5 hover:text-emerald-300 transition-all active:scale-95 group/btn"
                          >
                            <span className="text-sm font-mono font-bold text-slate-200 group-hover/btn:text-emerald-400 transition-colors">+{value}</span>
                          </button>
                        ))}
                      </div>
                      <div className="flex gap-2">
                        {[10, 50, 100].map((value) => (
                          <button
                            type="button" key={`minus-${value}`}
                            onClick={() => setFormData({...formData, rows: Math.max(2, (Number(formData.rows) || 2) - value)})}
                            className="flex-1 flex flex-col items-center py-2.5 rounded-xl bg-slate-900/50 text-slate-400 border border-slate-800/60 hover:border-red-500/40 hover:bg-red-500/5 hover:text-red-300 transition-all active:scale-95 group/btn"
                          >
                            <span className="text-sm font-mono font-bold text-slate-200 group-hover/btn:text-red-400 transition-colors">-{value}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* SLIDERS LFR */}
              <div className="lg:col-span-3 space-y-5 relative">
                <div className="hidden lg:block absolute -left-4 top-4 bottom-4 w-px bg-gradient-to-b from-transparent via-slate-700/50 to-transparent" />

                <div className="p-4 rounded-2xl bg-gradient-to-br from-cyan-500/[0.04] to-transparent border border-slate-800/50 hover:border-cyan-500/20 transition-all">
                  <Flex className="mb-3">
                    <Text className="text-slate-300 font-bold text-[11px] uppercase tracking-widest">Mixing Parameter (μ)</Text>
                    <Badge className="rounded-md font-mono text-[11px]">{formData.mu}</Badge>
                  </Flex>
                  <Slider value={formData.mu} min={0.1} max={0.9} step={0.01} onChange={(_, v) => setFormData({...formData, mu: v as number})} sx={getSliderStyle('#22d3ee')} />
                </div>

                <div className="p-4 rounded-2xl bg-gradient-to-br from-pink-500/[0.04] to-transparent border border-slate-800/50 hover:border-pink-500/20 transition-all">
                  <Flex className="mb-3">
                    <Text className="text-slate-300 font-bold text-[11px] uppercase tracking-widest">Exponente Gamma (γ)</Text>
                    <Badge className="rounded-md font-mono text-[11px]">{formData.gamma}</Badge>
                  </Flex>
                  <Slider value={formData.gamma} min={1.1} max={4.0} step={0.1} onChange={(_, v) => setFormData({...formData, gamma: v as number})} sx={getSliderStyle('#f472b6')} />
                </div>

                <div className="p-4 rounded-2xl bg-gradient-to-br from-orange-500/[0.04] to-transparent border border-slate-800/50 hover:border-orange-500/20 transition-all">
                  <Flex className="mb-3">
                    <Text className="text-slate-300 font-bold text-[11px] uppercase tracking-widest">Exponente Beta (β)</Text>
                    <Badge className="rounded-md font-mono text-[11px]">{formData.beta}</Badge>
                  </Flex>
                  <Slider value={formData.beta} min={1.1} max={3.0} step={0.1} onChange={(_, v) => setFormData({...formData, beta: v as number})} sx={getSliderStyle('#fb923c')} />
                </div>

                {!formData.use_random_seed && (
                  <div className="p-4 rounded-2xl bg-gradient-to-r from-cyan-500/[0.04] to-transparent border border-cyan-800/20 animate-in fade-in slide-in-from-top-2 hover:border-cyan-500/20 transition-all">
                    <Text className="text-slate-300 font-bold text-[11px] uppercase tracking-widest mb-3">Valor de Semilla</Text>
                    <NumberInput 
                      min={1} 
                      enableStepper={true}
                      value={formData.seed_value} 
                      onValueChange={(v) => {
                        let val = Number(v);
                        // Si no es un número o está vacío, reseteamos a 1
                        if (Number.isNaN(val) || v === undefined) {
                          setFormData({...formData, seed_value: 1});
                        } else {
                          // Forzamos que el valor mínimo sea siempre 1
                          setFormData({...formData, seed_value: Math.max(1, val)});
                        }
                      }}
                      className="font-mono text-white bg-slate-950/80 border-slate-800 rounded-xl focus:border-cyan-500/50 [&_input::-webkit-outer-spin-button]:appearance-none [&_input::-webkit-inner-spin-button]:appearance-none [&_input]:[-moz-appearance:textfield]" 
                    />
                  </div>
                )}

              </div>
            </div>
          </Card>
        </div>

        {/* SECCIÓN 2: INFRAESTRUCTURA */}
        <div className="lg:col-span-1 h-full">
          <Card className="bg-gradient-to-b from-[#161B22] to-[#0B0E14] border-slate-800 shadow-2xl h-full flex flex-col relative overflow-hidden">
            {/* Brillo de fondo decorativo */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/10 blur-[100px] rounded-full pointer-events-none" />

            <div className="flex items-center gap-3 mb-8 relative z-10">
              <div className="p-2.5 bg-cyan-500/10 rounded-xl border border-cyan-500/20 shadow-[0_0_15px_rgba(6,182,212,0.15)]">
                <CircleStackIcon className="w-5 h-5 text-cyan-400" />
              </div>
              <Title className="text-white text-xl tracking-wide font-semibold italic">Infraestructura</Title>
            </div>

            <div className="space-y-5 flex-grow relative z-10">
              
              {/* ITEM 1: Purgar Grafo */}
              <div className="p-4 lg:p-5 rounded-2xl bg-slate-900/50 border border-slate-800/60 hover:border-cyan-500/30 transition-all flex justify-between items-center group">
                <div className="space-y-1">
                  <Text className="text-slate-200 font-bold text-xs uppercase tracking-widest">Purgar Grafo</Text>
                  <Text className="text-slate-500 text-[10px] uppercase font-semibold">Limpiar DB</Text>
                </div>
                {/* Interruptor personalizado de Tailwind */}
                <button
                  type="button"
                  onClick={() => setFormData({...formData, clear_db: !formData.clear_db})}
                  className={`${
                    formData.clear_db ? 'bg-cyan-500' : 'bg-slate-700'
                  } relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-300 ease-in-out shadow-inner focus:outline-none`}
                >
                  <span className={`${
                      formData.clear_db ? 'translate-x-5' : 'translate-x-0'
                    } pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-md transition duration-300 ease-in-out`} 
                  />
                </button>
              </div>

              {/* ITEM 2: Semilla Fija */}
              <div className="p-4 lg:p-5 rounded-2xl bg-slate-900/50 border border-slate-800/60 hover:border-cyan-500/30 transition-all flex justify-between items-center group">
                <div className="space-y-1">
                  <Text className="text-slate-200 font-bold text-xs uppercase tracking-widest">Semilla Fija</Text>
                  <Text className="text-slate-500 text-[10px] uppercase font-semibold">Reproducibilidad</Text>
                </div>
                {/* Interruptor personalizado (Color Cyan) */}
                <button
                  type="button"
                  onClick={() => setFormData({...formData, use_random_seed: !formData.use_random_seed})}
                  className={`${
                    formData.use_random_seed ? 'bg-cyan-500' : 'bg-slate-700'
                  } relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-300 ease-in-out shadow-inner focus:outline-none`}
                >
                  <span className={`${
                      formData.use_random_seed ? 'translate-x-5' : 'translate-x-0'
                    } pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-md transition duration-300 ease-in-out`} 
                  />
                </button>
              </div>

              {/* ITEM 3: Batch Size */}
              <div className="p-4 lg:p-5 rounded-2xl bg-[#0B0E14]/80 border border-slate-800/60 hover:border-slate-600 transition-colors">
                <Text className="text-slate-300 font-bold text-xs uppercase tracking-widest mb-3">Batch Size</Text>
                <NumberInput 
                  min={1} 
                  enableStepper={true}
                  value={formData.batch_size} 
                  onValueChange={(v) => {
                    let val = Number(v);
                    // Validación para evitar campos vacíos o valores no numéricos
                    if (Number.isNaN(val) || v === undefined) {
                      setFormData({...formData, batch_size: 1});
                    } else {
                      // Forzamos que el batch_size sea como mínimo 1
                      setFormData({...formData, batch_size: Math.max(1, val)});
                    }
                  }} 
                  className="font-mono text-white bg-slate-950/80 border-slate-800 rounded-xl focus:border-cyan-500/50 [&_input::-webkit-outer-spin-button]:appearance-none [&_input::-webkit-inner-spin-button]:appearance-none [&_input]:[-moz-appearance:textfield]" 
                />
              </div>
            </div>

            {/* BOTÓN Y STATUS */}
            <div className="mt-8 relative z-10">
              {status.type && (
                <div className={`p-4 rounded-xl mb-6 text-sm font-medium border backdrop-blur-sm flex items-center gap-3 ${
                  status.type === "success" 
                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" 
                  : "bg-red-500/10 text-red-400 border-red-500/20"
                }`}>
                  {/* Pequeño punto de luz animado junto al mensaje de estado */}
                  <div className={`w-2 h-2 rounded-full ${status.type === "success" ? "bg-emerald-400" : "bg-red-400"} animate-pulse`} />
                  {status.msg}
                </div>
              )}
              
              <Button 
                size="xl" 
                className="w-full py-5 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 border-none shadow-[0_0_20px_rgba(8,145,178,0.3)] hover:shadow-[0_0_30px_rgba(8,145,178,0.5)] transition-all text-lg font-bold tracking-wide rounded-xl group" 
                loading={loading} 
                onClick={runPipeline} 
                icon={RocketLaunchIcon}
              >
                <span className="group-hover:translate-x-1 transition-transform">EJECUTAR PIPELINE</span>
              </Button>
            </div>
          </Card>
        </div>

        {/* SECCIÓN 3: CONECTIVIDAD MEDIA */}
        <div className="lg:col-span-3">
          <Card className="bg-[#161B22] border-slate-800 shadow-2xl relative overflow-hidden">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-32 bg-indigo-500/5 blur-[100px] pointer-events-none" />

            <div className="flex items-center gap-3 mb-8 relative z-10">
              <div className="p-2.5 bg-indigo-500/10 rounded-xl border border-indigo-500/20 shadow-[0_0_15px_rgba(99,102,241,0.15)]">
                <InformationCircleIcon className="w-5 h-5 text-indigo-400" />
              </div>
              <div>
                <Title className="text-white text-xl tracking-wide font-semibold italic">Conectividad Media</Title>
                <Text className="text-slate-400 text-sm mt-1">Parámetros de relación por tipo de arista</Text>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 relative z-10">
              {(["supplies", "documents", "products"] as const).map((key) => {
                // Definimos las claves dinámicas correctamente para TS
                const dataKey = `avg_degree_${key}` as keyof typeof formData;
                
                const styles = {
                  supplies: "from-blue-500/[0.04] hover:border-blue-500/30",
                  documents: "from-purple-500/[0.04] hover:border-purple-500/30",
                  products: "from-emerald-500/[0.04] hover:border-emerald-500/30"
                }[key];

                return (
                  <div key={key} className={`p-6 rounded-2xl bg-gradient-to-br ${styles} to-transparent border border-slate-800/50 transition-all duration-300 group`}>
                    <Flex className="mb-5">
                      <Text className="text-slate-400 text-xs uppercase font-black tracking-widest group-hover:text-slate-300 transition-colors">{key}</Text>
                    </Flex>
                    <div className="relative">
                      <NumberInput 
                        min={1}
                        enableStepper={true}
                        value={formData[dataKey] as number} 
                        onValueChange={(v) => {
                          let val = Number(v);
                          if (Number.isNaN(val) || v === undefined) {
                            setFormData({...formData, [dataKey]: 1});
                          } else {
                            setFormData({...formData, [dataKey]: Math.max(1, val)});
                          }
                        }}
                        className="bg-slate-950/60 border-slate-800/80 text-white font-mono text-sm h-12 rounded-xl focus:border-indigo-500/50 transition-all shadow-inner [&_input::-webkit-outer-spin-button]:appearance-none [&_input::-webkit-inner-spin-button]:appearance-none [&_input]:[-moz-appearance:textfield]" 
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>

      </div>
    </main>
  );
}