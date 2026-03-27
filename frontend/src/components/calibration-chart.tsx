"use client";

import type { CalibrationProfile } from "@/lib/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

const AGENT_COLORS: Record<string, string> = {
  quant_analyst: "#3b82f6",
  geopolitical_analyst: "#ef4444",
  macro_economist: "#22c55e",
  sentiment_analyst: "#f59e0b",
  energy_analyst: "#8b5cf6",
  china_analyst: "#ec4899",
  polling_analyst: "#06b6d4",
  human_analyst: "#ffffff",
};

interface CalibrationChartProps {
  profiles: CalibrationProfile[];
}

interface BucketDataPoint {
  bucket: string;
  midpoint: number;
  [key: string]: string | number;
}

export function CalibrationChart({ profiles }: CalibrationChartProps) {
  if (profiles.length === 0) {
    return (
      <div className="text-center text-[var(--text-muted)] py-8">
        No calibration data yet. Run some forecasts and score them to see
        calibration curves.
      </div>
    );
  }

  // Build bucket data points for the chart
  const allBuckets = new Set<string>();
  for (const profile of profiles) {
    for (const bucket of Object.keys(profile.buckets)) {
      allBuckets.add(bucket);
    }
  }

  const sortedBuckets = [...allBuckets].sort((a, b) => {
    const aNum = parseInt(a.split("-")[0]);
    const bNum = parseInt(b.split("-")[0]);
    return aNum - bNum;
  });

  const data: BucketDataPoint[] = sortedBuckets.map((bucket) => {
    const low = parseInt(bucket.split("-")[0]) / 100;
    const mid = low + 0.05;
    const point: BucketDataPoint = {
      bucket,
      midpoint: Math.round(mid * 100),
    };
    for (const profile of profiles) {
      const bd = profile.buckets[bucket];
      if (bd) {
        point[profile.agent_id] = Math.round(bd.actual_accuracy * 100);
      }
    }
    return point;
  });

  return (
    <div className="space-y-6">
      {/* Accuracy overview */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
        {profiles.map((p) => (
          <div
            key={p.agent_id}
            className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-3"
          >
            <div className="flex items-center gap-2 mb-2">
              <div
                className="w-2 h-2 rounded-full"
                style={{
                  backgroundColor:
                    AGENT_COLORS[p.agent_id] || "var(--text-muted)",
                }}
              />
              <span className="text-xs font-medium truncate">
                {p.agent_id.replace("_", " ")}
              </span>
            </div>
            <div className="text-lg font-bold">
              {p.overall_accuracy !== null
                ? `${(p.overall_accuracy * 100).toFixed(1)}%`
                : "N/A"}
            </div>
            <div className="text-xs text-[var(--text-muted)]">
              {p.total_predictions} predictions
            </div>
            <div className="mt-1 flex items-center gap-1">
              <span className="text-xs text-[var(--text-muted)]">Weight:</span>
              <span
                className={`text-xs font-medium ${
                  p.calibration_weight >= 0.7
                    ? "text-green-400"
                    : p.calibration_weight >= 0.4
                      ? "text-yellow-400"
                      : "text-red-400"
                }`}
              >
                {p.calibration_weight.toFixed(2)}
              </span>
            </div>
            {p.platt_params && (
              <div className="text-[10px] text-[var(--text-muted)] mt-1">
                Platt scaling active
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Calibration curve chart */}
      {data.length > 0 && (
        <div>
          <h3 className="text-sm font-medium mb-2">
            Calibration Curve (Predicted vs Actual Accuracy)
          </h3>
          <p className="text-xs text-[var(--text-muted)] mb-3">
            Perfect calibration = bars match the diagonal (predicted confidence
            equals actual accuracy).
          </p>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data} barGap={2}>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="var(--border)"
                opacity={0.3}
              />
              <XAxis
                dataKey="bucket"
                tick={{ fill: "var(--text-muted)", fontSize: 11 }}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fill: "var(--text-muted)", fontSize: 11 }}
                label={{
                  value: "Actual Accuracy %",
                  angle: -90,
                  position: "insideLeft",
                  style: { fill: "var(--text-muted)", fontSize: 11 },
                }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "var(--bg-card)",
                  border: "1px solid var(--border)",
                  borderRadius: "6px",
                  fontSize: "12px",
                }}
                labelStyle={{ color: "var(--text)" }}
              />
              <ReferenceLine
                y={0}
                stroke="var(--border)"
              />
              {profiles.map((p) => (
                <Bar
                  key={p.agent_id}
                  dataKey={p.agent_id}
                  name={p.agent_id.replace("_", " ")}
                  fill={AGENT_COLORS[p.agent_id] || "#888"}
                  opacity={0.8}
                  radius={[2, 2, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
