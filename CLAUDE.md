# Swarm Forecaster — Multi-Agent Predictive Intelligence Engine

> A coordinated agent swarm that mirrors Isara's architecture: specialized AI agents that debate, disagree, and converge on high-conviction forecasts for commodities, geopolitics, and macroeconomic shifts.

---

## Vision

Isara proved that ~2,000 coordinated agents can forecast gold prices better than any single model. This project distills that insight into a buildable system: a **swarm of specialist agents** — each with distinct expertise, real-time data access, and structured signal output — orchestrated through the **OpenAI Agents SDK** into a consensus forecasting engine.

This is not prompt chaining. This is adversarial collaboration — agents that challenge each other's assumptions, surface blind spots, and produce calibrated forecasts with transparent reasoning chains.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR (Triage Agent)                  │
│         Receives forecast request → spawns specialist swarm         │
│         Manages rounds → triggers convergence protocol              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │ GEOPOLITICAL │  │   MACRO     │  │  SENTIMENT  │  │   QUANT   │ │
│  │   ANALYST    │  │  ECONOMIST  │  │   ANALYST   │  │  ANALYST  │ │
│  │              │  │             │  │             │  │           │ │
│  │ • Conflicts  │  │ • GDP/CPI   │  │ • News tone │  │ • Price   │ │
│  │ • Sanctions  │  │ • Rate path │  │ • Social    │  │   action  │ │
│  │ • Elections  │  │ • Trade     │  │ • Fear/greed│  │ • Correl. │ │
│  │ • Alliances  │  │ • Fiscal    │  │ • Positioning│ │ • Vol     │ │
│  └──────┬───────┘  └──────┬──────┘  └──────┬──────┘  └─────┬─────┘ │
│         │                 │                │               │       │
│         ▼                 ▼                ▼               ▼       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    SIGNAL BUS (Structured JSON)              │   │
│  │   { direction, magnitude, confidence, horizon, evidence[] } │   │
│  └─────────────────────────┬───────────────────────────────────┘   │
│                            │                                       │
│                            ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                 ADVERSARIAL DEBATE ROUND                     │   │
│  │   Agents review each other's signals → challenge weaknesses  │   │
│  │   Agents may revise confidence or direction after debate     │   │
│  └─────────────────────────┬───────────────────────────────────┘   │
│                            │                                       │
│                            ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   AGGREGATOR AGENT                           │   │
│  │   Confidence-weighted synthesis │ Disagreement detection     │   │
│  │   Bayesian signal combination   │ Calibrated final forecast  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                      MCP DATA LAYER                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │  FRED    │  │  NEWS    │  │  MARKET  │  │  ECONOMIC         │  │
│  │  Server  │  │  Server  │  │  Server  │  │  CALENDAR Server  │  │
│  └──────────┘  └──────────┘  └──────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Core Concepts

### 1. Agents Are Not Prompts — They Are Roles With Tools

Each agent is a fully instantiated `Agent` object from the OpenAI Agents SDK with:
- A **system identity** defining its analytical lens and cognitive biases
- **Dedicated tools** (function calls) that give it access to domain-specific data
- **Guardrails** that constrain output to structured signal schemas
- **Handoff capabilities** to pass context to other agents or escalate to the aggregator

### 2. The Signal Protocol

Every agent emits a **Signal** — a structured object, not free text:

```python
class Signal(BaseModel):
    agent_id: str                          # Which agent produced this
    asset: str                             # What is being forecast (e.g., "XAUUSD")
    direction: Literal["bullish", "bearish", "neutral"]
    magnitude: float                       # Expected % move (-1.0 to 1.0)
    confidence: float                      # 0.0 to 1.0, calibrated
    horizon: str                           # e.g., "7d", "30d", "90d"
    evidence: list[Evidence]               # Structured supporting data
    risks: list[str]                       # What could invalidate this signal
    contrarian_note: str | None            # What the consensus might be missing
```

```python
class Evidence(BaseModel):
    source: str                            # Data origin (e.g., "FRED:GDP", "Reuters")
    observation: str                       # What the data shows
    relevance: float                       # How much this drives the signal (0-1)
    timestamp: str                         # When this data was observed
```

This is the language agents speak. No ambiguity. No hallucinated confidence. Every claim is grounded in cited evidence.

### 3. Adversarial Debate Protocol

After initial signals are collected, agents enter a **debate round**:

1. Each agent receives all other agents' signals
2. Each agent writes a **challenge** to the signal it disagrees with most, citing specific evidence gaps or logical flaws
3. Challenged agents may **revise** their signal or **defend** with additional evidence
4. The debate transcript is passed to the aggregator as context

This prevents groupthink — the failure mode that kills ensemble forecasting systems. Isara's value proposition depends on agents that genuinely disagree, not echo chambers.

### 4. Confidence-Weighted Aggregation

The Aggregator agent does not simply average signals. It:

- **Weights by calibrated confidence** — an agent that says 0.9 confidence should be right ~90% of the time. Track and penalize miscalibration over time.
- **Detects divergence** — if geopolitical and macro agents strongly disagree, flag this as a high-uncertainty forecast rather than splitting the difference.
- **Applies Bayesian updating** — prior forecasts are updated with new signals, not replaced.
- **Produces a final Forecast object** with explicit uncertainty bounds.

