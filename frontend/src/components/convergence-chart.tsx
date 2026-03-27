"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { Signal } from "@/lib/types";
import { agentMeta } from "./agent-avatar";

interface Props {
  signals: Signal[];
}

export function ConvergenceChart({ signals }: Props) {
  const phaseOrder = ["initial", "debate_r1", "debate_r2", "debate_r3"];
  const agentIds = [...new Set(signals.map((s) => s.agent_id))];

  const phaseMap: Record<string, Record<string, number>> = {};
  for (const s of signals) {
    if (!phaseMap[s.phase]) phaseMap[s.phase] = {};
    phaseMap[s.phase][s.agent_id] = s.confidence;
  }

  const phases = phaseOrder.filter((p) => p in phaseMap);
  if (phases.length < 2) {
    return (
      <p className="text-[13px] text-[var(--text-tertiary)] font-light">
        Not enough debate rounds to show convergence.
      </p>
    );
  }

  const data = phases.map((phase, i) => {
    const entry: Record<string, unknown> = { phase: `Round ${i}`, phaseLabel: phase };
    for (const agentId of agentIds) {
      entry[agentId] = phaseMap[phase]?.[agentId] ?? null;
    }
    return entry;
  });

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#091a15" />
        <XAxis
          dataKey="phase"
          tick={{ fill: "#5c7264", fontSize: 11, fontWeight: 500 }}
          axisLine={{ stroke: "#091a15" }}
          tickLine={false}
        />
        <YAxis
          domain={[0, 1]}
          tick={{ fill: "#5c7264", fontSize: 11, fontWeight: 500 }}
          tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
          axisLine={{ stroke: "#091a15" }}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "#0a1c18",
            border: "1px solid #13332a",
            borderRadius: 0,
            color: "#f2efe8",
            fontSize: 12,
            boxShadow: "0 8px 32px rgba(0,0,0,0.6)",
          }}
          formatter={(value: number) => `${(value * 100).toFixed(1)}%`}
        />
        <Legend wrapperStyle={{ fontSize: 11, fontWeight: 500 }} />
        {agentIds.map((agentId) => {
          const meta = agentMeta(agentId);
          return (
            <Line
              key={agentId}
              type="monotone"
              dataKey={agentId}
              name={meta.label}
              stroke={meta.color}
              strokeWidth={2}
              dot={{ r: 3.5, fill: meta.color, strokeWidth: 0 }}
              activeDot={{ r: 5.5, stroke: meta.color, strokeWidth: 2, fill: "#0a1c18" }}
              connectNulls
            />
          );
        })}
      </LineChart>
    </ResponsiveContainer>
  );
}
