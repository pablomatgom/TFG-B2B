"use client";

import { Text } from "@tremor/react";

interface Props {
  text?: string;
}

export function LoadingState({ text = "Cargando..." }: Props) {
  return (
    <main className="p-10 max-w-7xl mx-auto flex flex-col items-center justify-center min-h-[60vh]">
      <div className="w-12 h-12 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mb-4" />
      <Text className="text-slate-400 animate-pulse">{text}</Text>
    </main>
  );
}

interface ErrorProps {
  title?: string;
  message?: string;
}

export function ErrorState({
  title = "Sin datos",
  message = "Ejecuta primero el pipeline desde /pipeline.",
}: ErrorProps) {
  return (
    <main className="p-10 max-w-7xl mx-auto text-center">
      <p className="text-red-400 text-xl font-semibold mb-2">{title}</p>
      <p className="text-slate-500 text-sm">{message}</p>
    </main>
  );
}