```python
class Forecast(BaseModel):
    asset: str
    direction: Literal["bullish", "bearish", "neutral"]
    expected_move: float                   # Point estimate
    confidence_interval: tuple[float, float]  # 80% CI
    horizon: str
    conviction: Literal["low", "medium", "high"]
    consensus_strength: float              # How much agents agreed (0-1)
    key_drivers: list[str]                 # Top 3 reasons
    key_risks: list[str]                   # Top 3 risks
    dissenting_view: str | None            # Strongest counter-argument
    agent_signals: list[Signal]            # Full transparency
    debate_summary: str                    # What agents argued about
```

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Agent Orchestration | **OpenAI Agents SDK** (`openai-agents`) | Native multi-agent handoffs, guardrails, tracing — built for this exact pattern |
| LLM | **GPT-4.1** (agents), **GPT-4.1-mini** (data summarization) | 4.1 for reasoning-heavy agent work, mini for high-volume data preprocessing |
| Structured Output | **Pydantic + OpenAI Structured Outputs** | Type-safe signal protocol, zero parsing errors |
| Data Layer | **MCP Servers** (custom) | Standardized tool interface for financial data, news, economic indicators |
| Financial Data | **Alpha Vantage / yfinance / FRED API** | Real-time and historical market data, economic indicators |
| News & Sentiment | **NewsAPI / RSS feeds / Tavily** | Real-time news ingestion, sentiment scoring |
| Persistence | **SQLite** (signals + forecasts) | Lightweight, zero-config, sufficient for signal logging and backtesting |
| Tracing & Observability | **OpenAI Agents SDK Tracing** | Built-in trace visualization for debugging agent behavior |
| API Layer | **FastAPI** | Async-native, automatic OpenAPI docs, WebSocket support for live forecasts |
| Frontend | **Next.js 15 + Tailwind + shadcn/ui** | Dashboard for forecast visualization, agent signal inspection, debate replay |
| Charts | **Recharts or Lightweight Charts (TradingView)** | Time series visualization, signal overlay on price charts |

---

## Project Structure

```
isara-swarm-forecaster/
├── CLAUDE.md
├── README.md
├── pyproject.toml                         # uv/poetry project config
├── .env.example                           # API keys template
│
├── src/
│   ├── __init__.py
│   │
│   ├── agents/                            # Agent definitions
│   │   ├── __init__.py
│   │   ├── registry.py                    # Agent registry & factory
│   │   ├── geopolitical.py                # Geopolitical analyst agent
│   │   ├── macro.py                       # Macro-economics agent
│   │   ├── sentiment.py                   # Market sentiment agent
│   │   ├── quant.py                       # Quantitative/technical agent
│   │   └── aggregator.py                  # Consensus aggregator agent
│   │
│   ├── orchestrator/                      # Swarm coordination logic
│   │   ├── __init__.py
│   │   ├── swarm.py                       # Main orchestration loop
│   │   ├── debate.py                      # Adversarial debate protocol
│   │   └── rounds.py                      # Multi-round convergence logic
│   │
│   ├── signals/                           # Signal protocol & aggregation
│   │   ├── __init__.py
│   │   ├── schema.py                      # Signal, Evidence, Forecast models
│   │   ├── aggregation.py                 # Confidence-weighted aggregation
│   │   └── calibration.py                 # Confidence calibration tracking
│   │
│   ├── tools/                             # Function tools for agents
│   │   ├── __init__.py
│   │   ├── market_data.py                 # Price data, technicals, vol
│   │   ├── economic_indicators.py         # FRED data, GDP, CPI, rates
│   │   ├── news.py                        # News search & summarization
│   │   ├── sentiment.py                   # Social sentiment scoring
│   │   └── calendar.py                    # Economic event calendar
│   │
│   ├── mcp/                               # MCP server implementations
│   │   ├── __init__.py
│   │   ├── fred_server.py                 # FRED economic data MCP server
│   │   ├── market_server.py               # Market data MCP server
│   │   └── news_server.py                 # News & sentiment MCP server
│   │
│   ├── persistence/                       # Data storage
│   │   ├── __init__.py
│   │   ├── database.py                    # SQLite setup & queries
│   │   └── models.py                      # DB models (signals, forecasts, runs)
│   │
│   ├── api/                               # FastAPI backend
│   │   ├── __init__.py
│   │   ├── main.py                        # App entrypoint
│   │   ├── routes/
│   │   │   ├── forecasts.py               # GET/POST forecasts
│   │   │   ├── signals.py                 # GET agent signals
│   │   │   ├── runs.py                    # GET/POST forecast runs
│   │   │   └── ws.py                      # WebSocket for live updates
│   │   └── deps.py                        # Shared dependencies
│   │
│   └── config.py                          # Environment & app configuration
│
├── frontend/                              # Next.js dashboard
│   ├── package.json
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                       # Dashboard home — active forecasts
│   │   ├── forecast/[id]/page.tsx         # Single forecast deep-dive
│   │   └── runs/page.tsx                  # Historical runs & backtesting
│   ├── components/
│   │   ├── forecast-card.tsx              # Forecast summary card
│   │   ├── signal-panel.tsx               # Individual agent signal display
│   │   ├── debate-replay.tsx              # Debate round visualizer
│   │   ├── convergence-chart.tsx          # How signals evolved across rounds
│   │   ├── agent-avatar.tsx               # Agent identity & status
│   │   └── price-chart.tsx                # Asset price with signal overlay
│   └── lib/
│       ├── api.ts                         # API client
│       └── types.ts                       # Shared TypeScript types
│
├── scripts/
│   ├── run_forecast.py                    # CLI: trigger a single forecast run
│   ├── backtest.py                        # Run historical forecasts & score accuracy
│   └── seed_data.py                       # Seed DB with sample data
│
└── tests/
    ├── test_agents/                       # Agent behavior tests
    │   ├── test_geopolitical.py
    │   ├── test_macro.py
    │   ├── test_sentiment.py
    │   └── test_quant.py
    ├── test_orchestrator/                 # Orchestration tests
    │   ├── test_swarm.py
    │   └── test_debate.py
    ├── test_signals/                      # Signal protocol tests
    │   ├── test_schema.py
    │   └── test_aggregation.py
    └── test_api/                          # API endpoint tests
        └── test_routes.py
```

