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

### Phase 1 — Foundation: Signal Protocol & Single Agent (Days 1–3)

**Goal:** Establish the core data contracts and prove a single agent can ingest real data and emit a valid, structured signal. Nothing works without this foundation.

**Build:**
- `src/signals/schema.py` — `Signal`, `Evidence`, `Forecast` Pydantic models with full validation (confidence clamped 0–1, non-empty evidence, valid horizons)
- `src/config.py` — Environment config loader, API key validation, app settings
- `src/agents/quant.py` — The Quantitative Analyst as the first agent (chosen because it depends on the most concrete, testable data — prices and indicators)
- `src/tools/market_data.py` — `get_price_data()` and `get_technical_indicators()` using yfinance (free, no API key needed to start)
- `scripts/run_forecast.py` — Bare-bones CLI: `python scripts/run_forecast.py --asset XAUUSD --horizon 30d`
- `pyproject.toml` — Project config with `openai-agents`, `pydantic`, `yfinance`, `python-dotenv`
- `.env.example` — Template with all required keys

**Definition of Done:**
```bash
python scripts/run_forecast.py --asset XAUUSD --horizon 30d
# → Prints a valid Signal JSON with direction, confidence, and ≥2 evidence items
# → Evidence references real price data with timestamps
# → Entire run completes in <30 seconds
```

**Key Decisions:**
- Use OpenAI Structured Outputs from day 1 — never allow free-text signals, even in development
- yfinance for initial market data (free), swap to Alpha Vantage later for production reliability
- The quant agent is the canary — if it can't produce a grounded signal, the architecture is wrong

**Files:**
```
src/signals/schema.py          ← NEW
src/config.py                  ← NEW
src/agents/__init__.py         ← NEW
src/agents/quant.py            ← NEW
src/tools/__init__.py          ← NEW
src/tools/market_data.py       ← NEW
scripts/run_forecast.py        ← NEW
pyproject.toml                 ← NEW
.env.example                   ← NEW
```

---

### Phase 2 — The Specialist Swarm (Days 4–7)

**Goal:** Build all four specialist agents, each with distinct tools and cognitive identity, running in parallel on the same forecast request.

**Build:**
- `src/agents/geopolitical.py` — Geopolitical analyst with news search and conflict monitoring tools
- `src/agents/macro.py` — Macro-economics analyst with FRED integration
- `src/agents/sentiment.py` — Sentiment analyst with news sentiment and social tools
- `src/agents/registry.py` — Agent factory that instantiates all specialists from config
- `src/tools/economic_indicators.py` — FRED API wrapper (`get_fred_series`, `get_inflation_breakdown`)
- `src/tools/news.py` — NewsAPI or Tavily wrapper (`search_news`, `get_news_sentiment`)
- `src/tools/sentiment.py` — Social sentiment scoring (`get_fear_greed_index`, `get_social_sentiment`)
- `src/tools/calendar.py` — Economic event calendar
- `src/orchestrator/swarm.py` — Parallel agent execution: spawns all 4 agents via `asyncio.gather`, collects signals

**Definition of Done:**
```bash
python scripts/run_forecast.py --asset XAUUSD --horizon 30d
# → 4 signals printed, one per agent
# → Each signal has distinct evidence sources (no two agents cite the same data)
# → All 4 agents complete within 60 seconds total (parallel execution)
# → Each agent's signal reflects its cognitive bias:
#    - Quant cites price levels and RSI
#    - Macro cites GDP and rate expectations
#    - Geopolitical cites news events and risk factors
#    - Sentiment cites crowd positioning and fear/greed
```

**Key Decisions:**
- Agents run fully independently in this phase — no cross-talk yet. This isolates agent quality issues from orchestration issues.
- Each agent gets a 60-second timeout. If it can't produce a signal in 60s, it's doing too much.
- The registry pattern allows dynamically enabling/disabling agents by config — foundation for Phase 7's dynamic spawning.

**Files:**
```
src/agents/geopolitical.py     ← NEW
src/agents/macro.py            ← NEW
src/agents/sentiment.py        ← NEW
src/agents/registry.py         ← NEW
src/tools/economic_indicators.py ← NEW
src/tools/news.py              ← NEW
src/tools/sentiment.py         ← NEW
src/tools/calendar.py          ← NEW
src/orchestrator/__init__.py   ← NEW
src/orchestrator/swarm.py      ← NEW
scripts/run_forecast.py        ← MODIFY (use orchestrator instead of single agent)
```

---

