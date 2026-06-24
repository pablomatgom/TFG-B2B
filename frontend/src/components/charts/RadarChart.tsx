"use client";

import { useState, useEffect, useMemo } from "react";
import {
  RadarChart as RechartsRadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export interface RadarSeries {
  name:   string;
  color:  string;
  /** One value (0–100) per axis, in the same order as the `axes` prop. */
  values: number[];
}

interface RadarChartProps {
  axes:         string[];
  series:       RadarSeries[];
  height?:      number;
  outerRadius?: string | number;
}

interface HoverData {
  label: string;
  items: { name: string; value: number; color: string }[];
}

/* Invisible bridge — Recharts clones this and injects active/payload/label */
function TooltipBridge({
  active, payload, label, onUpdate,
}: {
  active?:   boolean;
  payload?:  { name: string; value: number; color: string }[];
  label?:    string;
  onUpdate:  (d: HoverData | null) => void;
}) {
  useEffect(() => {
    onUpdate(
      active && payload?.length && label
        ? { label, items: payload.map((p) => ({ name: p.name, value: p.value, color: p.color })) }
        : null
    );
   
  }, [active, label, payload?.length]);
  return null;
}

export default function RadarChart({
  axes,
  series,
  height = 320,
  outerRadius = "65%",
}: RadarChartProps) {
  const [active,  setActive]  = useState<Set<string>>(() => new Set(series.map((s) => s.name)));
  const [hovered, setHovered] = useState<HoverData | null>(null);

  const toggle = (name: string) =>
    setActive((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        if (next.size === 1) return prev;
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });

  const visibleSeries = useMemo(() => series.filter((s) => active.has(s.name)), [series, active]);
  const fillOpacity   = visibleSeries.length <= 2 ? 0.22 : 0.13;

  const data = axes.map((axis, i) => ({
    subject: axis,
    ...Object.fromEntries(series.map((s) => [s.name, s.values[i] ?? 0])),
  }));

  return (
    <div className="flex gap-56 items-start justify-center w-full mx-auto">

      {/* ── Series toggles ─────────────────────────────── */}
      <div className="flex flex-col gap-1.5 shrink-0 pt-2">
        {series.map((s) => {
          const on = active.has(s.name);
          return (
            <button
              key={s.name}
              onClick={() => toggle(s.name)}
              className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg border text-xs font-medium transition-all duration-150 text-left"
              style={on
                ? { borderColor: s.color, color: s.color, backgroundColor: `${s.color}10` }
                : { borderColor: "#e5e7eb", color: "#9ca3af", backgroundColor: "#fff" }
              }
              title={on ? "Ocultar" : "Mostrar"}
            >
              <span
                className="w-2 h-2 rounded-full shrink-0 transition-colors duration-150"
                style={{ backgroundColor: on ? s.color : "#d1d5db" }}
              />
              {s.name}
            </button>
          );
        })}
        <p className="text-[10px] text-gray-400 mt-1 px-1">Pulsa para filtrar</p>
      </div>

      {/* ── Chart ──────────────────────────────────────── */}
      <div className="shrink-0" style={{ width: height }}>
        <ResponsiveContainer width="100%" height={height}>
          <RechartsRadarChart cx="50%" cy="50%" outerRadius={outerRadius} data={data}>
            <PolarGrid stroke="#e5e7eb" />
            <PolarAngleAxis
              dataKey="subject"
              tick={{ fontSize: 11, fill: "#6b7280" }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={false}
              axisLine={false}
            />

            {visibleSeries.map((s) => (
              <Radar
                key={s.name}
                name={s.name}
                dataKey={s.name}
                fill={s.color}
                fillOpacity={fillOpacity}
                stroke={s.color}
                strokeWidth={1.5}
                dot={false}
              />
            ))}

            <Tooltip
              content={<TooltipBridge onUpdate={setHovered} />}
            />
          </RechartsRadarChart>
        </ResponsiveContainer>
      </div>

      {/* ── Fixed info panel ───────────────────────────── */}
      <div className="w-44 shrink-0 pt-2">
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-3 min-h-[96px]">
          {hovered ? (
            <>
              <p className="text-[10px] font-bold uppercase tracking-wide text-gray-400 mb-2">
                {hovered.label}
              </p>
              <div className="space-y-1.5">
                {hovered.items
                  .filter((p) => active.has(p.name))
                  .map((p) => (
                    <div key={p.name} className="flex items-center justify-between gap-2">
                      <span className="flex items-center gap-1.5 min-w-0">
                        <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: p.color }} />
                        <span className="text-gray-500 text-[11px] truncate">{p.name}</span>
                      </span>
                      <span className="font-mono text-xs text-gray-700 shrink-0">{p.value.toFixed(1)}</span>
                    </div>
                  ))}
              </div>
            </>
          ) : (
            <p className="text-[11px] text-gray-400 leading-snug">
              Pasa el cursor sobre el gráfico para ver los valores por eje.
            </p>
          )}
        </div>
      </div>

    </div>
  );
}