"use client";

const AGENT_META: Record<string, { label: string; color: string; icon: string }> = {
  geopolitical_analyst: { label: "Geopolitical", color: "#f97316", icon: "G" },
  macro_economist:      { label: "Macro",        color: "#3b82f6", icon: "M" },
  sentiment_analyst:    { label: "Sentiment",    color: "#a855f7", icon: "S" },
  quant_analyst:        { label: "Quant",        color: "#22c55e", icon: "Q" },
  aggregator:           { label: "Aggregator",   color: "#6366f1", icon: "A" },
};

export function agentMeta(agentId: string) {
  return AGENT_META[agentId] ?? { label: agentId, color: "#888", icon: agentId[0]?.toUpperCase() ?? "?" };
}

export function AgentAvatar({
  agentId,
  size = "md",
}: {
  agentId: string;
  size?: "sm" | "md";
}) {
  const meta = agentMeta(agentId);
  const dim = size === "sm" ? "w-6 h-6 text-xs" : "w-8 h-8 text-sm";
  return (
    <div className="flex items-center gap-2">
      <div
        className={`${dim} rounded-full flex items-center justify-center font-bold`}
        style={{ backgroundColor: meta.color + "30", color: meta.color }}
      >
        {meta.icon}
      </div>
      <span className="text-sm font-medium">{meta.label}</span>
    </div>
  );
}