### Phase 3 — Adversarial Debate & Aggregation (Days 8–12)

**Goal:** The hardest phase. Implement the debate protocol that prevents groupthink and the aggregation logic that produces a single consensus forecast. This is what separates "multi-agent" from "multi-prompt."

**Build:**
- `src/orchestrator/debate.py` — The debate engine:
  - Round 1: Each agent receives all other signals, writes a structured `Challenge` targeting the signal it most disagrees with
  - Challenged agents respond with either a `Revision` (updated signal) or a `Defense` (rebuttal with new evidence)
  - Round 2 (optional): Only triggers if signals still diverge significantly
- `src/orchestrator/rounds.py` — Convergence detection logic:
  - Direction convergence: ≥3 of 4 agents agree on direction
  - Confidence stability: No agent shifted confidence >0.1 since last round
  - Max rounds hard cap: 2 (never let agents debate forever)
- `src/signals/aggregation.py` — Confidence-weighted signal combination:
  - Weighted directional vote (confidence × direction)
  - Uncertainty quantification from signal dispersion
  - Disagreement flagging when agents are split 2-2
- `src/agents/aggregator.py` — The Aggregator agent that receives signals + debate transcript and produces the final `Forecast` object

**New Schemas:**
```python
class Challenge(BaseModel):
    challenger_id: str              # Who is challenging
    target_id: str                  # Whose signal is being challenged
    argument: str                   # The specific critique
    evidence_gap: str               # What data the target agent missed
    suggested_revision: str         # What the challenger thinks should change

class Revision(BaseModel):
    agent_id: str
    original_signal: Signal
    revised_signal: Signal
    revision_reason: str            # What convinced them to change
    # OR
    defense: str | None             # Why they're standing firm
```

**Definition of Done:**
```bash
python scripts/run_forecast.py --asset XAUUSD --horizon 30d --verbose
# → Phase 1: 4 independent signals
# → Phase 2: Debate round with ≥2 challenges issued
# → At least 1 agent revises their signal after challenge
# → Phase 3: Aggregator produces a Forecast with:
#    - consensus_strength score reflecting actual agreement level
#    - dissenting_view capturing the strongest counter-argument
#    - debate_summary explaining what agents argued about
# → Full run completes in <90 seconds
```

**Why This Is Hard:**
- Debate prompts must be carefully designed to produce *substantive* challenges, not polite agreement. The system prompt must explicitly instruct agents to find flaws.
- Convergence detection is nuanced — you don't want to stop debate too early (agents haven't genuinely engaged) or too late (circular arguments).
- The aggregator must handle the 2-2 split case gracefully — this should produce a "low conviction" forecast, not a forced consensus.

**Files:**
```
src/orchestrator/debate.py     ← NEW
src/orchestrator/rounds.py     ← NEW
src/signals/aggregation.py     ← NEW
src/agents/aggregator.py       ← NEW
src/signals/schema.py          ← MODIFY (add Challenge, Revision, Defense)
src/orchestrator/swarm.py      ← MODIFY (integrate debate + aggregation into flow)
```

---

### Phase 4 — MCP Data Servers (Days 13–16)

**Goal:** Replace the direct API wrappers with MCP servers. This standardizes the data layer, makes tools reusable across agents, and demonstrates production-grade data architecture.

**Build:**
- `src/mcp/fred_server.py` — MCP server exposing FRED economic data:
  - `get_series` — Fetch any FRED series by ID
  - `get_rate_expectations` — Fed funds futures derived data
  - `get_gdp_nowcast` — GDP tracking composite
  - Built-in caching (1-hour TTL for economic data)
- `src/mcp/market_server.py` — MCP server for market data:
  - `get_price_data` — OHLCV with configurable intervals
  - `get_technical_indicators` — Computed on-server (RSI, MACD, Bollinger)
  - `get_volatility` — Historical and implied vol data
  - `get_correlation_matrix` — Cross-asset correlations
  - Built-in caching (1-minute TTL for price data)
- `src/mcp/news_server.py` — MCP server for news and sentiment:
  - `search_news` — Full-text news search with region/topic filters
  - `get_sentiment_score` — Aggregated sentiment for an asset
  - `get_social_buzz` — Social media mention volume and sentiment
  - Built-in caching (15-minute TTL for news)
- Refactor all agent tool definitions to use MCP server connections instead of direct API calls

