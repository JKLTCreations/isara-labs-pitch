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
  const [calibrationProfiles, setCalibrationProfiles] = useState<
    CalibrationProfile[]
  >([]);
  const [calibrationLoading, setCalibrationLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    listRuns({ asset: filter, limit: 50 })
      .then((d) => {
        setRuns(d.runs);
        setTotal(d.total);
      })
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
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Forecast Runs</h1>
          <p className="text-sm text-[var(--text-muted)]">
            {total} total runs
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setTab("runs")}
            className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
              tab === "runs"
                ? "bg-[var(--accent)] text-white"
                : "border border-[var(--border)] text-[var(--text-muted)]"
            }`}
          >
            Runs
          </button>
          <button
            onClick={() => setTab("calibration")}
            className={`px-4 py-1.5 rounded text-sm font-medium transition-colors ${
              tab === "calibration"
                ? "bg-[var(--accent)] text-white"
                : "border border-[var(--border)] text-[var(--text-muted)]"
            }`}
          >
            Calibration
          </button>
        </div>
      </div>

      {tab === "runs" && (
        <>
          <div className="flex gap-2 mb-4">
            <button
              onClick={() => setFilter(undefined)}
              className={`px-3 py-1 rounded text-xs border transition-colors ${
                !filter
                  ? "border-[var(--accent)] bg-[var(--accent)]/20 text-[var(--text)]"
                  : "border-[var(--border)] text-[var(--text-muted)]"
              }`}
            >
              All
            </button>
            {assets.map((a) => (
              <button
                key={a}
                onClick={() => setFilter(a)}
                className={`px-3 py-1 rounded text-xs border transition-colors ${
                  filter === a
                    ? "border-[var(--accent)] bg-[var(--accent)]/20 text-[var(--text)]"
                    : "border-[var(--border)] text-[var(--text-muted)]"
                }`}
              >
                {a}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div
                  key={i}
                  className="h-12 rounded bg-[var(--bg-card)] animate-pulse"
                />
              ))}
            </div>
          ) : (
            <div className="rounded-lg border border-[var(--border)] overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-[var(--bg-card)] text-[var(--text-muted)] text-xs">
                    <th className="text-left px-4 py-2 font-medium">Run ID</th>
                    <th className="text-left px-4 py-2 font-medium">Asset</th>
                    <th className="text-left px-4 py-2 font-medium">
                      Horizon
                    </th>
                    <th className="text-left px-4 py-2 font-medium">Status</th>
                    <th className="text-left px-4 py-2 font-medium">Agents</th>
                    <th className="text-left px-4 py-2 font-medium">
                      Debates
                    </th>
                    <th className="text-left px-4 py-2 font-medium">Time</th>
                    <th className="text-left px-4 py-2 font-medium">
                      Created
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map((run) => (
                    <tr
                      key={run.id}
                      className="border-t border-[var(--border)] hover:bg-[var(--bg-hover)] transition-colors"
                    >
                      <td className="px-4 py-2">
                        <a
                          href={`/forecast/${run.id}`}
                          className="text-[var(--accent)] hover:underline font-mono text-xs"
                        >
                          {run.id}
                        </a>
                      </td>
                      <td className="px-4 py-2 font-medium">{run.asset}</td>
                      <td className="px-4 py-2 text-[var(--text-muted)]">
                        {run.horizon}
                      </td>
                      <td className="px-4 py-2">
                        <span
                          className={`text-xs ${
                            run.status === "completed"
                              ? "text-green-400"
                              : run.status === "running"
                                ? "text-yellow-400"
                                : "text-red-400"
                          }`}
                        >
                          {run.status}
                        </span>
                      </td>
                      <td className="px-4 py-2 text-[var(--text-muted)]">
                        {run.agent_count}
                      </td>
                      <td className="px-4 py-2 text-[var(--text-muted)]">
                        {run.debate_rounds}
                      </td>
                      <td className="px-4 py-2 text-[var(--text-muted)] font-mono text-xs">
                        {run.elapsed_seconds
                          ? `${run.elapsed_seconds.toFixed(1)}s`
                          : "-"}
                      </td>
                      <td className="px-4 py-2 text-[var(--text-muted)] text-xs">
                        {new Date(run.created_at).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
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
        <div>
          <p className="text-sm text-[var(--text-muted)] mb-4">
            Agent calibration tracks whether confidence scores are accurate. An
            agent saying 80% confidence should be correct ~80% of the time.
          </p>
          {calibrationLoading ? (
            <div className="space-y-4">
              {[...Array(3)].map((_, i) => (
                <div
                  key={i}
                  className="h-24 rounded bg-[var(--bg-card)] animate-pulse"
                />
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
