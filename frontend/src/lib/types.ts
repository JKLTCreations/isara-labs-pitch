export interface Run {
  id: string;
  asset: string;
  horizon: string;
  status: string;
  agent_count: number;
  debate_rounds: number;
  elapsed_seconds: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface Evidence {
  source: string;
  observation: string;
  relevance: number;
  timestamp: string;
}

export interface Signal {
  id: string;
  run_id: string;
  agent_id: string;
  phase: string;
  direction: "bullish" | "bearish" | "neutral";
  magnitude: number;
  confidence: number;
  horizon: string;
  evidence: Evidence[];
  risks: string[];
  contrarian_note: string | null;
  created_at: string;
}

export interface Debate {
  id: string;
  run_id: string;
  round_number: number;
  challenger_id: string;
  target_id: string;
  argument: string;
  evidence_gap: string;
  suggested_revision: string;
  response_type: "revision" | "defense" | null;
  response_text: string | null;
  created_at: string;
}

export interface Forecast {
  id: string;
  run_id: string;
  asset: string;
  direction: "bullish" | "bearish" | "neutral";
  expected_move: number;
  ci_lower: number;
  ci_upper: number;
  horizon: string;
  conviction: "low" | "medium" | "high";
  consensus_strength: number;
  key_drivers: string[];
  key_risks: string[];
  dissenting_view: string | null;
  debate_summary: string;
  created_at: string;
}

export interface ForecastDetail {
  run: Run;
  forecast: Forecast | null;
  signals: Signal[];
  debates: Debate[];
}

export interface AgentTrace {
  agent_id: string;
  signal_count: number;
  phases: string[];
}

export interface RunTrace {
  run_id: string;
  run: Run;
  elapsed_seconds: number | null;
  agent_count: number;
  debate_rounds: number;
  phases: Record<string, number>;
  agents: AgentTrace[];
  signals: Signal[];
  debate_exchanges: number;
  calibration_entries: number;
}
