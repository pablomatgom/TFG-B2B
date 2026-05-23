// components/forms/TopologySection.tsx
"use client";

import React from "react";
import { Card, Title, Text, NumberInput, Flex, Badge } from "@tremor/react";
import Slider from '@mui/material/Slider';
import { RocketLaunchIcon } from "@heroicons/react/24/outline";
import { PipelineFormData } from "@/types/pipeline"; // Ajusta la ruta de importación según tu proyecto

interface Props {
  formData: PipelineFormData;
  setFormData: React.Dispatch<React.SetStateAction<PipelineFormData>>;
}

export default function TopologySection({ formData, setFormData }: Props) {
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

                {/* Casilla Introducción Manual */}
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
                    if (Number.isNaN(val) || v === undefined) {
                      setFormData({...formData, seed_value: 1});
                    } else {
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
  );
}