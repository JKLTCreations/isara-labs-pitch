"use client";

import { useEffect, useState } from "react";
import type { Run } from "@/lib/types";
import { listRuns } from "@/lib/api";
import { ConvictionBadge } from "@/components/conviction-badge";

export default function RunsPage() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string | undefined>();

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
                <th className="text-left px-4 py-2 font-medium">Horizon</th>
                <th className="text-left px-4 py-2 font-medium">Status</th>
                <th className="text-left px-4 py-2 font-medium">Agents</th>
                <th className="text-left px-4 py-2 font-medium">Debates</th>
                <th className="text-left px-4 py-2 font-medium">Time</th>
                <th className="text-left px-4 py-2 font-medium">Created</th>
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
    </div>
  );
}
