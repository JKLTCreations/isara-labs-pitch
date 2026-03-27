"use client";

import { useEffect, useState } from "react";
import type { Run, CalibrationProfile } from "@/lib/types";
import { listRuns, getCalibrationDashboard } from "@/lib/api";
import { CalibrationChart } from "@/components/calibration-chart";

type Tab = "runs" | "calibration";

export default function RunsPage() {
  const [tab, setTab] = useState<Tab>("runs");
  const [runs, setRuns] = useState<Run[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string | undefined>();
  const [calibrationProfiles, setCalibrationProfiles] = useState<CalibrationProfile[]>([]);
  const [calibrationLoading, setCalibrationLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    listRuns({ asset: filter, limit: 50 })
      .then((d) => { setRuns(d.runs); setTotal(d.total); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [filter]);

  useEffect(() => {
    if (tab === "calibration" && calibrationProfiles.length === 0) {
      setCalibrationLoading(true);
      getCalibrationDashboard()
        .then((d) => setCalibrationProfiles(d.profiles))
        .catch(() => {})
        .finally(() => setCalibrationLoading(false));
    }
  }, [tab, calibrationProfiles.length]);

  const assets = [...new Set(runs.map((r) => r.asset))];

  return (
    <div className="fade-up">
      <div className="flex items-center justify-between mb-10">
        <div>
          <h1 className="text-2xl font-semibold tracking-[-0.02em] text-[var(--cream)]">Runs</h1>
          <p className="text-[13px] text-[var(--text-tertiary)] mt-1 font-light">
            {total} total forecast runs
          </p>
        </div>
        <div className="flex bg-[var(--bg-secondary)] border border-[var(--border)] p-1">
          <TabButton active={tab === "runs"} onClick={() => setTab("runs")}>Runs</TabButton>
          <TabButton active={tab === "calibration"} onClick={() => setTab("calibration")}>Calibration</TabButton>
        </div>
      </div>

      {tab === "runs" && (
        <>
          <div className="flex gap-2 mb-6">
            <FilterChip active={!filter} onClick={() => setFilter(undefined)}>All</FilterChip>
            {assets.map((a) => (
              <FilterChip key={a} active={filter === a} onClick={() => setFilter(a)}>{a}</FilterChip>
            ))}
          </div>

          {loading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="skeleton h-14" />
              ))}
            </div>
          ) : (
            <div className="border border-[var(--border)] overflow-hidden bg-[var(--bg-card)] shadow-[var(--shadow-sm)]">
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="text-[10px] font-semibold uppercase tracking-widest text-[var(--text-tertiary)] bg-[var(--bg-secondary)]">
                    <th className="text-left px-5 py-4">Run ID</th>
                    <th className="text-left px-5 py-4">Asset</th>
                    <th className="text-left px-5 py-4">Horizon</th>
                    <th className="text-left px-5 py-4">Status</th>
                    <th className="text-left px-5 py-4">Agents</th>
                    <th className="text-left px-5 py-4">Debates</th>
                    <th className="text-left px-5 py-4">Time</th>
                    <th className="text-left px-5 py-4">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map((run) => (
                    <tr
                      key={run.id}
                      className="border-t border-[var(--border)] transition-all duration-200 hover:bg-[var(--accent-subtle)]"
                    >
                      <td className="px-5 py-3.5">
                        <a href={`/forecast/${run.id}`} className="text-[var(--accent-light)] hover:text-[var(--green)] text-[12px] font-mono font-medium transition-colors duration-200">
                          {run.id}
                        </a>
                      </td>
                      <td className="px-5 py-3.5 font-semibold text-[var(--cream)]">{run.asset}</td>
                      <td className="px-5 py-3.5 text-[var(--text-tertiary)] font-light">{run.horizon}</td>
                      <td className="px-5 py-3.5">
                        <StatusDot status={run.status} />
                      </td>
                      <td className="px-5 py-3.5 text-[var(--text-tertiary)] tabular-nums font-light">{run.agent_count}</td>
                      <td className="px-5 py-3.5 text-[var(--text-tertiary)] tabular-nums font-light">{run.debate_rounds}</td>
                      <td className="px-5 py-3.5 text-[var(--text-tertiary)] tabular-nums text-[12px] font-light">
                        {run.elapsed_seconds ? `${run.elapsed_seconds.toFixed(1)}s` : "-"}
                      </td>
                      <td className="px-5 py-3.5 text-[var(--text-tertiary)] text-[12px] font-light">
                        {new Date(run.created_at).toLocaleDateString("en-US", {
                          month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
                        })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {tab === "calibration" && (
        <div className="fade-up-d1">
          <p className="text-[13px] text-[var(--text-tertiary)] mb-6 leading-relaxed font-light">
            Agent calibration tracks whether confidence scores are accurate.
            An agent saying 80% confidence should be correct ~80% of the time.
          </p>
          {calibrationLoading ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="skeleton h-24" />
              ))}
            </div>
          ) : (
            <CalibrationChart profiles={calibrationProfiles} />
          )}
        </div>
      )}
    </div>
  );
}

function TabButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-[12px] font-semibold transition-all duration-300 ${
        active
          ? "bg-[var(--accent)] text-[var(--cream)] shadow-sm"
          : "text-[var(--text-tertiary)] hover:text-[var(--cream-dim)] hover:bg-[var(--accent-subtle)]"
      }`}
    >
      {children}
    </button>
  );
}

function FilterChip({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`px-3.5 py-1.5 text-[12px] font-semibold transition-all duration-300 ${
        active
          ? "bg-[var(--accent)] text-[var(--cream)] shadow-[0_2px_12px_var(--accent-glow)]"
          : "bg-[var(--bg-secondary)] text-[var(--text-tertiary)] border border-[var(--border)] hover:border-[var(--accent)]/25 hover:text-[var(--cream-dim)] hover:translate-y-[-1px]"
      }`}
    >
      {children}
    </button>
  );
}

function StatusDot({ status }: { status: string }) {
  const color =
    status === "completed" ? "var(--green)" :
    status === "running" ? "var(--yellow)" : "var(--red)";
  return (
    <div className="flex items-center gap-2">
      <div
        className="w-[7px] h-[7px] rounded-full"
        style={{ backgroundColor: color, boxShadow: `0 0 6px ${color}` }}
      />
      <span className="text-[12px] font-medium capitalize" style={{ color }}>{status}</span>
    </div>
  );
}
