"use client";

import {
  FunnelChart as RechartsFunnelChart,
  Funnel,
  LabelList,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export interface FunnelSegment {
  name:  string;
  value: number;
  fill:  string;
}

interface FunnelChartProps {
  data:     FunnelSegment[];
  height?:  number;
  caption?: string;
  /** Formatter for the center value label inside each segment. */
  valueFormatter?: (value: number) => string;
}

 
function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const seg: FunnelSegment = payload[0]?.payload;
  if (!seg) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-lg px-3 py-2.5 text-xs">
      <div className="flex items-center gap-2 mb-0.5">
        <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: seg.fill }} />
        <span className="font-semibold text-gray-900">{seg.name}</span>
      </div>
      <p className="text-gray-500 font-mono">{seg.value.toLocaleString("es-ES")} unidades</p>
    </div>
  );
}

export default function FunnelChart({
  data,
  height = 180,
  caption,
  valueFormatter,
}: FunnelChartProps) {
  const sorted = [...data].sort((a, b) => b.value - a.value);
  const fmt = (v: unknown) =>
    valueFormatter ? valueFormatter(v as number) : (v as number).toLocaleString("es-ES");

  return (
    <div>
      <ResponsiveContainer width="100%" height={height}>
        <RechartsFunnelChart>
          <Funnel dataKey="value" data={sorted} isAnimationActive>
            <LabelList
              position="center"
              fill="white"
              fontSize={13}
              fontWeight={700}
              formatter={fmt}
            />
            <LabelList
              position="right"
              dataKey="name"
              fill="#374151"
              fontSize={11}
            />
          </Funnel>
          <Tooltip content={<CustomTooltip />} />
        </RechartsFunnelChart>
      </ResponsiveContainer>

      {caption && (
        <p className="text-gray-400 text-xs text-center mt-1">{caption}</p>
      )}
    </div>
  );
}