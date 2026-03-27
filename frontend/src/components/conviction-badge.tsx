"use client";

const STYLES: Record<string, string> = {
  high: "bg-[var(--green-subtle)] text-[var(--green)] border-l-2 border-[var(--green)]",
  medium: "bg-[var(--yellow-subtle)] text-[var(--yellow)] border-l-2 border-[var(--yellow)]",
  low: "bg-[var(--red-subtle)] text-[var(--red)] border-l-2 border-[var(--red)]",
};

export function ConvictionBadge({ conviction }: { conviction: string }) {
  const cls = STYLES[conviction] ?? STYLES.low;
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider ${cls}`}>
      {conviction}
    </span>
  );
}
