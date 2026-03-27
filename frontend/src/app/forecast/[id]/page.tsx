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
      <div className="space-y-5">
        <div className="skeleton h-6 w-48" />
        <div className="skeleton h-56" />
        <div className="skeleton h-40" />
      </div>
    );
  }

  if (!data) {
    return <p className="text-[13px] text-[var(--text-tertiary)] font-light">Forecast not found.</p>;
  }

  const { run, forecast, signals, debates } = data;

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
    <div className="space-y-10 fade-up">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-[13px]">
        <a href="/" className="text-[var(--text-tertiary)] hover:text-[var(--accent-light)] transition-colors duration-300 font-medium">
          Forecasts
        </a>
        <span className="text-[var(--text-tertiary)]">/</span>
        <span className="text-[var(--cream-dim)] font-medium">{run.id}</span>
      </div>

      {/* Forecast header */}
      {forecast ? (
        <div className="p-8 bg-[var(--bg-card)] border border-[var(--border)] shadow-[var(--shadow-sm)]">
          <div className="flex flex-wrap items-center gap-3 mb-7">
            <h1 className="text-xl font-semibold tracking-[-0.02em] text-[var(--cream)]">{forecast.asset}</h1>
            <span className="text-[11px] font-medium text-[var(--text-tertiary)] bg-[var(--cream-subtle)] px-2.5 py-1">
              {forecast.horizon}
            </span>
            <ConvictionBadge conviction={forecast.conviction} />
            <span className="text-[11px] text-[var(--text-tertiary)] font-light ml-auto">
              {run.status} &middot; {run.elapsed_seconds?.toFixed(1)}s &middot;{" "}
              {run.debate_rounds} round{run.debate_rounds !== 1 ? "s" : ""}
            </span>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-7">
            <MetricCard label="Direction">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 flex items-center justify-center bg-[var(--accent-subtle)]">
                  <DirectionArrow direction={forecast.direction} size={16} />
                </div>
                <span className={`text-[14px] font-semibold capitalize ${directionColor(forecast.direction)}`}>
                  {forecast.direction}
                </span>
              </div>
            </MetricCard>
            <MetricCard label="Expected Move">
              <span className="text-xl font-semibold tabular-nums text-[var(--cream)]">
                {(forecast.expected_move * 100).toFixed(2)}%
              </span>
            </MetricCard>
            <MetricCard label="80% CI">
              <span className="text-[13px] font-medium tabular-nums text-[var(--text-secondary)]">
                [{(forecast.ci_lower * 100).toFixed(2)}%, {(forecast.ci_upper * 100).toFixed(2)}%]
              </span>
            </MetricCard>
            <MetricCard label="Consensus">
              <span className="text-xl font-semibold tabular-nums text-[var(--accent-light)]">
                {(forecast.consensus_strength * 100).toFixed(0)}%
              </span>
            </MetricCard>
          </div>

          {/* Drivers & Risks */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="p-5 bg-[var(--bg-secondary)] border-l-2 border-[var(--green)]">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-[var(--green)] mb-3">Key Drivers</p>
              <ul className="text-[13px] space-y-2.5">
                {forecast.key_drivers.map((d, i) => (
                  <li key={i} className="flex gap-2.5 text-[var(--text-secondary)] leading-relaxed font-light">
                    <span className="text-[var(--green)] font-semibold mt-0.5">+</span> {d}
                  </li>
                ))}
              </ul>
            </div>
            <div className="p-5 bg-[var(--bg-secondary)] border-l-2 border-[var(--red)]">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-[var(--red)] mb-3">Key Risks</p>
              <ul className="text-[13px] space-y-2.5">
                {forecast.key_risks.map((r, i) => (
                  <li key={i} className="flex gap-2.5 text-[var(--text-secondary)] leading-relaxed font-light">
                    <span className="text-[var(--red)] font-semibold mt-0.5">&ndash;</span> {r}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {forecast.dissenting_view && (
            <div className="p-5 bg-[var(--yellow-subtle)] border-l-2 border-[var(--yellow)]">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-[var(--yellow)] mb-2">Dissenting View</p>
              <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed font-light">{forecast.dissenting_view}</p>
            </div>
          )}

          {forecast.debate_summary && (
            <div className="mt-6 p-5 bg-[var(--bg-secondary)] border border-[var(--border)]">
              <p className="text-[10px] font-semibold uppercase tracking-widest text-[var(--text-tertiary)] mb-2">Debate Summary</p>
              <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed font-light">{forecast.debate_summary}</p>
            </div>
          )}
        </div>
      ) : (
        <div className="p-8 bg-[var(--bg-card)] border border-[var(--border)] shadow-[var(--shadow-sm)]">
          <h1 className="text-xl font-semibold tracking-[-0.02em] text-[var(--cream)] mb-2">{run.asset}</h1>
          <p className="text-[13px] text-[var(--text-tertiary)] font-light">
            Status: {run.status}. No final forecast produced.
          </p>
        </div>
      )}

      {/* Agent Signals */}
      <Section title="Agent Signals" count={latestSignals.length}>
        {latestSignals.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            {latestSignals.map((s, i) => (
              <div key={s.id} className={`fade-up-d${Math.min(i + 1, 6)}`}>
                <SignalPanel signal={s} />
              </div>
            ))}
          </div>
        ) : (
          <p className="text-[13px] text-[var(--text-tertiary)] font-light">No signals recorded.</p>
        )}
      </Section>

      {/* Convergence */}
      {signals.length > 0 && (
        <Section title="Confidence Convergence">
          <div className="p-6 bg-[var(--bg-card)] border border-[var(--border)] shadow-[var(--shadow-sm)]">
            <ConvergenceChart signals={signals} />
          </div>
        </Section>
      )}

      {/* Debate */}
      <Section title="Debate Replay" count={debates.length}>
        <DebateReplay debates={debates} />
      </Section>
    </div>
  );
}

function Section({ title, count, children }: { title: string; count?: number; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex items-center gap-3 mb-5">
        <h2 className="text-[14px] font-semibold tracking-[-0.01em] text-[var(--cream)]">{title}</h2>
        {count !== undefined && count > 0 && (
          <span className="text-[10px] font-semibold tabular-nums text-[var(--text-tertiary)] bg-[var(--cream-subtle)] px-2 py-0.5">
            {count}
          </span>
        )}
        <div className="flex-1 h-px bg-gradient-to-r from-[var(--accent)]/15 to-transparent" />
      </div>
      {children}
    </div>
  );
}

function MetricCard({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="bg-[var(--bg-secondary)] border border-[var(--border)] px-5 py-4 shadow-[var(--shadow-sm)] transition-all duration-300 hover:bg-[var(--bg-tertiary)] hover:border-[var(--border-hover)]">
      <p className="text-[10px] font-semibold uppercase tracking-widest text-[var(--text-tertiary)] mb-2">{label}</p>
      {children}
    </div>
  );
}
