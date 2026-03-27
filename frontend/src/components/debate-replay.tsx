"use client";

import type { Debate } from "@/lib/types";
import { AgentAvatar, agentMeta } from "./agent-avatar";
import { ArrowRight, Shield, RefreshCw } from "lucide-react";

export function DebateReplay({ debates }: { debates: Debate[] }) {
  if (debates.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-14 bg-[var(--bg-secondary)] border border-[var(--border)] shadow-[var(--shadow-sm)]">
        <p className="text-[13px] text-[var(--text-tertiary)] font-light">
          No debate exchanges recorded.
        </p>
      </div>
    );
  }

  const rounds: Record<number, Debate[]> = {};
  for (const d of debates) {
    (rounds[d.round_number] ??= []).push(d);
  }

  return (
    <div className="space-y-8">
      {Object.entries(rounds).map(([roundNum, exchanges]) => (
        <div key={roundNum}>
          <div className="flex items-center gap-3 mb-4">
            <span className="text-[11px] font-semibold uppercase tracking-widest text-[var(--accent)]">
              Round {roundNum}
            </span>
            <div className="flex-1 h-px bg-[var(--border)]" />
          </div>
          <div className="space-y-3">
            {exchanges.map((d) => {
              const challengerM = agentMeta(d.challenger_id);
              const targetM = agentMeta(d.target_id);
              return (
                <div
                  key={d.id}
                  className="group p-5 bg-[var(--bg-card)] border border-[var(--border)] shadow-[var(--shadow-sm)] transition-all duration-300 ease-out hover:bg-[var(--bg-tertiary)] hover:border-[var(--border-hover)] hover:translate-y-[-1px] hover:shadow-[var(--shadow-lg)]"
                >
                  <div className="flex items-center gap-2.5 mb-4">
                    <AgentAvatar agentId={d.challenger_id} size="sm" />
                    <ArrowRight size={14} className="text-[var(--text-tertiary)] group-hover:text-[var(--accent-light)] transition-colors duration-300" />
                    <AgentAvatar agentId={d.target_id} size="sm" />
                  </div>

                  <div className="mb-4 p-4 bg-[var(--bg-secondary)] border border-[var(--border)]">
                    <p className="text-[10px] font-semibold uppercase tracking-widest mb-2" style={{ color: challengerM.color }}>
                      Challenge
                    </p>
                    <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed font-light">{d.argument}</p>
                    {d.evidence_gap && (
                      <p className="text-[11px] text-[var(--text-tertiary)] mt-2 italic font-light">
                        Gap: {d.evidence_gap}
                      </p>
                    )}
                  </div>

                  {d.response_type && (
                    <div className="p-4 bg-[var(--bg-secondary)] border border-[var(--border)]">
                      <div className="flex items-center gap-2 mb-2">
                        {d.response_type === "defense" ? (
                          <Shield size={13} className="text-[var(--blue)]" />
                        ) : (
                          <RefreshCw size={13} className="text-[var(--yellow)]" />
                        )}
                        <p className="text-[10px] font-semibold uppercase tracking-widest" style={{ color: targetM.color }}>
                          {d.response_type === "defense" ? "Defended" : "Revised"}
                        </p>
                      </div>
                      <p className="text-[13px] text-[var(--text-secondary)] leading-relaxed font-light">
                        {d.response_text}
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