---

## Agent Specifications

### Geopolitical Analyst

**Identity:** Senior geopolitical risk analyst. Thinks in terms of power dynamics, alliances, escalation ladders, and second-order effects of policy decisions.

**Tools:**
- `search_news(query, region, days_back)` — Search recent geopolitical news
- `get_sanctions_data(country)` — Active sanctions and trade restrictions
- `get_election_calendar(region)` — Upcoming elections and polling data
- `get_conflict_monitor(region)` — Active conflicts and escalation indicators

**Cognitive Bias (intentional):** Overweights tail risks and geopolitical contagion. The swarm needs at least one agent that takes worst-case scenarios seriously.

---

### Macro-Economics Analyst

**Identity:** Central bank economist. Thinks in terms of monetary transmission mechanisms, yield curves, fiscal multipliers, and inflation dynamics.

**Tools:**
- `get_fred_series(series_id, period)` — Any FRED economic indicator
- `get_rate_expectations(currency)` — Fed funds futures, OIS curves
- `get_gdp_nowcast(country)` — Real-time GDP tracking estimates
- `get_inflation_breakdown(country)` — CPI/PCE component analysis

**Cognitive Bias (intentional):** Anchors heavily to historical macro regimes. Provides the "this has happened before" perspective.

---

### Sentiment Analyst

**Identity:** Behavioral finance specialist. Tracks crowd psychology, positioning extremes, and narrative shifts that precede market moves.

**Tools:**
- `get_fear_greed_index()` — CNN Fear & Greed or equivalent
- `get_news_sentiment(asset, days_back)` — Aggregated news sentiment scores
- `get_social_sentiment(asset, platform)` — Reddit/X sentiment analysis
- `get_positioning_data(asset)` — COT data, fund flows, options positioning

**Cognitive Bias (intentional):** Contrarian. When sentiment is extreme, this agent pushes back against the crowd.

---

### Quantitative Analyst

**Identity:** Systematic trader. Thinks in terms of price action, volatility regimes, correlations, and statistical anomalies. Distrusts narratives.

**Tools:**
- `get_price_data(asset, period, interval)` — OHLCV price data
- `get_technical_indicators(asset, indicators)` — RSI, MACD, Bollinger, etc.
- `get_volatility_surface(asset)` — Implied vol, term structure, skew
- `get_correlation_matrix(assets, period)` — Cross-asset correlation analysis

**Cognitive Bias (intentional):** Ignores narratives entirely. Only respects price and statistical evidence. This agent is the swarm's bullshit detector.

---

### Aggregator Agent

**Identity:** Chief Investment Officer. Synthesizes conflicting views into a coherent, actionable forecast. Expert at identifying when disagreement is informative vs. noise.

**Does NOT have data tools.** Only receives signals and debate transcripts from other agents. Its job is pure synthesis and judgment.

**Responsibilities:**
- Detect when agents are seeing fundamentally different regimes (high-uncertainty flag)
- Weight signals by historical calibration accuracy
- Produce a final `Forecast` object with explicit uncertainty bounds
- Write a human-readable executive summary

---

## Orchestration Flow

```python
# Pseudocode for a single forecast run

async def run_forecast(asset: str, horizon: str) -> Forecast:

    # Phase 1: Independent Analysis
    # All specialist agents run in parallel, no cross-talk
    signals: list[Signal] = await asyncio.gather(
        run_agent(geopolitical_agent, asset, horizon),
        run_agent(macro_agent, asset, horizon),
        run_agent(sentiment_agent, asset, horizon),
        run_agent(quant_agent, asset, horizon),
    )

    # Phase 2: Adversarial Debate (1-2 rounds)
    # Each agent sees all signals, writes challenges
    debate_transcript = []
    for round in range(MAX_DEBATE_ROUNDS):
        challenges = await run_debate_round(agents, signals)
        revised_signals = await collect_revisions(agents, challenges)
        debate_transcript.append(challenges)

        if convergence_detected(signals, revised_signals):
            break
        signals = revised_signals

    # Phase 3: Aggregation
    # Aggregator synthesizes final forecast
    forecast = await run_agent(
        aggregator_agent,
        signals=signals,
        debate=debate_transcript,
    )

    # Phase 4: Persist & Return
    await save_forecast(forecast)
    return forecast
```

---

## Development Guidelines

### Agent Development

- **Every agent must emit valid `Signal` objects.** Use OpenAI Structured Outputs to enforce this at the API level. Never parse free text into signals.
- **Agents must cite evidence.** Any signal with an empty `evidence` list is a bug. The guardrail should reject it.
- **System prompts are versioned.** Store them as constants in each agent module with a `PROMPT_VERSION` string. Changes to prompts must be documented.
- **Test agents in isolation first.** Each agent should produce a reasonable signal for a known historical scenario before being added to the swarm.

### Orchestration

- **Debate rounds are capped.** Default to 2 rounds. Infinite debate loops are a real risk — convergence detection must be implemented.
- **Convergence = direction agreement + confidence stability.** If all agents agree on direction and no agent's confidence shifted more than 0.1 in the last round, stop.
- **Timeouts are mandatory.** Each agent gets 60 seconds max per phase. A hung agent should not block the swarm.

### Data & Tools

- **All external data calls go through tool functions.** Agents never make raw HTTP requests.
- **Cache aggressively.** Financial data doesn't change intra-minute. Cache FRED data for 1 hour, price data for 1 minute, news for 15 minutes.
- **Every tool returns timestamps.** Agents must know how fresh their data is.

### Code Standards

