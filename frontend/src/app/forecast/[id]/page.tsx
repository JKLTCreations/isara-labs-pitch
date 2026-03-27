"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import type { ForecastDetail, Signal } from "@/lib/types";
import { getForecast } from "@/lib/api";
import { ConvictionBadge } from "@/components/conviction-badge";
import { DirectionArrow, directionColor } from "@/components/direction-arrow";
import { SignalPanel } from "@/components/signal-panel";
import { DebateReplay } from "@/components/debate-replay";
import { ConvergenceChart } from "@/components/convergence-chart";

export default function ForecastPage() {
  const params = useParams();
  const id = params.id as string;
  const [data, setData] = useState<ForecastDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getForecast(id)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 w-48 rounded bg-[var(--bg-card)]" />
        <div className="h-40 rounded-lg bg-[var(--bg-card)]" />
      </div>
    );
  }

  if (!data) {
    return <p className="text-[var(--text-muted)]">Forecast not found.</p>;
  }

  const { run, forecast, signals, debates } = data;

  // Get latest signals per agent (last phase for each)
  const latestSignals: Signal[] = [];
  const seen = new Set<string>();
  for (const s of [...signals].reverse()) {
    if (!seen.has(s.agent_id)) {
      seen.add(s.agent_id);
      latestSignals.push(s);
    }
  }
  latestSignals.reverse();

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <a
            href="/"
            className="text-sm text-[var(--text-muted)] hover:text-[var(--text)]"
          >
            Forecasts
          </a>
          <span className="text-[var(--text-muted)]">/</span>
          <span className="text-sm">{run.id}</span>
        </div>

        {forecast ? (
          <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <div className="flex flex-wrap items-center gap-4 mb-4">
              <h1 className="text-2xl font-bold">{forecast.asset}</h1>
              <span className="text-[var(--text-muted)]">{forecast.horizon}</span>
              <ConvictionBadge conviction={forecast.conviction} />
              <span className="text-xs text-[var(--text-muted)]">
                {run.status} &middot;{" "}
                {run.elapsed_seconds?.toFixed(1)}s &middot;{" "}
                {run.debate_rounds} debate round{run.debate_rounds !== 1 ? "s" : ""}
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-6 mb-4">
              <div className="flex items-center gap-2">
                <DirectionArrow direction={forecast.direction} size={24} />
                <span
                  className={`text-xl font-bold ${directionColor(forecast.direction)}`}
                >
                  {forecast.direction}
                </span>
              </div>
              <div>
                <p className="text-xs text-[var(--text-muted)]">Expected Move</p>
                <p className="font-mono font-semibold">
                  {(forecast.expected_move * 100).toFixed(2)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-[var(--text-muted)]">80% CI</p>
                <p className="font-mono text-sm">
                  [{(forecast.ci_lower * 100).toFixed(2)}%,{" "}
                  {(forecast.ci_upper * 100).toFixed(2)}%]
                </p>
              </div>
              <div>
                <p className="text-xs text-[var(--text-muted)]">Consensus</p>
                <p className="font-mono font-semibold">
                  {(forecast.consensus_strength * 100).toFixed(0)}%
                </p>
              </div>
            </div>

            {/* Drivers & Risks */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-xs font-medium text-[var(--text-muted)] mb-1">
                  Key Drivers
                </p>
                <ul className="text-sm space-y-1">
                  {forecast.key_drivers.map((d, i) => (
                    <li key={i} className="flex gap-1.5">
                      <span className="text-green-400">+</span>
                      {d}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="text-xs font-medium text-[var(--text-muted)] mb-1">
                  Key Risks
                </p>
                <ul className="text-sm space-y-1">
                  {forecast.key_risks.map((r, i) => (
                    <li key={i} className="flex gap-1.5">
                      <span className="text-red-400">-</span>
                      {r}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Dissenting view */}
            {forecast.dissenting_view && (
              <div className="p-3 rounded bg-yellow-500/5 border border-yellow-500/20 text-sm">
                <p className="text-xs font-medium text-yellow-400 mb-1">
                  Dissenting View
                </p>
                <p className="text-[var(--text)]">{forecast.dissenting_view}</p>
              </div>
            )}

            {/* Debate summary */}
            {forecast.debate_summary && (
              <div className="mt-4">
                <p className="text-xs font-medium text-[var(--text-muted)] mb-1">
                  Debate Summary
                </p>
                <p className="text-sm text-[var(--text)]">
                  {forecast.debate_summary}
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-6">
            <h1 className="text-2xl font-bold mb-2">{run.asset}</h1>
            <p className="text-[var(--text-muted)]">
              Status: {run.status}. No final forecast produced.
            </p>
          </div>
        )}
      </div>

      {/* Agent Signals */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Agent Signals</h2>
        {latestSignals.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {latestSignals.map((s) => (
              <SignalPanel key={s.id} signal={s} />
            ))}
          </div>
        ) : (
          <p className="text-sm text-[var(--text-muted)]">No signals recorded.</p>
        )}
      </div>

      {/* Convergence Chart */}
      {signals.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold mb-3">Confidence Convergence</h2>
          <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-4">
            <ConvergenceChart signals={signals} />
          </div>
        </div>
      )}

      {/* Debate Replay */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Debate Replay</h2>
        <DebateReplay debates={debates} />
      </div>
    </div>
  );
}
