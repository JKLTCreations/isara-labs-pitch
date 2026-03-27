"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { triggerForecast } from "@/lib/api";

const ASSETS = ["XAUUSD", "CL1", "SPX", "DXY", "BTC", "TLT"];
const HORIZONS = ["7d", "30d", "90d"];

export function NewForecastModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const [asset, setAsset] = useState("XAUUSD");
  const [horizon, setHorizon] = useState("30d");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ run_id: string } | null>(null);

  if (!open) return null;

  async function handleSubmit() {
    setLoading(true);
    setResult(null);
    try {
      const res = await triggerForecast({ asset, horizon });
      setResult(res);
    } catch {
      // Error handled by clearing loading
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="relative w-full max-w-md rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-6">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-[var(--text-muted)] hover:text-[var(--text)]"
        >
          <X size={18} />
        </button>

        <h2 className="text-lg font-semibold mb-4">New Forecast</h2>

        <div className="space-y-4">
          {/* Asset */}
          <div>
            <label className="block text-sm text-[var(--text-muted)] mb-1">
              Asset
            </label>
            <div className="flex flex-wrap gap-2">
              {ASSETS.map((a) => (
                <button
                  key={a}
                  onClick={() => setAsset(a)}
                  className={`px-3 py-1.5 rounded text-sm border transition-colors ${
                    asset === a
                      ? "border-[var(--accent)] bg-[var(--accent)]/20 text-[var(--text)]"
                      : "border-[var(--border)] text-[var(--text-muted)] hover:border-[var(--text-muted)]"
                  }`}
                >
                  {a}
                </button>
              ))}
            </div>
          </div>

          {/* Horizon */}
          <div>
            <label className="block text-sm text-[var(--text-muted)] mb-1">
              Horizon
            </label>
            <div className="flex gap-2">
              {HORIZONS.map((h) => (
                <button
                  key={h}
                  onClick={() => setHorizon(h)}
                  className={`px-3 py-1.5 rounded text-sm border transition-colors ${
                    horizon === h
                      ? "border-[var(--accent)] bg-[var(--accent)]/20 text-[var(--text)]"
                      : "border-[var(--border)] text-[var(--text-muted)] hover:border-[var(--text-muted)]"
                  }`}
                >
                  {h}
                </button>
              ))}
            </div>
          </div>

          {/* Submit */}
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full py-2 rounded bg-[var(--accent)] text-white font-medium text-sm hover:opacity-90 disabled:opacity-50 transition-opacity"
          >
            {loading ? "Running swarm..." : "Run Forecast"}
          </button>

          {/* Result */}
          {result && (
            <div className="p-3 rounded bg-green-500/10 border border-green-500/30 text-sm">
              <p className="text-green-400 font-medium">Forecast triggered</p>
              <p className="text-[var(--text-muted)] text-xs mt-1">
                Run ID:{" "}
                <a
                  href={`/forecast/${result.run_id}`}
                  className="underline text-[var(--accent)]"
                >
                  {result.run_id}
                </a>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
