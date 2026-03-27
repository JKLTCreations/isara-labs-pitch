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
} from "recharts";

const AGENT_COLORS: Record<string, string> = {
  quant_analyst: "#5a9e75",
  geopolitical_analyst: "#c98a4e",
  macro_economist: "#6a9ec0",
  sentiment_analyst: "#9a85c0",
  energy_analyst: "#c98a4e",
  china_analyst: "#c07878",
  polling_analyst: "#6aaeb5",
  human_analyst: "#ede9e1",
};

interface BucketDataPoint {
  bucket: string;
  midpoint: number;
  [key: string]: string | number;
}

export function CalibrationChart({ profiles }: { profiles: CalibrationProfile[] }) {
  if (profiles.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-14 bg-[var(--bg-secondary)] border border-[var(--border)] shadow-[var(--shadow-sm)]">
        <p className="text-[13px] text-[var(--text-tertiary)] font-light">
          No calibration data yet. Run forecasts and score them to see calibration curves.
        </p>
      </div>
    );
  }

  const allBuckets = new Set<string>();
  for (const profile of profiles) {
    for (const bucket of Object.keys(profile.buckets)) {
      allBuckets.add(bucket);
    }
  }

  const sortedBuckets = [...allBuckets].sort((a, b) => parseInt(a) - parseInt(b));

  const data: BucketDataPoint[] = sortedBuckets.map((bucket) => {
    const low = parseInt(bucket.split("-")[0]) / 100;
    const mid = low + 0.05;
    const point: BucketDataPoint = { bucket, midpoint: Math.round(mid * 100) };
    for (const profile of profiles) {
      const bd = profile.buckets[bucket];
      if (bd) point[profile.agent_id] = Math.round(bd.actual_accuracy * 100);
    }
    return point;
  });

  return (
    <div className="space-y-7">
      {/* Agent cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {profiles.map((p, i) => (
          <div
            key={p.agent_id}
            className={`group p-5 bg-[var(--bg-card)] border border-[var(--border)] shadow-[var(--shadow-sm)] transition-all duration-300 ease-out hover:bg-[var(--bg-tertiary)] hover:border-[var(--border-hover)] hover:translate-y-[-2px] hover:shadow-[var(--shadow-lg)] fade-up-d${Math.min(i + 1, 6)}`}
          >
            <div className="flex items-center gap-2.5 mb-3">
              <div
                className="w-2.5 h-2.5 rounded-full"
                style={{ backgroundColor: AGENT_COLORS[p.agent_id] || "#5c7264" }}
              />
              <span className="text-[12px] font-semibold text-[var(--text-secondary)] truncate capitalize">
                {p.agent_id.replace(/_/g, " ")}
              </span>
            </div>
            <div className="text-2xl font-semibold tabular-nums text-[var(--cream)]">
              {p.overall_accuracy !== null ? `${(p.overall_accuracy * 100).toFixed(1)}%` : "N/A"}
            </div>
            <div className="text-[11px] text-[var(--text-tertiary)] tabular-nums mt-1 font-light">
              {p.total_predictions} predictions
            </div>
            <div className="mt-2.5 flex items-center gap-2">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">Weight</span>
              <span className={`text-[12px] font-semibold tabular-nums ${
                p.calibration_weight >= 0.7 ? "text-[var(--green)]" :
                p.calibration_weight >= 0.4 ? "text-[var(--yellow)]" : "text-[var(--red)]"
              }`}>
                {p.calibration_weight.toFixed(2)}
              </span>
            </div>
            {p.platt_params && (
              <p className="text-[10px] text-[var(--accent-light)] mt-1.5 font-medium">Platt scaling active</p>
            )}
          </div>
        ))}
      </div>

      {/* Chart */}
      {data.length > 0 && (
        <div>
          <div className="flex items-center gap-3 mb-5">
            <h3 className="text-[14px] font-semibold tracking-[-0.01em] text-[var(--cream)]">Calibration Curve</h3>
            <div className="flex-1 h-px bg-gradient-to-r from-[var(--accent)]/15 to-transparent" />
          </div>
          <p className="text-[11px] text-[var(--text-tertiary)] mb-5 font-light">
            Perfect calibration means bars match the predicted confidence bucket.
          </p>
          <div className="p-6 bg-[var(--bg-card)] border border-[var(--border)] shadow-[var(--shadow-sm)]">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={data} barGap={2}>
                <CartesianGrid strokeDasharray="3 3" stroke="#091a15" />
                <XAxis
                  dataKey="bucket"
                  tick={{ fill: "#5c7264", fontSize: 11, fontWeight: 500 }}
                  axisLine={{ stroke: "#091a15" }}
                  tickLine={false}
                />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fill: "#5c7264", fontSize: 11, fontWeight: 500 }}
                  axisLine={{ stroke: "#091a15" }}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0a1c18",
                    border: "1px solid #13332a",
                    borderRadius: 0,
                    fontSize: 12,
                    boxShadow: "0 8px 32px rgba(6,18,16,0.6)",
                  }}
                  labelStyle={{ color: "#f2efe8", fontWeight: 600 }}
                />
                {profiles.map((p) => (
                  <Bar
                    key={p.agent_id}
                    dataKey={p.agent_id}
                    name={p.agent_id.replace(/_/g, " ")}
                    fill={AGENT_COLORS[p.agent_id] || "#5c7264"}
                    opacity={0.85}
                    radius={[0, 0, 0, 0]}
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
