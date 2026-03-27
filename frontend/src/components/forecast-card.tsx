"use client";

import type { Forecast } from "@/lib/types";
import { ConvictionBadge } from "./conviction-badge";
import { DirectionArrow, directionColor } from "./direction-arrow";

export function ForecastCard({ forecast }: { forecast: Forecast }) {
  const move = (forecast.expected_move * 100).toFixed(2);
  const consensus = (forecast.consensus_strength * 100).toFixed(0);
  const date = new Date(forecast.created_at).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <a
      href={`/forecast/${forecast.run_id}`}
      className="block rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-4 hover:border-[var(--accent)] transition-colors"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-base">{forecast.asset}</span>
          <span className="text-xs text-[var(--text-muted)]">
            {forecast.horizon}
          </span>
        </div>
        <ConvictionBadge conviction={forecast.conviction} />
      </div>

      <div className="flex items-center gap-3 mb-3">
        <DirectionArrow direction={forecast.direction} size={22} />
        <span className={`text-lg font-bold ${directionColor(forecast.direction)}`}>
          {forecast.direction}
        </span>
        <span className="text-sm text-[var(--text-muted)]">
          {move}% expected
        </span>
      </div>

      {/* Consensus strength bar */}
      <div className="mb-2">
        <div className="flex justify-between text-xs text-[var(--text-muted)] mb-1">
          <span>Consensus</span>
          <span>{consensus}%</span>
        </div>
        <div className="h-1.5 rounded-full bg-[var(--border)]">
          <div
            className="h-full rounded-full bg-[var(--accent)]"
            style={{ width: `${consensus}%` }}
          />
        </div>
      </div>

      <div className="text-xs text-[var(--text-muted)]">{date}</div>
    </a>
  );
}
