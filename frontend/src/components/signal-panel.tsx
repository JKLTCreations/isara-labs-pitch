"use client";

import type { Signal } from "@/lib/types";
import { AgentAvatar } from "./agent-avatar";
import { DirectionArrow, directionColor } from "./direction-arrow";
import { EvidenceList } from "./evidence-list";

export function SignalPanel({ signal }: { signal: Signal }) {
  const confPct = (signal.confidence * 100).toFixed(0);

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-4">
      <div className="flex items-center justify-between mb-3">
        <AgentAvatar agentId={signal.agent_id} />
        <span className="text-xs text-[var(--text-muted)]">{signal.phase}</span>
      </div>

      {/* Direction + confidence */}
      <div className="flex items-center gap-3 mb-3">
        <DirectionArrow direction={signal.direction} />
        <span className={`font-semibold ${directionColor(signal.direction)}`}>
          {signal.direction}
        </span>
        <span className="text-sm text-[var(--text-muted)]">
          {(signal.magnitude * 100).toFixed(2)}%
        </span>
      </div>

      {/* Confidence gauge */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-[var(--text-muted)] mb-1">
          <span>Confidence</span>
          <span>{confPct}%</span>
        </div>
        <div className="h-1.5 rounded-full bg-[var(--border)]">
          <div
            className="h-full rounded-full transition-all"
            style={{
              width: `${confPct}%`,
              backgroundColor:
                signal.confidence >= 0.7
                  ? "var(--green)"
                  : signal.confidence >= 0.4
                    ? "var(--yellow)"
                    : "var(--red)",
            }}
          />
        </div>
      </div>

      {/* Evidence */}
      <EvidenceList evidence={signal.evidence} />

      {/* Risks */}
      {signal.risks.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-medium text-[var(--text-muted)] mb-1">
            Risks
          </p>
          <ul className="text-xs text-[var(--text-muted)] space-y-0.5">
            {signal.risks.map((r, i) => (
              <li key={i} className="flex gap-1">
                <span className="text-red-400">-</span> {r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Contrarian note */}
      {signal.contrarian_note && (
        <div className="mt-3 p-2 rounded bg-[var(--bg-hover)] text-xs text-[var(--text-muted)] italic">
          {signal.contrarian_note}
        </div>
      )}
    </div>
  );
}
