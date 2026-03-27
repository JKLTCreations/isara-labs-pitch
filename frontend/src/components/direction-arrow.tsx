"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export function DirectionArrow({
  direction,
  size = 18,
}: {
  direction: "bullish" | "bearish" | "neutral";
  size?: number;
}) {
  if (direction === "bullish")
    return <TrendingUp size={size} className="text-green-400" />;
  if (direction === "bearish")
    return <TrendingDown size={size} className="text-red-400" />;
  return <Minus size={size} className="text-yellow-400" />;
}

export function directionColor(direction: string) {
  if (direction === "bullish") return "text-green-400";
  if (direction === "bearish") return "text-red-400";
  return "text-yellow-400";
}
