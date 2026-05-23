// components/ui/DbStatusBadge.tsx
import React from "react";
import { ServerStackIcon } from "@heroicons/react/24/outline";

interface DbStatusBadgeProps {
  status: "checking" | "connected" | "disconnected";
}

export default function DbStatusBadge({ status }: DbStatusBadgeProps) {
  return (
    <div className={`hidden sm:flex px-4 py-2.5 rounded-xl border backdrop-blur-md items-center gap-3 shadow-lg transition-colors duration-500 ${
      status === 'connected' 
        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.15)]' 
        : status === 'disconnected' 
        ? 'bg-red-500/10 border-red-500/30 text-red-400 shadow-[0_0_15px_rgba(239,68,68,0.15)]'
        : 'bg-slate-500/10 border-slate-500/30 text-slate-400'
    }`}>
      <ServerStackIcon className="w-5 h-5 opacity-80" />
      <div className="flex flex-col">
        <span className="text-[10px] font-black uppercase tracking-widest opacity-70">Neo4j Status</span>
        <span className="text-sm font-semibold tracking-wide">
          {status === 'connected' ? 'Online / Activa' : status === 'disconnected' ? 'Offline / Inactiva' : 'Conectando...'}
        </span>
      </div>
      <div className={`w-2.5 h-2.5 rounded-full ml-1 ${
        status === 'connected' ? 'bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.8)]' :
        status === 'disconnected' ? 'bg-red-500' :
        'bg-slate-500 animate-pulse'
      }`} />
    </div>
  );
}