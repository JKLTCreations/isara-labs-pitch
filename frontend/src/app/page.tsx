"use client";

import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import type { Forecast } from "@/lib/types";
import { listForecasts } from "@/lib/api";
import { ForecastCard } from "@/components/forecast-card";
import { NewForecastModal } from "@/components/new-forecast-modal";

export default function DashboardPage() {
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    listForecasts({ limit: 20 })
      .then((d) => setForecasts(d.forecasts))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="fade-up">
      <div className="flex items-center justify-between mb-10">
        <div>
          <h1 className="text-2xl font-semibold tracking-[-0.02em] text-[var(--cream)]">
            Forecasts
          </h1>
          <p className="text-[13px] text-[var(--text-tertiary)] mt-1 font-light">
            Active swarm consensus predictions
          </p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="inline-flex items-center gap-2 px-5 py-2.5 text-[13px] font-semibold text-[var(--cream)] bg-[var(--accent)] shadow-[var(--shadow-md)] transition-all duration-300 ease-out hover:bg-[var(--accent-hover)] hover:shadow-[var(--shadow-lg)] hover:translate-y-[-1px] active:translate-y-0"
        >
          <Plus size={15} strokeWidth={2.5} />
          New Forecast
        </button>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="skeleton h-48" />
          ))}
        </div>
      ) : forecasts.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-28 bg-[var(--bg-secondary)] border border-[var(--border)] shadow-[var(--shadow-md)]">
          <img src="/isara.png" alt="" className="w-12 h-12 rounded-full opacity-15 mb-6" />
          <p className="text-[15px] font-medium text-[var(--cream-dim)]">No forecasts yet</p>
          <p className="text-[13px] text-[var(--text-tertiary)] mt-1 font-light">
            Trigger a new forecast to get started.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {forecasts.map((f, i) => (
            <div key={f.id} className={`fade-up-d${Math.min(i + 1, 6)}`}>
              <ForecastCard forecast={f} />
            </div>
          ))}
        </div>
      )}

      <NewForecastModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </div>
  );
}
