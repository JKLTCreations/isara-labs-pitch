"use client";

const COLORS: Record<string, string> = {
  high: "bg-green-500/20 text-green-400 border-green-500/30",
  medium: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  low: "bg-red-500/20 text-red-400 border-red-500/30",
};

export function ConvictionBadge({ conviction }: { conviction: string }) {
  const cls = COLORS[conviction] ?? COLORS.low;
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${cls}`}
    >
      {conviction}
    </span>
  );
}
