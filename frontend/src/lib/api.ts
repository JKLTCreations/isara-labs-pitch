import type { ForecastDetail, Forecast, Run, RunTrace, Signal, Debate, CalibrationProfile } from "./types";

const BASE = "/api";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }
  return res.json() as Promise<T>;
}

// Forecasts
export async function listForecasts(params?: {
  asset?: string;
  conviction?: string;
  limit?: number;
  offset?: number;
}): Promise<{ forecasts: Forecast[]; count: number }> {
  const qs = new URLSearchParams();
  if (params?.asset) qs.set("asset", params.asset);
  if (params?.conviction) qs.set("conviction", params.conviction);
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const q = qs.toString();
  return fetchJSON(`/forecasts${q ? `?${q}` : ""}`);
}

export async function getForecast(runId: string): Promise<ForecastDetail> {
  return fetchJSON(`/forecasts/${runId}`);
}

// Signals
export async function getSignals(
  runId: string
): Promise<{ run_id: string; signals: Signal[]; count: number }> {
  return fetchJSON(`/forecasts/${runId}/signals`);
}

export async function getAgentSignal(
  runId: string,
  agentId: string
): Promise<{ run_id: string; agent_id: string; signals: Signal[] }> {
  return fetchJSON(`/forecasts/${runId}/signals/${agentId}`);
}

// Runs
export async function listRuns(params?: {
  asset?: string;
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<{ runs: Run[]; total: number }> {
  const qs = new URLSearchParams();
  if (params?.asset) qs.set("asset", params.asset);
  if (params?.status) qs.set("status", params.status);
  if (params?.limit) qs.set("limit", String(params.limit));
  if (params?.offset) qs.set("offset", String(params.offset));
  const q = qs.toString();
  return fetchJSON(`/runs${q ? `?${q}` : ""}`);
}

export async function getDebate(
  runId: string
): Promise<{ run_id: string; total_rounds: number; rounds: Record<string, Debate[]>; exchanges: Debate[] }> {
  return fetchJSON(`/runs/${runId}/debate`);
}

export async function getRunTrace(runId: string): Promise<RunTrace> {
  return fetchJSON(`/runs/${runId}/trace`);
}

// Trigger new forecast
export async function triggerForecast(params: {
  asset: string;
  horizon: string;
  agents?: string[];
  skip_debate?: boolean;
}): Promise<{ run_id: string; status: string }> {
  const res = await fetch(`${BASE}/forecasts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }
  return res.json();
}

// Calibration
export async function getCalibrationDashboard(): Promise<{
  profiles: CalibrationProfile[];
  count: number;
}> {
  return fetchJSON("/runs/calibration");
}

export async function getAgentCalibration(
  agentId: string,
  asset?: string
): Promise<CalibrationProfile> {
  const qs = asset ? `?asset=${encodeURIComponent(asset)}` : "";
  return fetchJSON(`/runs/calibration/${agentId}${qs}`);
}
