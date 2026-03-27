"use client";

import type { Debate } from "@/lib/types";
import { AgentAvatar, agentMeta } from "./agent-avatar";
import { ArrowRight, Shield, RefreshCw } from "lucide-react";

export function DebateReplay({ debates }: { debates: Debate[] }) {
  if (debates.length === 0) {
    return (
      <p className="text-sm text-[var(--text-muted)]">No debate exchanges recorded.</p>
    );
  }

  // Group by round
  const rounds: Record<number, Debate[]> = {};
  for (const d of debates) {
    (rounds[d.round_number] ??= []).push(d);
  }

  return (
    <div className="space-y-6">
      {Object.entries(rounds).map(([roundNum, exchanges]) => (
        <div key={roundNum}>
          <h4 className="text-sm font-medium text-[var(--text-muted)] mb-3">
            Round {roundNum}
          </h4>
          <div className="space-y-3">
            {exchanges.map((d) => {
              const challengerMeta = agentMeta(d.challenger_id);
              const targetMeta = agentMeta(d.target_id);
              return (
                <div
                  key={d.id}
                  className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-4"
                >
                  {/* Header: challenger -> target */}
                  <div className="flex items-center gap-2 mb-3">
                    <AgentAvatar agentId={d.challenger_id} size="sm" />
                    <ArrowRight size={14} className="text-[var(--text-muted)]" />
                    <AgentAvatar agentId={d.target_id} size="sm" />
                  </div>

                  {/* Challenge */}
                  <div className="mb-3">
                    <p className="text-xs font-medium mb-1" style={{ color: challengerMeta.color }}>
                      Challenge
                    </p>
                    <p className="text-sm text-[var(--text)]">{d.argument}</p>
                    {d.evidence_gap && (
                      <p className="text-xs text-[var(--text-muted)] mt-1">
                        Evidence gap: {d.evidence_gap}
                      </p>
                    )}
                  </div>

                  {/* Response */}
                  {d.response_type && (
                    <div className="border-t border-[var(--border)] pt-3">
                      <div className="flex items-center gap-1 mb-1">
                        {d.response_type === "defense" ? (
                          <Shield size={12} className="text-blue-400" />
                        ) : (
                          <RefreshCw size={12} className="text-yellow-400" />
                        )}
                        <p
                          className="text-xs font-medium"
                          style={{ color: targetMeta.color }}
                        >
                          {d.response_type === "defense" ? "Defended" : "Revised"}
                        </p>
                      </div>
                      <p className="text-sm text-[var(--text)]">
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
