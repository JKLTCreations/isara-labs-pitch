"use client";

import type { Signal } from "@/lib/types";
import { AgentAvatar } from "./agent-avatar";
import { DirectionArrow, directionColor } from "./direction-arrow";
import { EvidenceList } from "./evidence-list";

export function SignalPanel({ signal }: { signal: Signal }) {
  const confPct = (signal.confidence * 100).toFixed(0);

  const barColor =
    signal.confidence >= 0.7 ? "bg-[var(--green)]" :
    signal.confidence >= 0.4 ? "bg-[var(--yellow)]" :
                               "bg-[var(--red)]";

  return (
    <div className="group p-5 bg-[var(--bg-card)] border border-[var(--border)] shadow-[var(--shadow-sm)] transition-all duration-300 ease-out hover:bg-[var(--bg-tertiary)] hover:border-[var(--border-hover)] hover:translate-y-[-2px] hover:shadow-[var(--shadow-lg)]">
      <div className="flex items-center justify-between mb-4">
        <AgentAvatar agentId={signal.agent_id} />
        <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)] bg-[var(--bg-tertiary)] px-2 py-1">
          {signal.phase}
        </span>
      </div>

      <div className="flex items-center gap-2.5 mb-4">
        <div className="w-8 h-8 flex items-center justify-center bg-[var(--accent-subtle)] group-hover:bg-[var(--accent)]/15 transition-colors duration-300">
          <DirectionArrow direction={signal.direction} />
        </div>
        <span className={`text-[14px] font-semibold capitalize ${directionColor(signal.direction)}`}>
          {signal.direction}
        </span>
        <span className="text-[12px] text-[var(--text-tertiary)] tabular-nums font-light">
          {(signal.magnitude * 100).toFixed(2)}%
        </span>
      </div>

      <div className="mb-4">
        <div className="flex justify-between text-[11px] font-medium text-[var(--text-tertiary)] mb-2">
          <span>Confidence</span>
          <span className="tabular-nums text-[var(--cream-dim)]">{confPct}%</span>
        </div>
        <div className="h-[5px] bg-[var(--bg-tertiary)] overflow-hidden">
          <div
            className={`h-full ${barColor} transition-all duration-700 ease-out`}
            style={{ width: `${confPct}%` }}
          />
        </div>
      </div>

      <EvidenceList evidence={signal.evidence} />

      {signal.risks.length > 0 && (
        <div className="mt-4 p-3.5 bg-[var(--red-subtle)] border-l-2 border-[var(--red)]">
          <p className="text-[10px] font-semibold text-[var(--red)] mb-2 uppercase tracking-wider">Risks</p>
          <ul className="text-[12px] text-[var(--text-secondary)] space-y-1.5">
            {signal.risks.map((r, i) => (
              <li key={i} className="flex gap-2 leading-relaxed font-light">
                <span className="text-[var(--red)] mt-0.5">&#x2022;</span> {r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {signal.contrarian_note && (
        <div className="mt-4 p-3.5 bg-[var(--yellow-subtle)] border-l-2 border-[var(--yellow)]">
          <p className="text-[10px] font-semibold text-[var(--yellow)] mb-1 uppercase tracking-wider">Contrarian</p>
          <p className="text-[12px] text-[var(--text-secondary)] leading-relaxed font-light">
            {signal.contrarian_note}
          </p>
        </div>
      )}
    </div>
  );
}