- **Python 3.12+**, type hints everywhere, strict mypy
- **Pydantic v2** for all data models
- **async/await** throughout — agents run concurrently
- **uv** for dependency management
- Format with **ruff**, lint with **ruff**
- Tests with **pytest + pytest-asyncio**

---

## Environment Variables

```bash
# .env
OPENAI_API_KEY=sk-...                     # Required — GPT-4.1 access
ALPHA_VANTAGE_API_KEY=...                 # Market data
FRED_API_KEY=...                          # Economic indicators
NEWS_API_KEY=...                          # News search
TAVILY_API_KEY=...                        # Web search for agents (optional)

# Optional
DATABASE_URL=sqlite:///./data/forecasts.db
LOG_LEVEL=INFO
MAX_DEBATE_ROUNDS=2
AGENT_TIMEOUT_SECONDS=60
```

---

## Development Phases

### PHASES 1–5: COMPLETED

> Phases 1–5 are fully implemented and tested. **Read the code before starting Phase 6.**

---

### Onboarding: Read These Files First

Before writing any code, you MUST read and understand the existing codebase. Phases 1–5 built the entire backend engine. Your job (Phases 6–10) is to expose it, visualize it, harden it, and extend it.

**Start here — read in this order:**

1. **`src/signals/schema.py`** — The data contracts everything is built on. `Signal`, `Evidence`, `Challenge`, `Revision`, `Forecast`. Every field, every constraint. This is the language the system speaks.

2. **`src/agents/quant.py`** — Read ONE agent end-to-end to understand the pattern: system prompt with `PROMPT_VERSION`, `create_*_agent()` factory function, `Agent()` with `output_type=Signal`. Then skim `geopolitical.py`, `macro.py`, `sentiment.py` — same pattern, different tools and biases.

3. **`src/agents/aggregator.py`** — The CIO agent. Note that it has NO tools — pure synthesis. Read `build_aggregator_prompt()` to see how signals + debate context are assembled.

4. **`src/agents/registry.py`** — How agents are created and composed. `create_swarm()` returns a list of agents. `AGENT_FACTORIES` dict is the registry. Phase 9 will extend this.

5. **`src/orchestrator/swarm.py`** — **THE CORE FILE.** Read every line. This is the full pipeline:
   - `run_swarm()` orchestrates: parallel analysis → debate → aggregation
   - `_run_single_agent()` handles per-agent timeout and error catching
   - `_persist_signals()`, `_persist_debate()`, `_persist_forecast()` save everything to SQLite
   - `SwarmResult` dataclass is what the CLI and your API will consume
   - Note the `persist=True` flag and `run_id` tracking

6. **`src/orchestrator/debate.py`** — How agents challenge each other. `run_debate_round()` is the key function. Understand the flow: generate challenges in parallel → group by target → generate revisions in parallel → merge into updated signals.

7. **`src/orchestrator/rounds.py`** — Convergence detection: `convergence_detected()` checks direction agreement (≥75%) AND confidence stability (no agent shifted >0.1). `compute_consensus_strength()` produces a 0–1 score.

8. **`src/signals/aggregation.py`** — The math behind aggregation: `aggregate_direction()` (confidence-weighted vote), `compute_confidence_interval()` (spread-based), `determine_conviction()`, `find_dissenting_view()`, `extract_key_drivers()`, `extract_key_risks()`.

9. **`src/mcp/`** — Three MCP servers (`market_server.py`, `fred_server.py`, `news_server.py`). Each has its own cache TTL. `src/tools/` modules are thin wrappers that delegate to these. `src/mcp/client.py` re-exports everything.

10. **`src/persistence/database.py`** — SQLite schema with 5 tables: `forecast_runs`, `signals`, `debates`, `forecasts`, `calibration_log`. All functions are async. Key functions: `create_run()`, `save_signal()`, `save_debate()`, `save_forecast()`, `save_calibration_entry()`, `score_calibration()`, `get_agent_calibration()`, `list_runs()`, `get_run()`.

11. **`src/signals/calibration.py`** — `get_calibration_profile()` returns per-agent accuracy by confidence bucket. `get_swarm_calibration_weights()` returns a dict of agent_id → weight.

12. **`src/config.py`** — `get_config()` singleton. All env vars. `agent_model` = `gpt-4.1`, `fast_model` = `gpt-4.1-mini`.

13. **`scripts/run_forecast.py`** — The CLI. Shows how `run_swarm()` is called and how `SwarmResult` is consumed. Your API endpoints will do the same thing.

14. **`scripts/backtest.py`** and **`scripts/seed_data.py`** — Skim these. The seed script is useful for populating the DB during frontend development.

15. **`tests/`** — 37 tests, all passing. Run `python -m pytest tests/ -v` to verify before making any changes.

**After reading, run this to verify the full system:**
```bash
# Install deps
pip install -e ".[dev]"

# Run tests (37 should pass)
python -m pytest tests/ -v

# Seed sample data
python -m scripts.seed_data

# Verify DB
python -c "import sqlite3; conn = sqlite3.connect('data/forecasts.db'); [print(f'  {t}: {conn.execute(f\"SELECT COUNT(*) FROM {t}\").fetchone()[0]} rows') for t in ['forecast_runs','signals','debates','forecasts','calibration_log']]"
```

---

### What's Already Built (Phases 1–5)

