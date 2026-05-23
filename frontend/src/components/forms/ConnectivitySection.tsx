// components/forms/ConnectivitySection.tsx
"use client";

import React from "react";
import { Card, Title, Text, Flex, NumberInput } from "@tremor/react";
import { InformationCircleIcon } from "@heroicons/react/24/outline";
import { PipelineFormData } from "@/types/pipeline";

interface Props {
  formData: PipelineFormData;
  setFormData: React.Dispatch<React.SetStateAction<PipelineFormData>>;
}

export default function ConnectivitySection({ formData, setFormData }: Props) {
  return (
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
  );
}