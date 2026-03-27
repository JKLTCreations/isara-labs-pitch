"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import type { Evidence } from "@/lib/types";

export function EvidenceList({ evidence }: { evidence: Evidence[] }) {
  const [expanded, setExpanded] = useState(false);

  if (evidence.length === 0) return null;

  return (
    <div>
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)] hover:text-[var(--accent-light)] transition-colors duration-300"
      >
        {expanded ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
        Evidence ({evidence.length})
      </button>
      {expanded && (
        <ul className="space-y-2 mt-3">
          {evidence.map((e, i) => (
            <li
              key={i}
              className="text-[12px] p-3 bg-[var(--bg-secondary)] border-l-2 border-[var(--accent)] transition-colors duration-200 hover:bg-[var(--bg-tertiary)]"
            >
              <p className="text-[var(--text-secondary)] leading-relaxed font-light">{e.observation}</p>
              <div className="flex gap-3 text-[var(--text-tertiary)] mt-1.5">
                <span className="font-mono text-[10px] bg-[var(--bg-tertiary)] px-1.5 py-0.5">{e.source}</span>
                <span className="tabular-nums text-[10px] font-light">rel: {(e.relevance * 100).toFixed(0)}%</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
