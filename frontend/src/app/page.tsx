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
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Forecasts</h1>
          <p className="text-sm text-[var(--text-muted)]">
            Active and recent swarm forecasts
          </p>
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[var(--accent)] text-white text-sm font-medium hover:opacity-90 transition-opacity"
        >
          <Plus size={16} />
          New Forecast
        </button>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="h-44 rounded-lg border border-[var(--border)] bg-[var(--bg-card)] animate-pulse"
            />
          ))}
        </div>
      ) : forecasts.length === 0 ? (
        <div className="text-center py-20 text-[var(--text-muted)]">
          <p className="text-lg mb-2">No forecasts yet</p>
          <p className="text-sm">
            Trigger a new forecast to get started.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {forecasts.map((f) => (
            <ForecastCard key={f.id} forecast={f} />
          ))}
        </div>
      )}

      <NewForecastModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
      />
    </div>
  );
}