| Layer | Status | Key Files |
|-------|--------|-----------|
| Signal Protocol | DONE | `src/signals/schema.py` — Signal, Evidence, Challenge, Revision, Forecast |
| 4 Specialist Agents | DONE | `src/agents/{quant,geopolitical,macro,sentiment}.py` |
| Aggregator Agent | DONE | `src/agents/aggregator.py` — CIO synthesis agent |
| Agent Registry | DONE | `src/agents/registry.py` — factory + `create_swarm()` |
| Swarm Orchestrator | DONE | `src/orchestrator/swarm.py` — parallel analysis → debate → aggregation |
| Adversarial Debate | DONE | `src/orchestrator/debate.py` — challenge/revision protocol |
| Convergence Detection | DONE | `src/orchestrator/rounds.py` — direction + confidence stability |
| Signal Aggregation | DONE | `src/signals/aggregation.py` — weighted voting, CI, conviction |
| MCP Market Server | DONE | `src/mcp/market_server.py` — price, technicals, vol, correlation (1min cache) |
| MCP FRED Server | DONE | `src/mcp/fred_server.py` — rates, inflation, economic series (1hr cache) |
| MCP News Server | DONE | `src/mcp/news_server.py` — search, sentiment, fear/greed, positioning (15min cache) |
| Tool Wrappers | DONE | `src/tools/` — thin delegates to MCP servers |
| SQLite Persistence | DONE | `src/persistence/database.py` — 5 tables, full async CRUD |
| Calibration Tracking | DONE | `src/signals/calibration.py` — per-agent accuracy by bucket |
| CLI | DONE | `scripts/run_forecast.py` — full pipeline with `--verbose`, `--no-debate`, `--agents` |
| Backtesting | DONE | `scripts/backtest.py` — scorecard with Brier, per-agent, per-conviction |
| Seed Data | DONE | `scripts/seed_data.py` — populates DB with 5 sample runs |
| Tests | DONE | 37 tests passing (schema, aggregation, convergence, persistence) |

**The swarm engine is complete. Your job is to expose it, visualize it, harden it, and extend it.**

---

### Phase 6 — FastAPI Backend (Days 22–26)

**Goal:** Expose the swarm as an API. Any frontend, script, or external system can trigger forecasts, inspect signals, and replay debates over HTTP and WebSocket.

**How it connects to existing code:**
- Your routes call `run_swarm()` from `src/orchestrator/swarm.py` — this is the same function the CLI uses
- `run_swarm()` returns a `SwarmResult` dataclass (see `swarm.py`). It has: `run_id`, `signals`, `debate_rounds`, `forecast`, `errors`, `elapsed_seconds`
- For reading historical data, use the async functions in `src/persistence/database.py`: `list_runs()`, `get_run()`, `get_agent_calibration()`
- The DB is already populated by the swarm (every `run_swarm(persist=True)` call writes to it). Your API just reads it back.
- Add `fastapi` and `uvicorn` to `pyproject.toml` dependencies (uvicorn is already installed as a transitive dep)

**Build:**
- `src/api/main.py` — FastAPI app with CORS, error handling, lifespan hook that calls `init_db()`
- `src/api/routes/forecasts.py`:
  - `POST /forecasts` — Takes `{"asset": "XAUUSD", "horizon": "30d"}`. Calls `run_swarm()` in a background task. Returns `{"run_id": "...", "status": "running"}` immediately.
  - `GET /forecasts/{id}` — Reads from `forecasts` table via `database.py`. Returns the full Forecast JSON.
  - `GET /forecasts` — Calls `list_runs()` with optional `?asset=XAUUSD` filter.
- `src/api/routes/signals.py`:
  - `GET /forecasts/{id}/signals` — Query `signals` table WHERE `run_id=id`
  - `GET /forecasts/{id}/signals/{agent_id}` — Single agent's signal with evidence JSON
- `src/api/routes/runs.py`:
  - `GET /runs` — List all runs from `forecast_runs` table
  - `GET /runs/{id}/debate` — Query `debates` table WHERE `run_id=id`, return challenges + responses
- `src/api/routes/ws.py`:
  - `WS /ws/forecast/{id}` — For live forecasts, you'll need to modify `run_swarm()` to accept a callback/queue that emits events as each phase completes. Use `asyncio.Queue` and have the WebSocket endpoint consume from it.
- `src/api/deps.py` — `get_config()` dependency, DB path

**Definition of Done:**
```bash
# Start the API
uvicorn src.api.main:app --reload

# Trigger a forecast
curl -X POST localhost:8000/forecasts \
  -H "Content-Type: application/json" \
  -d '{"asset": "XAUUSD", "horizon": "30d"}'
# → {"run_id": "abc-123", "status": "running"}

# Poll for result
curl localhost:8000/forecasts/abc-123
# → Full Forecast JSON with signals, debate, and consensus

# WebSocket shows live progress
websocat ws://localhost:8000/ws/forecast/abc-123
# → {"event": "agent_complete", "agent": "quant", "signal": {...}}
# → {"event": "debate_round", "round": 1, "challenges": [...]}
# → {"event": "forecast_complete", "forecast": {...}}

# OpenAPI docs auto-generated
open http://localhost:8000/docs
```

**DB queries you'll need** (add these to `database.py` if missing):
```python
# Get all signals for a run
async def get_signals_for_run(run_id: str) -> list[dict]: ...

# Get all debates for a run
async def get_debates_for_run(run_id: str) -> list[dict]: ...

# Get forecast for a run
async def get_forecast_for_run(run_id: str) -> dict | None: ...
```

**Files:**
```
src/api/__init__.py            ← NEW
src/api/main.py                ← NEW
src/api/deps.py                ← NEW
src/api/routes/__init__.py     ← NEW
src/api/routes/forecasts.py    ← NEW
src/api/routes/signals.py      ← NEW
src/api/routes/runs.py         ← NEW
src/api/routes/ws.py           ← NEW
src/persistence/database.py    ← MODIFY (add query functions for API reads)
pyproject.toml                 ← MODIFY (add fastapi to deps)
```

---

### Phase 7 — Dashboard Frontend (Days 27–34)

**Goal:** A visual command center that makes the swarm's reasoning transparent. This is the demo layer — what you'd show in a meeting. Every forecast is explorable down to individual agent evidence.

