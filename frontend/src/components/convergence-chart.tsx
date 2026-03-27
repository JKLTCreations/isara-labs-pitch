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
  // Group signals by phase to track confidence evolution
  const phaseOrder = ["initial", "debate_r1", "debate_r2", "debate_r3"];
  const agentIds = [...new Set(signals.map((s) => s.agent_id))];

  // Build chart data: one entry per phase, with each agent's confidence
  const phaseMap: Record<string, Record<string, number>> = {};
  for (const s of signals) {
    if (!phaseMap[s.phase]) phaseMap[s.phase] = {};
    phaseMap[s.phase][s.agent_id] = s.confidence;
  }

  const phases = phaseOrder.filter((p) => p in phaseMap);
  if (phases.length < 2) {
    return (
      <p className="text-sm text-[var(--text-muted)]">
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
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
        <XAxis
          dataKey="phase"
          tick={{ fill: "var(--text-muted)", fontSize: 12 }}
        />
        <YAxis
          domain={[0, 1]}
          tick={{ fill: "var(--text-muted)", fontSize: 12 }}
          tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "var(--bg-card)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            color: "var(--text)",
          }}
          formatter={(value: number) => `${(value * 100).toFixed(1)}%`}
        />
        <Legend />
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
              dot={{ r: 4, fill: meta.color }}
              connectNulls
            />
          );
        })}
      </LineChart>
    </ResponsiveContainer>
  );
}
