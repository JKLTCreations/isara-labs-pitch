"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export function DirectionArrow({
  direction,
  size = 16,
}: {
  direction: "bullish" | "bearish" | "neutral";
  size?: number;
}) {
  if (direction === "bullish")
    return <TrendingUp size={size} className="text-[var(--green)]" />;
  if (direction === "bearish")
    return <TrendingDown size={size} className="text-[var(--red)]" />;
  return <Minus size={size} className="text-[var(--yellow)]" />;
}

export function directionColor(direction: string) {
  if (direction === "bullish") return "text-[var(--green)]";
  if (direction === "bearish") return "text-[var(--red)]";
  return "text-[var(--yellow)]";
}
