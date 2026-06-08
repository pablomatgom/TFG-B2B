"use client";

import { useState } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";

const DOC_TYPE_HEX: Record<string, string> = {
  INVOICE:      "#26b5a0",
  ORDER:        "#60a5fa",
  DESADV:       "#a78bfa",
};
const FALLBACK_HEX = "#6366f1";

interface DocTypeDonutProps {
  data: { name: string; value: number }[];
}

interface ActiveSlice { name: string; value: number; color: string }

export default function DocTypeDonut({ data }: DocTypeDonutProps) {
  const total = data.reduce((s, d) => s + d.value, 0);
  const [active, setActive] = useState<ActiveSlice | null>(null);

  return (
    <div>
      {/* Chart */}
      <div className="relative select-none [&_path]:outline-none [&_svg]:outline-none">
        <ResponsiveContainer width="100%" height={180}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius="54%"
              outerRadius="78%"
              paddingAngle={2}
              dataKey="value"
              strokeWidth={0}
              onMouseEnter={(entry) =>
                setActive({
                  name:  entry.name as string,
                  value: entry.value as number,
                  color: DOC_TYPE_HEX[entry.name as string] ?? FALLBACK_HEX,
                })
              }
              onMouseLeave={() => setActive(null)}
            >
              {data.map((entry) => (
                <Cell
                  key={entry.name}
                  fill={DOC_TYPE_HEX[entry.name] ?? FALLBACK_HEX}
                  opacity={active && active.name !== entry.name ? 0.4 : 1}
                  style={{ transition: "opacity 0.15s" }}
                />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>

        {/* Center label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <p className="text-gray-900 text-2xl font-black tabular-nums leading-none">
            {Intl.NumberFormat("es").format(total)}
          </p>
          <p className="text-gray-400 text-[10px] font-medium mt-0.5">documentos</p>
        </div>
      </div>

      {/* Hover detail — replaces floating tooltip */}
      <div className="mt-2 h-9 flex items-center px-3 rounded-lg bg-gray-50 border border-gray-200 transition-all duration-150">
        {active ? (
          <>
            <span
              className="w-2 h-2 rounded-full shrink-0 mr-2"
              style={{ background: active.color }}
            />
            <span className="text-xs font-semibold text-gray-800 mr-2">{active.name}</span>
            <span className="text-xs text-gray-500 tabular-nums">
              {Intl.NumberFormat("es").format(active.value)} docs
            </span>
            <span className="ml-auto text-xs font-mono text-gray-400">
              {total > 0 ? ((active.value / total) * 100).toFixed(1) : "0"}%
            </span>
          </>
        ) : (
          <span className="text-[11px] text-gray-400">Pasa el cursor sobre un segmento</span>
        )}
      </div>

      {/* Legend */}
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5">
        {data.map((d) => (
          <div key={d.name} className="flex items-center gap-1.5 min-w-0">
            <div
              className="w-2 h-2 rounded-full shrink-0"
              style={{ background: DOC_TYPE_HEX[d.name] ?? FALLBACK_HEX }}
            />
            <span className="text-gray-500 text-[10px] truncate">{d.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}