**Definition of Done:**
```bash
# Each MCP server runs standalone and is testable independently
python -m src.mcp.fred_server    # Starts FRED MCP server
python -m src.mcp.market_server  # Starts market data MCP server
python -m src.mcp.news_server    # Starts news MCP server

# Full forecast still works end-to-end with MCP backends
python scripts/run_forecast.py --asset XAUUSD --horizon 30d
# → Same output as Phase 3, but data flows through MCP servers
# → Caching confirmed: second run within TTL shows cached responses
```

**Why MCP:**
- Agents get a standardized tool interface — swap data providers without changing agent code
- Caching lives in one place (the server), not scattered across tool functions
- MCP servers are independently deployable and testable
- Demonstrates to Isara's team that you understand production data infrastructure, not just prompt engineering

**Files:**
```
src/mcp/__init__.py            ← NEW
src/mcp/fred_server.py         ← NEW
src/mcp/market_server.py       ← NEW
src/mcp/news_server.py         ← NEW
src/tools/market_data.py       ← MODIFY (delegate to MCP)
src/tools/economic_indicators.py ← MODIFY (delegate to MCP)
src/tools/news.py              ← MODIFY (delegate to MCP)
src/tools/sentiment.py         ← MODIFY (delegate to MCP)
```

---

### Phase 5 — Persistence, Backtesting & Calibration (Days 17–21)

**Goal:** Make the system auditable. Every forecast run, every signal, every debate exchange is persisted. Build the backtesting harness that proves the swarm works on historical data. Begin tracking agent calibration.

**Build:**
- `src/persistence/database.py` — SQLite setup with async access (aiosqlite):
  - `forecast_runs` table — One row per orchestration run (id, asset, horizon, timestamp, status)
  - `signals` table — Every signal from every agent, linked to its run
  - `debates` table — Challenge/revision pairs with full text
  - `forecasts` table — Final aggregated forecast per run
  - `calibration_log` table — Forecast vs. actual outcome for scoring
- `src/persistence/models.py` — SQLAlchemy-style dataclass models (or raw SQL — keep it simple)
- `src/signals/calibration.py` — Calibration tracker:
  - For each agent, track (predicted_direction, confidence) vs actual outcome
  - Compute calibration curve: group predictions by confidence bucket, measure actual hit rate
  - Produce a `calibration_weight` per agent that the aggregator can use
- `scripts/backtest.py` — Backtesting harness:
  - Takes a date range and asset
  - For each date, restricts all data tools to only serve data before that date (time-travel guard)
  - Runs the full swarm pipeline
  - Compares forecast to actual price movement
  - Outputs a scorecard: directional accuracy, calibration score, Brier score, per-agent breakdown
- `scripts/seed_data.py` — Seed the database with sample forecast runs for development

**Definition of Done:**
```bash
# Run a backtest over 10 historical dates
python scripts/backtest.py --asset XAUUSD --start 2025-01-01 --end 2025-10-01 --interval monthly
# → Runs 10 forecast simulations
# → Prints scorecard:
#    Directional Accuracy: 7/10 (70%)
#    Brier Score: 0.21
#    Best Agent: quant (80% directional accuracy)
#    Worst Agent: sentiment (50% directional accuracy)
#    Calibration: macro agent overconfident (says 0.8, hits 0.6)

# All runs persisted to SQLite
python -c "import sqlite3; print(sqlite3.connect('data/forecasts.db').execute('SELECT COUNT(*) FROM forecast_runs').fetchone())"
# → (10,)
```

**Key Design Decisions:**
- SQLite, not Postgres. This is a single-user research tool, not a web app. Zero config, ships as a file.
- Time-travel guard is critical for backtest integrity — if an agent can see future data, the backtest is meaningless
- Calibration weights update slowly (exponential moving average) to avoid overreacting to small samples

**Files:**
```
src/persistence/__init__.py    ← NEW
src/persistence/database.py    ← NEW
src/persistence/models.py      ← NEW
src/signals/calibration.py     ← NEW
scripts/backtest.py            ← NEW
scripts/seed_data.py           ← NEW
src/signals/aggregation.py     ← MODIFY (use calibration weights)
src/orchestrator/swarm.py      ← MODIFY (persist runs, signals, debates)
```

---

### Phase 6 — FastAPI Backend (Days 22–26)

**Goal:** Expose the swarm as an API. Any frontend, script, or external system can trigger forecasts, inspect signals, and replay debates over HTTP and WebSocket.

