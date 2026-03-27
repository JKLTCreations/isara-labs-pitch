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
      // noop
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#061210]/85 backdrop-blur-lg">
      <div className="relative w-full max-w-md bg-[var(--bg-secondary)] border border-[var(--border-hover)] p-8 shadow-[var(--shadow-xl)] fade-up">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 w-8 h-8 flex items-center justify-center text-[var(--text-tertiary)] hover:text-[var(--cream)] hover:bg-[var(--accent-subtle)] transition-all duration-200"
        >
          <X size={15} />
        </button>

        <h2 className="text-lg font-semibold tracking-[-0.01em] text-[var(--cream)] mb-7">New Forecast</h2>

        <div className="space-y-7">
          <div>
            <label className="block text-[10px] font-semibold uppercase tracking-widest text-[var(--text-tertiary)] mb-3">
              Asset
            </label>
            <div className="flex flex-wrap gap-2">
              {ASSETS.map((a) => (
                <button
                  key={a}
                  onClick={() => setAsset(a)}
                  className={`px-4 py-2 text-[13px] font-semibold transition-all duration-300 ${
                    asset === a
                      ? "bg-[var(--accent)] text-[var(--cream)] shadow-[var(--shadow-md)]"
                      : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border border-[var(--border)] hover:border-[var(--border-hover)] hover:text-[var(--cream)] hover:translate-y-[-1px]"
                  }`}
                >
                  {a}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-[10px] font-semibold uppercase tracking-widest text-[var(--text-tertiary)] mb-3">
              Horizon
            </label>
            <div className="flex gap-2">
              {HORIZONS.map((h) => (
                <button
                  key={h}
                  onClick={() => setHorizon(h)}
                  className={`px-4 py-2 text-[13px] font-semibold transition-all duration-300 ${
                    horizon === h
                      ? "bg-[var(--accent)] text-[var(--cream)] shadow-[var(--shadow-md)]"
                      : "bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border border-[var(--border)] hover:border-[var(--border-hover)] hover:text-[var(--cream)] hover:translate-y-[-1px]"
                  }`}
                >
                  {h}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full py-3 text-[13px] font-semibold text-[var(--cream)] bg-[var(--accent)] shadow-[var(--shadow-md)] transition-all duration-300 ease-out hover:bg-[var(--accent-hover)] hover:shadow-[var(--shadow-lg)] hover:translate-y-[-1px] active:translate-y-0 disabled:opacity-50"
          >
            {loading ? "Running swarm..." : "Run Forecast"}
          </button>

          {result && (
            <div className="p-4 bg-[var(--green-subtle)] border-l-2 border-[var(--green)]">
              <p className="text-[var(--green)] font-semibold text-[13px]">Forecast triggered</p>
              <p className="text-[var(--text-tertiary)] text-[11px] mt-1 font-light">
                Run ID:{" "}
                <a href={`/forecast/${result.run_id}`} className="text-[var(--accent-light)] hover:underline font-medium">
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
