"use client";

import { useRef } from "react";
import { AreaChart, Area, ResponsiveContainer, Tooltip } from "recharts";

interface Props {
  data: number[];
  color: string;
  id: string;
  onHoverValue?: (v: number | null) => void;
}

export default function MiniSparkline({ data, color, id, onHoverValue }: Props) {
  const cbRef = useRef(onHoverValue);
  cbRef.current = onHoverValue;

  if (!data.length) return null;
  const points = data.map((v, i) => ({ i, v }));

  return (
    <div className="w-full h-full" onMouseLeave={() => cbRef.current?.(null)}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={points} margin={{ top: 2, right: 0, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"   stopColor={color} stopOpacity={0.18} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <Tooltip
            content={({ active, payload }) => {
              const v = active && payload?.length ? (payload[0].value as number) : null;
              Promise.resolve().then(() => cbRef.current?.(v));
              return null;
            }}
            cursor={false}
            isAnimationActive={false}
          />
          <Area
            type="monotone"
            dataKey="v"
            stroke={color}
            strokeWidth={1.5}
            fill={`url(#${id})`}
            dot={false}
            activeDot={{ r: 2, fill: color, strokeWidth: 0 }}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}