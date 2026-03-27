"use client";

const AGENT_META: Record<string, { label: string; color: string; icon: string }> = {
  geopolitical_analyst: { label: "Geopolitical", color: "#c98a4e", icon: "G" },
  macro_economist:      { label: "Macro",        color: "#6a9ec0", icon: "M" },
  sentiment_analyst:    { label: "Sentiment",    color: "#9a85c0", icon: "S" },
  quant_analyst:        { label: "Quant",        color: "#5a9e75", icon: "Q" },
  energy_analyst:       { label: "Energy",       color: "#c98a4e", icon: "E" },
  china_analyst:        { label: "China",        color: "#c07878", icon: "C" },
  polling_analyst:      { label: "Polling",      color: "#6aaeb5", icon: "P" },
  human_analyst:        { label: "Human",        color: "#ede9e1", icon: "H" },
  aggregator:           { label: "Aggregator",   color: "#437e5b", icon: "A" },
};

export function agentMeta(agentId: string) {
  return AGENT_META[agentId] ?? { label: agentId, color: "#5c7264", icon: agentId[0]?.toUpperCase() ?? "?" };
}

export function AgentAvatar({
  agentId,
  size = "md",
}: {
  agentId: string;
  size?: "sm" | "md";
}) {
  const meta = agentMeta(agentId);
  const dim = size === "sm" ? "w-6 h-6 text-[10px]" : "w-7 h-7 text-[11px]";
  return (
    <div className="flex items-center gap-2.5">
      <div
        className={`${dim} flex items-center justify-center font-semibold transition-transform duration-200 hover:scale-110`}
        style={{
          backgroundColor: meta.color + "18",
          color: meta.color,
        }}
      >
        {meta.icon}
      </div>
      <span className="text-[13px] font-medium text-[var(--text-secondary)]">
        {meta.label}
      </span>
    </div>
  );
}