**How it connects to existing code:**
- The frontend talks to your Phase 6 FastAPI backend. All data comes from the API.
- Run `python -m scripts.seed_data` to populate the DB with 5 sample runs before starting frontend dev.
- The TypeScript types in `frontend/lib/types.ts` should mirror the Pydantic models in `src/signals/schema.py`. Key shapes: `Signal`, `Evidence`, `Forecast`, `Challenge`, `Revision`.
- The `SwarmResult` dataclass in `src/orchestrator/swarm.py` shows exactly what data is available per run.
- Agent IDs are: `quant_analyst`, `geopolitical_analyst`, `macro_economist`, `sentiment_analyst`, `aggregator`.

**Build:**
- `frontend/` — Next.js 15 app with App Router, Tailwind CSS, shadcn/ui
- **Dashboard Home** (`app/page.tsx`):
  - Active and recent forecasts in card layout
  - Each card: asset, direction arrow, conviction badge, consensus strength bar, timestamp
  - "New Forecast" button → modal with asset selector and horizon picker
  - Asset options: XAUUSD, CL1, SPX, DXY, BTC, TLT (from `ASSET_TICKER_MAP` in `src/mcp/market_server.py`)
- **Forecast Deep-Dive** (`app/forecast/[id]/page.tsx`):
  - Header: asset, direction, expected move, conviction, confidence interval
  - **Signal Panel** — 4-column layout, one per agent:
    - Agent avatar and name (use distinct colors per agent)
    - Direction + confidence gauge
    - Evidence list (collapsible, with source links)
    - Risk factors
    - Contrarian note (show only if non-null)
  - **Debate Replay** — Timeline visualization:
    - Each challenge rendered as a card with challenger → target
    - Revisions shown as before/after diffs on the signal
    - Expandable full text for each exchange
  - **Convergence Chart** — Line chart showing each agent's confidence across debate rounds
    - X-axis: round number, Y-axis: confidence
    - Color-coded by agent
    - Highlights where convergence occurred
    - Data comes from signals with `phase="initial"`, `phase="debate_r1"`, `phase="debate_r2"` in the signals table
  - **Price Chart** — Asset price with forecast overlay:
    - Historical price line (use Lightweight Charts / TradingView widget)
    - Forecast direction and confidence band projected forward
    - Agent signal markers on the timeline
- **Backtest History** (`app/runs/page.tsx`):
  - Table of all historical runs with accuracy scores
  - Per-agent calibration charts (data from `GET /calibration/{agent_id}` — add this endpoint in Phase 6 if missing)
  - Brier score trend over time
  - Filter by asset, date range, conviction

**Agent color scheme** (consistent across all components):
```
quant_analyst:       blue    (#3B82F6)
geopolitical_analyst: red    (#EF4444)
macro_economist:     green   (#22C55E)
sentiment_analyst:   purple  (#A855F7)
aggregator:          gold    (#EAB308)
```

**Component Breakdown:**
```
frontend/components/
├── forecast-card.tsx          # Summary card for dashboard grid
├── signal-panel.tsx           # Single agent's signal display
├── evidence-list.tsx          # Collapsible evidence items with sources
├── debate-replay.tsx          # Challenge/response timeline
├── convergence-chart.tsx      # Confidence evolution across rounds
├── price-chart.tsx            # TradingView-style price + forecast overlay
├── agent-avatar.tsx           # Agent identity badge with status indicator
├── conviction-badge.tsx       # Color-coded conviction level
├── new-forecast-modal.tsx     # Asset + horizon selector
└── calibration-chart.tsx      # Agent calibration curve visualization
```

**Definition of Done:**
- Dashboard loads and displays at least 3 historical forecast runs (seed with `scripts/seed_data.py`)
- Clicking a forecast card opens the deep-dive with all panels populated
- Debate replay shows the actual exchange between agents (not placeholder text)
- Convergence chart animates through rounds
- Price chart shows real historical price data with forecast overlay
- "New Forecast" triggers a run via the API and streams progress via WebSocket
- Responsive layout works on desktop (1440px+) and laptop (1024px+)

**Files:**
```
frontend/package.json          ← NEW
frontend/app/layout.tsx        ← NEW
frontend/app/page.tsx          ← NEW
frontend/app/forecast/[id]/page.tsx ← NEW
frontend/app/runs/page.tsx     ← NEW
frontend/components/*.tsx      ← NEW (10 components)
frontend/lib/api.ts            ← NEW
frontend/lib/types.ts          ← NEW
```

---

### Phase 8 — Production Hardening & Observability (Days 35–40)

**Goal:** Make the system reliable, observable, and debuggable. No demo-quality shortcuts — this phase is what separates a toy from a tool.

**How it connects to existing code:**
- `src/orchestrator/swarm.py` already has basic timeout handling (`asyncio.wait_for` with `config.agent_timeout_seconds`). Extend it.
- `src/orchestrator/debate.py` already catches exceptions per-agent and returns `None` on failure. Make this more robust.
- The MCP servers in `src/mcp/` have simple dict-based caches. Add circuit breaker logic there.
- The existing `_persist_*` functions in `swarm.py` are the right place to add trace/cost data.
- Add `structlog` to `pyproject.toml` dependencies.
- Agent timeout already works (60s default) — the improvement is graceful degradation (3/4 agents succeed = still produce forecast).

**Build:**
- **OpenAI Agents SDK Tracing** — Enable built-in trace collection for every agent run:
  - Tool call timing (which tools are slow, which fail)
  - Token usage per agent per phase (cost tracking)
  - Handoff traces (agent → aggregator flow)
  - Export traces to a viewable format (JSON + optional OpenTelemetry)
