"use client";

import { useMemo } from "react";
import {
  ScatterChart, Scatter, XAxis, YAxis, ZAxis,
  CartesianGrid, Tooltip, Legend, ReferenceLine,
  ResponsiveContainer, Label,
} from "recharts";

export interface BubblePoint {
  x:      number;
  y:      number;
  z:      number;
  label:  string;
  meta?:  Record<string, string | number>;
}

export interface BubbleSeries {
  name:  string;
  fill:  string;
  data:  BubblePoint[];
}

export interface ReferenceLineSpec {
  axis:   "x" | "y";
  value:  number;
  color:  string;
  label?: string;
}

interface BubbleChartProps {
  series:          BubbleSeries[];
  xLabel?:         string;
  yLabel?:         string;
  xFormatter?:     (v: number) => string;
  yFormatter?:     (v: number) => string;
  zRange?:         [number, number];
  referenceLines?: ReferenceLineSpec[];
  height?:         number;
  /** Custom extra rows rendered inside the tooltip below the default x/y/z lines. */
  tooltipExtra?:   (point: BubblePoint) => React.ReactNode;
}

 
function CustomTooltip({ active, payload, tooltipExtra }: any) {
  if (!active || !payload?.length) return null;
  const pt: BubblePoint = payload[0]?.payload;
  if (!pt) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-lg px-3 py-2.5 text-xs min-w-[160px]">
      <p className="font-semibold text-gray-900 mb-2 truncate">{pt.label}</p>
      {tooltipExtra && tooltipExtra(pt)}
    </div>
  );
}

export default function BubbleChart({
  series,
  xLabel,
  yLabel,
  xFormatter,
  yFormatter,
  zRange = [60, 380],
  referenceLines = [],
  height = 340,
  tooltipExtra,
}: BubbleChartProps) {
  // Auto-scale X domain: if no data sits near 0, start from slightly below
  // the minimum value instead of forcing Recharts to include 0 in the range.
  const r2 = (v: number) => Math.round(v * 100) / 100;

  const xDomain = useMemo((): [number, number | string] => {
    const allX = series.flatMap((s) => s.data.map((d) => d.x));
    if (allX.length === 0) return [0, "auto"];
    const minX  = allX.reduce((m, v) => Math.min(m, v), Infinity);
    const maxX  = allX.reduce((m, v) => Math.max(m, v), -Infinity);
    const range = maxX - minX || 1;
    const pad   = range * 0.08;
    const start = minX - pad > pad ? Math.max(0, r2(minX - pad)) : 0;
    return [start, r2(maxX + pad)];
  }, [series]);

  const yDomain = useMemo((): [number, number | string] => {
    const allY = series.flatMap((s) => s.data.map((d) => d.y));
    if (allY.length === 0) return [0, "auto"];
    const minY  = allY.reduce((m, v) => Math.min(m, v), Infinity);
    const maxY  = allY.reduce((m, v) => Math.max(m, v), -Infinity);
    const range = maxY - minY || 1;
    const pad   = range * 0.08;
    const start = minY - pad > pad ? Math.max(0, r2(minY - pad)) : 0;
    return [start, r2(maxY + pad)];
  }, [series]);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ScatterChart margin={{ top: 16, right: 24, bottom: 0, left: 24 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />

        <XAxis
          type="number"
          dataKey="x"
          domain={xDomain}
          tickFormatter={xFormatter}
          tick={{ fontSize: 11, fill: "#9ca3af" }}
          axisLine={{ stroke: "#e5e7eb" }}
          tickLine={false}
        >
          {xLabel && <Label value={xLabel} position="insideBottom" offset={-16} style={{ fontSize: 11, fill: "#9ca3af" }} />}
        </XAxis>

        <YAxis
          type="number"
          dataKey="y"
          domain={yDomain}
          tickFormatter={yFormatter}
          tick={{ fontSize: 11, fill: "#9ca3af" }}
          axisLine={{ stroke: "#e5e7eb" }}
          tickLine={false}
        >
          {yLabel && <Label value={yLabel} angle={-90} position="insideLeft" offset={0} style={{ fontSize: 11, fill: "#9ca3af", textAnchor: "middle" }} />}
        </YAxis>

        <ZAxis type="number" dataKey="z" range={zRange} />

        <Tooltip
          cursor={{ strokeDasharray: "3 3", stroke: "#e5e7eb" }}
          content={<CustomTooltip tooltipExtra={tooltipExtra} />}
        />

        <Legend
          content={() => (
            <div className="flex justify-center gap-5 pt-8">
              {series.map((s) => (
                <div key={s.name} className="flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: s.fill }} />
                  <span style={{ fontSize: 11, color: "#6b7280" }}>{s.name}</span>
                </div>
              ))}
            </div>
          )}
        />

        {referenceLines.map((rl, i) =>
          rl.axis === "x" ? (
            <ReferenceLine
              key={i}
              x={rl.value}
              stroke={rl.color}
              strokeDasharray="4 4"
              strokeWidth={1.5}
              label={rl.label ? { value: rl.label, fontSize: 9, fill: rl.color, position: "top" } : undefined}
            />
          ) : (
            <ReferenceLine
              key={i}
              y={rl.value}
              stroke={rl.color}
              strokeDasharray="4 4"
              strokeWidth={1.5}
              label={rl.label ? { value: rl.label, fontSize: 9, fill: rl.color, position: "right" } : undefined}
            />
          )
        )}

        {series.map((s) => (
          <Scatter
            key={s.name}
            name={s.name}
            data={s.data}
            fill={s.fill}
            fillOpacity={0.7}
          />
        ))}
      </ScatterChart>
    </ResponsiveContainer>
  );
}