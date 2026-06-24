"use client";

import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

export interface BarChartProps {
   
  data:             Record<string, any>[];
  index:            string;
  category:         string;
  valueFormatter?:  (value: number) => string;
  colorFn?:         (value: number) => string;
  color?:           string;
  layout?:          "horizontal" | "vertical";
  yAxisWidth?:      number;
  rowHeight?:       number;
  className?:       string;
}

const DEFAULT_COLOR = "#6366f1";

function TruncatedTick({ x, y, payload, maxWidth, fontSize }: {
  x?: number | string; y?: number | string; payload?: { value: string }; maxWidth: number; fontSize: number;
}) {
  const text     = payload?.value ?? "";
  const charPx   = fontSize * 0.58;
  const maxChars = Math.floor(maxWidth / charPx);
  const display  = text.length > maxChars ? text.slice(0, maxChars - 1) + "…" : text;
  return (
    <g transform={`translate(${Number(x)},${Number(y)})`}>
      <text x={0} y={0} dy={4} textAnchor="end" fill="#6b7280" fontSize={fontSize}>
        {display}
      </text>
    </g>
  );
}

export default function BarChart({
  data,
  index,
  category,
  valueFormatter = (v) => String(v),
  colorFn,
  color = DEFAULT_COLOR,
  layout = "vertical",
  yAxisWidth = 140,
  rowHeight = 26,
  className = "h-64",
}: BarChartProps) {
  const isVertical   = layout === "vertical";
  const tickFontSize = Math.max(9, Math.min(12, Math.round(rowHeight * 0.5)));

  const containerHeight = isVertical
    ? Math.max(data.length * rowHeight, 100)
    : undefined;

  return (
    <div className={isVertical ? undefined : className} style={isVertical ? { height: containerHeight } : undefined}>
      <ResponsiveContainer width="100%" height={containerHeight ?? 256} minWidth={1}>
        <RechartsBarChart
          data={data}
          layout={layout}
          margin={{ top: 2, right: 16, bottom: 2, left: 0 }}
          barCategoryGap="25%"
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#f0f0f0"
            horizontal={isVertical}
            vertical={!isVertical}
          />

          {isVertical ? (
            <>
              <YAxis
                type="category"
                dataKey={index}
                width={yAxisWidth}
                interval={0}
                tick={(props) => <TruncatedTick {...props} maxWidth={yAxisWidth} fontSize={tickFontSize} />}
                axisLine={false}
                tickLine={false}
                tickMargin={8}
              />
              <XAxis
                type="number"
                tick={{ fill: "#9ca3af", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                tickMargin={8}
                tickFormatter={valueFormatter}
              />
            </>
          ) : (
            <>
              <XAxis
                type="category"
                dataKey={index}
                tick={{ fill: "#6b7280", fontSize: 12 }}
                axisLine={false}
                tickLine={false}
                tickMargin={8}
              />
              <YAxis
                type="number"
                tick={{ fill: "#9ca3af", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                tickMargin={8}
                tickFormatter={valueFormatter}
              />
            </>
          )}

          <Tooltip
            cursor={{ fill: "rgba(0,0,0,0.04)" }}
            formatter={(value) => [valueFormatter(value as number), category]}
            contentStyle={{
              background: "#fff",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
              fontSize: "12px",
              color: "#111827",
              boxShadow: "0 4px 6px -1px rgba(0,0,0,0.07)",
            }}
            labelStyle={{ color: "#6b7280", marginBottom: 4 }}
            isAnimationActive={false}
          />

          <Bar dataKey={category} radius={[0, 4, 4, 0]} isAnimationActive={false}>
            {data.map((entry, i) => (
              <Cell
                key={i}
                fill={colorFn ? colorFn(entry[category] as number) : color}
              />
            ))}
          </Bar>
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  );
}