- **Structured Logging** — Replace print statements with `structlog`:
  - Every log line includes `run_id`, `agent_id`, `phase` for filterability
  - Log levels: DEBUG (tool call details), INFO (phase transitions), WARN (timeouts, retries), ERROR (failures)
- **Error Handling & Resilience:**
  - `swarm.py` already handles timeouts and errors per agent — add a `degraded` flag to `SwarmResult` when <4 agents succeed
  - API rate limit handling with exponential backoff in MCP servers
  - Circuit breaker for external data APIs (if yfinance is down, return last cached data and set a `stale: true` flag)
  - `debate.py` already skips failed challenges — add logging so you can see what failed and why
- **Input Validation & Guardrails:**
  - Validate asset symbols against `ASSET_TICKER_MAP` in `src/mcp/market_server.py`
  - Output guardrail already exists: Signal.confidence is capped at 0.95 in schema.py
  - Add an API-level validation: reject unknown assets before spawning the swarm
- **Cost Tracking:**
  - Add a `token_usage` column to `forecast_runs` table in `database.py`
  - Use the Agents SDK's response metadata to capture tokens per agent
  - Log estimated cost per forecast (GPT-4.1 pricing)

**Definition of Done:**
- A forecast run that encounters a yfinance outage still completes (degraded, flagged)
- One agent timing out doesn't block the swarm — the remaining 3 produce a forecast with a "reduced coverage" flag
- Every run has a trace viewable in the SDK's trace viewer
- Logs are structured and filterable: `cat logs/app.log | jq 'select(.agent_id == "quant")'`
- Token usage per run is logged and queryable

**Files:**
```
src/orchestrator/swarm.py      ← MODIFY (degraded flag, tracing, cost tracking)
src/orchestrator/debate.py     ← MODIFY (structured logging)
src/agents/*.py                ← MODIFY (structured logging in each agent)
src/mcp/*.py                   ← MODIFY (circuit breakers, stale data flags)
src/api/main.py                ← MODIFY (error middleware, request logging)
src/persistence/database.py    ← MODIFY (token_usage column)
src/config.py                  ← MODIFY (cost thresholds, logging config)
pyproject.toml                 ← MODIFY (add structlog)
```

---

### Phase 9 — Swarm Scaling & Dynamic Agents (Days 41–48)

**Goal:** Move from a fixed 4-agent swarm toward Isara's vision of dynamically composed swarms. The system should reason about *which* agents to spawn based on the forecast target.

**Build:**
- **Triage Agent** (`src/agents/triage.py`):
  - Receives the forecast request (asset + horizon + optional context)
  - Decides which specialist agents to spawn based on the asset:
    - Gold forecast → geopolitical + macro + sentiment + quant (standard)
    - Oil forecast → geopolitical + macro + quant + **energy specialist** (new)
    - CNY forecast → geopolitical + macro + **China specialist** (new) + quant
    - Election outcome → geopolitical + sentiment + **polling specialist** (new) + macro
  - Uses the OpenAI Agents SDK's native handoff mechanism to delegate to selected specialists
- **Agent Template System** (`src/agents/templates/`):
  - Base agent configuration that can be specialized via parameters
  - New agents defined as config (system prompt + tool list + bias description), not new code
  - Enables rapid creation of sub-specialists without touching orchestration logic
- **Sub-Specialist Agents:**
  - `energy.py` — Energy supply chain, OPEC dynamics, storage data
  - `china.py` — PBoC policy, CNY intervention, trade balance, property sector
  - `polling.py` — Election polling aggregation, prediction market data, historical accuracy of polls
- **Parallel Swarm Runs:**
  - For correlated assets (gold + USD + treasuries), run parallel swarms
  - Cross-swarm signal sharing: each swarm can read (not write) the other's signals
  - Correlation-aware aggregation: flag when correlated asset swarms disagree

**Definition of Done:**
```bash
# Oil forecast dynamically spawns energy specialist
python scripts/run_forecast.py --asset CL1 --horizon 30d
# → Triage agent selects: geopolitical, macro, quant, energy
# → Energy agent cites OPEC production data, strategic reserve levels

# Gold forecast uses standard swarm
python scripts/run_forecast.py --asset XAUUSD --horizon 30d
# → Triage agent selects: geopolitical, macro, sentiment, quant
# → Same behavior as Phase 3

# Multi-asset run
python scripts/run_forecast.py --asset XAUUSD,DXY,TLT --horizon 30d --correlated
# → 3 parallel swarms with cross-swarm signal visibility
# → Aggregator notes: "Gold bullish signal conflicts with USD strength signal"
```

**Files:**
```
src/agents/triage.py           ← NEW
src/agents/templates/          ← NEW (base config system)
src/agents/energy.py           ← NEW
src/agents/china.py            ← NEW
src/agents/polling.py          ← NEW
src/orchestrator/swarm.py      ← MODIFY (triage-based agent selection)
src/orchestrator/multi_swarm.py ← NEW (parallel correlated swarms)
src/agents/registry.py         ← MODIFY (dynamic registration from templates)
```

---

### Phase 10 — Agent Memory & Adaptive Calibration (Days 49–55)

**Goal:** Agents learn from their track record. An agent that has been consistently wrong about China de-risks its confidence on China-related forecasts. The swarm gets smarter over time without retraining any models.

**Build:**
- **Agent Memory Store** (`src/persistence/memory.py`):
  - Per-agent history: every signal the agent has produced, linked to the actual outcome
  - Queryable by asset, horizon, and time period
  - Agents receive a "track record summary" in their system prompt context:
    ```
    Your recent performance on XAUUSD (last 20 forecasts):
    - Directional accuracy: 65%
    - Your confidence of 0.8+ was correct 55% of the time (overconfident)
    - You tend to underweight geopolitical risk for gold
    ```
