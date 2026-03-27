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
        className="flex items-center gap-1 text-xs font-medium text-[var(--text-muted)] hover:text-[var(--text)] transition-colors mb-1"
      >
        {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        Evidence ({evidence.length})
      </button>
      {expanded && (
        <ul className="space-y-2 ml-3">
          {evidence.map((e, i) => (
            <li key={i} className="text-xs border-l-2 border-[var(--accent)] pl-2">
              <p className="text-[var(--text)]">{e.observation}</p>
              <div className="flex gap-3 text-[var(--text-muted)] mt-0.5">
                <span>{e.source}</span>
                <span>rel: {(e.relevance * 100).toFixed(0)}%</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
