"use client";

import { useRef, useState } from "react";
import {
  ResponsiveContainer,
  AreaChart as RechAreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechTooltip,
} from "recharts";

interface TemporalAreaChartProps {
  data: { date: string; documents: number; flagged?: number }[];
}

interface ActivePoint {
  label:     string;
  documents: number;
  flagged:   number;
}

const RANGES = [
  { label: "6M",   months: 6    },
  { label: "1A",   months: 12   },
  { label: "2A",   months: 24   },
  { label: "Todo", months: null },
] as const;

type RangeLabel = typeof RANGES[number]["label"];

export default function TemporalAreaChart({ data }: TemporalAreaChartProps) {
  const [range, setRange]   = useState<RangeLabel>("Todo");
  const [active, setActive] = useState<ActivePoint | null>(null);
  const activeKey = useRef<string | null>(null);

  const selectedMonths = RANGES.find((r) => r.label === range)!.months;
  const filteredData   = selectedMonths ? data.slice(-selectedMonths) : data;
  const hasFlagged     = filteredData.some((r) => (r.flagged ?? 0) > 0);

  return (
    <div>
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4 mb-4 flex-wrap">
        {/* Inline legend */}
        <div className="flex items-center gap-5 text-[11px] text-gray-400">
          <div className="flex items-center gap-1.5">
            <span className="inline-block w-4 h-[2px] bg-[#26b5a0] rounded" />
            Total documentos
          </div>
          {hasFlagged && (
            <div className="flex items-center gap-1.5">
              <span className="inline-block w-4 h-[2px] bg-amber-400 rounded opacity-80" />
              Con discrepancia
            </div>
          )}
        </div>

        {/* Range pills */}
        <div className="flex items-center gap-1 p-1 bg-gray-100 border border-gray-200 rounded-lg">
          {RANGES.map((r) => (
            <button
              key={r.label}
              onClick={() => { setRange(r.label); setActive(null); }}
              className={`px-2.5 py-1 text-[11px] font-semibold rounded-md transition-all duration-150 ${
                range === r.label
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-400 hover:text-gray-600"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart + fixed left tooltip */}
      <div
        className="relative"
        onMouseLeave={() => { activeKey.current = null; setActive(null); }}
      >
        {/* Fixed info box — always top-left, only visible on hover */}
        {active && (
          <div className="absolute left-1 top-0 z-10 pointer-events-none">
            <div className="bg-white border border-gray-200 rounded-lg shadow-sm px-3 py-2 text-xs min-w-[140px]">
              <p className="text-gray-400 font-mono mb-1">{active.label}</p>
              <p className="font-semibold text-gray-900">
                {Intl.NumberFormat("es").format(active.documents)} docs
              </p>
              {active.flagged > 0 && (
                <p className="text-amber-600 mt-0.5">
                  {Intl.NumberFormat("es").format(active.flagged)} irregulares
                </p>
              )}
            </div>
          </div>
        )}

        <ResponsiveContainer width="100%" height={272}>
          <RechAreaChart
            data={filteredData}
            margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id="areaGradDocs" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#26b5a0" stopOpacity={0.70} />
                <stop offset="95%" stopColor="#26b5a0" stopOpacity={0.08} />
              </linearGradient>
            </defs>

            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fill: "#9ca3af", fontSize: 11 }}
              axisLine={false} tickLine={false} tickMargin={8}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fill: "#9ca3af", fontSize: 11 }}
              axisLine={false} tickLine={false} tickMargin={8}
              tickFormatter={(n: number) =>
                Intl.NumberFormat("es", { notation: "compact" }).format(n)
              }
            />

            <RechTooltip
              content={({ active: a, payload, label }) => {
                if (a && payload?.length) {
                  const key = label as string;
                  if (key !== activeKey.current) {
                    activeKey.current = key;
                    const docs    = payload.find((p) => p.dataKey === "documents")?.value as number ?? 0;
                    const flagged = payload.find((p) => p.dataKey === "flagged")?.value as number ?? 0;
                    setActive({ label: key, documents: docs, flagged });
                  }
                }
                return null;
              }}
              cursor={{ stroke: "#26b5a0", strokeWidth: 1, strokeDasharray: "4 2" }}
              isAnimationActive={false}
            />

            <Area
              type="monotone"
              dataKey="documents"
              stroke="#26b5a0"
              strokeWidth={2}
              fill="url(#areaGradDocs)"
              dot={false}
              activeDot={{ r: 4, fill: "#26b5a0", stroke: "#fff", strokeWidth: 2 }}
            />

            {hasFlagged && (
              <Area
                type="monotone"
                dataKey="flagged"
                stroke="#f59e0b"
                strokeWidth={1.5}
                strokeDasharray="4 2"
                fill="none"
                dot={false}
                activeDot={{ r: 3, fill: "#f59e0b", strokeWidth: 1 }}
              />
            )}
          </RechAreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}