- **Adaptive Confidence Calibration** (`src/signals/calibration.py` — extend):
  - Platt scaling: fit a logistic regression on (raw_confidence → actual_accuracy) per agent
  - Auto-adjust: agent's raw 0.8 confidence gets mapped to calibrated 0.65 before aggregation
  - Recalibrate weekly or every N forecasts
- **Aggregator Dynamic Weighting:**
  - The aggregator receives each agent's calibration profile
  - Agents with better track records on the specific asset type get higher weight
  - Explicitly surfaces when an agent is "out of domain" (e.g., sentiment agent on a low-volume commodity)
- **Human-in-the-Loop Signal Injection:**
  - API endpoint: `POST /forecasts/{id}/signals` — inject a manual signal as a "human analyst" agent
  - The human signal enters the debate round alongside AI signals
  - Aggregator treats human signals with a configurable weight (default: equal to best-calibrated agent)

**Definition of Done:**
- After 20+ backtest runs, agent calibration weights visibly diverge (some agents are trusted more)
- An agent that was 50% accurate on oil gets lower weight for oil forecasts than one that was 75% accurate
- Human signal injection changes the final forecast output
- The calibration dashboard (frontend) shows per-agent calibration curves

**Files:**
```
src/persistence/memory.py      ← NEW
src/signals/calibration.py     ← MODIFY (Platt scaling, adaptive weights)
src/agents/aggregator.py       ← MODIFY (dynamic weighting from calibration)
src/agents/*.py                ← MODIFY (track record in system prompt context)
src/api/routes/signals.py      ← MODIFY (human signal injection endpoint)
frontend/app/runs/page.tsx     ← MODIFY (calibration dashboard)
frontend/components/calibration-chart.tsx ← NEW
```

---

### Phase Summary

| Phase | What | Days | Core Deliverable |
|-------|------|------|------------------|
| **1** | Foundation | 1–3 | Single agent emits a valid, evidence-backed signal |
| **2** | Specialist Swarm | 4–7 | 4 diverse agents run in parallel on same forecast |
| **3** | Debate & Aggregation | 8–12 | Agents challenge each other, aggregator produces consensus |
| **4** | MCP Data Layer | 13–16 | Standardized, cached data servers replace direct API calls |
| **5** | Persistence & Backtesting | 17–21 | Every run is stored, backtestable, and scored |
| **6** | API Backend | 22–26 | Full REST + WebSocket API for external access |
| **7** | Dashboard | 27–34 | Visual command center with debate replay and signal inspection |
| **8** | Production Hardening | 35–40 | Timeouts, tracing, resilience, cost tracking |
| **9** | Dynamic Swarms | 41–48 | Triage agent, sub-specialists, multi-asset correlation |
| **10** | Agent Memory | 49–55 | Track records, adaptive calibration, human-in-the-loop |

**Phases 1–3** = the core intellectual contribution (the swarm works)
**Phases 4–6** = production infrastructure (the swarm is usable)
**Phases 7–8** = presentation and reliability (the swarm is demoable and trustworthy)
**Phases 9–10** = the Isara differentiator (the swarm scales and learns)

---

## Key Metrics to Track

| Metric | What It Measures | Why It Matters |
|--------|-----------------|----------------|
| **Directional Accuracy** | % of forecasts where direction was correct | The most basic measure of forecast quality |
| **Calibration Score** | Does 70% confidence = ~70% accuracy? | Overconfident agents destroy the aggregation math |
| **Consensus Strength** | How often agents agree before debate | Low consensus = the swarm is surfacing genuine uncertainty |
| **Debate Impact** | How often debate changes the final forecast | If debate never changes anything, it's theater |
| **Signal Diversity** | Correlation between agent signals | High correlation = agents are redundant, not diverse |
| **Time to Forecast** | End-to-end latency | Matters for production deployment |

---

## Backtest Protocol

The system must be backtestable. For any historical date:

1. Restrict all data tools to only return data available **before** that date
2. Run the full swarm pipeline
3. Compare the forecast to what actually happened
4. Log accuracy metrics per agent and for the aggregated forecast

This is how you prove the system works — not with demos, but with auditable historical performance.

---

## What Makes This Different From "Just Calling GPT-4 Four Times"

1. **Structured Signal Protocol** — Agents don't chat. They emit typed, evidence-backed signals. This is a data pipeline, not a conversation.
2. **Adversarial Debate** — Agents actively challenge each other. Groupthink is the default failure mode of multi-agent systems. Debate breaks it.
3. **Intentional Cognitive Diversity** — Each agent has a deliberate analytical bias. The quant ignores narratives. The geopolitical analyst overweights tail risks. The sentiment agent is contrarian. This is ensemble design, not prompt variation.
4. **Calibration Tracking** — Confidence scores are meaningless unless tracked and penalized over time. The system learns which agents to trust more.
5. **Transparent Reasoning** — Every forecast includes the full signal chain, debate transcript, and dissenting view. No black boxes.
6. **Real Data Grounding** — Agents have tools that return real market data, economic indicators, and news. Forecasts are grounded in facts, not training data.

---

## References

- [OpenAI Agents SDK Documentation](https://openai.github.io/openai-agents-python/)
- [Isara — Zhang & Gasztowtt, "Multi-Agent Systems for Policy Analysis" (2024)](https://arxiv.org/)
- [Superforecasting — Philip Tetlock](https://en.wikipedia.org/wiki/Superforecasting) — The intellectual foundation for calibrated, diverse-perspective forecasting
- [Prediction Markets & Information Aggregation](https://en.wikipedia.org/wiki/Prediction_market) — Why diverse, independent signals beat individual experts
- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs) — Enforcing typed agent responses