**Build:**
- `src/api/main.py` — FastAPI app with CORS, error handling, lifespan hooks (start MCP servers on boot)
- `src/api/routes/forecasts.py`:
  - `POST /forecasts` — Trigger a new forecast run (asset, horizon). Returns run ID immediately, processes async.
  - `GET /forecasts/{id}` — Get completed forecast with full signal chain and debate summary
  - `GET /forecasts` — List all forecasts with pagination and filters (asset, date range, conviction level)
- `src/api/routes/signals.py`:
  - `GET /forecasts/{id}/signals` — All agent signals for a specific run
  - `GET /forecasts/{id}/signals/{agent_id}` — Single agent's signal with full evidence
- `src/api/routes/runs.py`:
  - `GET /runs` — List all orchestration runs with status and timing
  - `GET /runs/{id}/debate` — Full debate transcript for a run
  - `GET /runs/{id}/trace` — Agent execution trace (timing, tool calls, token usage)
- `src/api/routes/ws.py`:
  - `WS /ws/forecast/{id}` — Live stream of forecast progress: agent completion events, debate rounds, final result
- `src/api/deps.py` — Shared dependencies: database session, agent registry, config

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
```

---

### Phase 7 — Dashboard Frontend (Days 27–34)

**Goal:** A visual command center that makes the swarm's reasoning transparent. This is the demo layer — what you'd show in a meeting. Every forecast is explorable down to individual agent evidence.

**Build:**
- `frontend/` — Next.js 15 app with App Router, Tailwind CSS, shadcn/ui
- **Dashboard Home** (`app/page.tsx`):
  - Active and recent forecasts in card layout
  - Each card: asset, direction arrow, conviction badge, consensus strength bar, timestamp
  - "New Forecast" button → modal with asset selector and horizon picker
- **Forecast Deep-Dive** (`app/forecast/[id]/page.tsx`):
  - Header: asset, direction, expected move, conviction, confidence interval
  - **Signal Panel** — 4-column layout, one per agent:
    - Agent avatar and name
    - Direction + confidence gauge
    - Evidence list (collapsible, with source links)
    - Risk factors
    - Contrarian note
  - **Debate Replay** — Timeline visualization:
    - Each challenge rendered as a card with challenger → target
    - Revisions shown as before/after diffs on the signal
    - Expandable full text for each exchange
  - **Convergence Chart** — Line chart showing each agent's confidence across debate rounds
    - X-axis: round number, Y-axis: confidence
    - Color-coded by agent
    - Highlights where convergence occurred
  - **Price Chart** — Asset price with forecast overlay:
    - Historical price line (Lightweight Charts / TradingView widget)
    - Forecast direction and confidence band projected forward
    - Agent signal markers on the timeline
- **Backtest History** (`app/runs/page.tsx`):
  - Table of all historical runs with accuracy scores
  - Per-agent calibration charts
  - Brier score trend over time
  - Filter by asset, date range, conviction

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
- Dashboard loads and displays at least 3 historical forecast runs
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
  - Agent timeout enforcement: 60s per agent, graceful degradation (run forecast with 3/4 agents if one times out)
  - API rate limit handling with exponential backoff
  - Circuit breaker for external data APIs (if FRED is down, use cached data and flag staleness)
  - Graceful fallback: if debate round fails, skip to aggregation with Round 0 signals
- **Input Validation & Guardrails:**
  - Validate asset symbols against a known whitelist
  - Reject signals with hallucinated evidence (cross-check cited data sources against actual tool call results)
  - Output guardrail: reject forecasts with confidence >0.95 (nothing is that certain)
- **Cost Tracking:**
  - Log tokens consumed per run, per agent, per phase
  - Estimated cost per forecast (useful for pricing decisions)
  - Alert threshold: warn if a single run exceeds $X

**Definition of Done:**
- A forecast run that encounters a FRED API outage still completes (degraded, flagged)
- One agent timing out doesn't block the swarm — the remaining 3 produce a forecast with a "reduced coverage" flag
- Every run has a trace viewable in the SDK's trace viewer
- Logs are structured and filterable: `cat logs/app.log | jq 'select(.agent_id == "quant")'`
- Token usage per run is logged and queryable

**Files:**
```
src/orchestrator/swarm.py      ← MODIFY (timeouts, fallbacks, tracing)
src/orchestrator/debate.py     ← MODIFY (graceful degradation)
src/agents/*.py                ← MODIFY (structured logging in each agent)
src/tools/*.py                 ← MODIFY (retry logic, circuit breakers)
src/api/main.py                ← MODIFY (error middleware, request logging)
src/config.py                  ← MODIFY (cost thresholds, timeouts config)
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
