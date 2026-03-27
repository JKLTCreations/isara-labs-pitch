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
      className="group block p-6 bg-[var(--bg-card)] border border-[var(--border)] shadow-[var(--shadow-sm)] transition-all duration-300 ease-out hover:bg-[var(--bg-tertiary)] hover:border-[var(--border-hover)] hover:translate-y-[-3px] hover:shadow-[var(--shadow-xl)]"
    >
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <span className="text-[17px] font-semibold tracking-[-0.01em] text-[var(--cream)]">{forecast.asset}</span>
          <span className="text-[11px] font-medium text-[var(--text-tertiary)] bg-[var(--bg-tertiary)] px-2 py-0.5">
            {forecast.horizon}
          </span>
        </div>
        <ConvictionBadge conviction={forecast.conviction} />
      </div>

      <div className="flex items-center gap-3 mb-5">
        <div className="w-9 h-9 flex items-center justify-center bg-[var(--accent-subtle)] group-hover:bg-[var(--accent)]/15 transition-colors duration-300">
          <DirectionArrow direction={forecast.direction} size={18} />
        </div>
        <div>
          <span className={`text-[14px] font-semibold capitalize ${directionColor(forecast.direction)}`}>
            {forecast.direction}
          </span>
          <span className="text-[12px] text-[var(--text-tertiary)] tabular-nums ml-2 font-light">
            {move}%
          </span>
        </div>
      </div>

      <div className="mb-5">
        <div className="flex justify-between text-[11px] font-medium text-[var(--text-tertiary)] mb-2">
          <span>Consensus</span>
          <span className="tabular-nums text-[var(--cream-dim)]">{consensus}%</span>
        </div>
        <div className="h-[5px] bg-[var(--bg-tertiary)] overflow-hidden">
          <div
            className="h-full bg-[var(--accent)] transition-all duration-700 ease-out"
            style={{ width: `${consensus}%` }}
          />
        </div>
      </div>

      <p className="text-[11px] text-[var(--text-tertiary)] font-light">{date}</p>
    </a>
  );
}
