# Swarm Forecaster

A multi-agent adversarial forecasting engine that coordinates specialized AI agents to debate, disagree, and converge on high-conviction forecasts for commodities, geopolitics, and macroeconomic shifts.

Built on the OpenAI Agents SDK, the system mirrors Isara's architecture: a swarm of specialist agents — each with distinct expertise, real-time data access, and structured signal output — orchestrated through adversarial debate into calibrated consensus forecasts.

---

## How It Works

```
Forecast Request
       │
       ▼
┌─────────────┐
│   Triage    │──── Selects optimal agent team based on asset
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────────┐
│  Phase 1: Independent Analysis (parallel)    │
│                                              │
│  Quant ─── Macro ─── Geopolitical ─── Sent. │
│    │          │           │              │   │
│    ▼          ▼           ▼              ▼   │
│           Structured Signals                 │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│  Phase 2: Adversarial Debate (1-2 rounds)    │
│                                              │
│  Agents challenge each other's signals       │
│  Revise or defend with new evidence          │
│  Convergence detection stops early if needed │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────┐
│  Phase 3: Aggregation                        │
│                                              │
│  Confidence-weighted synthesis               │
│  Calibration-adjusted agent weights          │
│  Disagreement detection + uncertainty bounds │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
            Final Forecast
   (direction, magnitude, CI, conviction,
    key drivers, risks, dissenting view)
```

---

## Agents

| Agent | Role | Evidence Sources | Cognitive Bias |
|-------|------|------------------|----------------|
| **Quantitative Analyst** | Price action, technicals, volatility regimes, correlations | Price data, technicals (RSI/MACD/Bollinger), multi-timeframe volatility, cross-asset momentum, correlation matrix | Ignores narratives — only respects price and statistical evidence |
| **Macro Economist** | GDP, CPI, rate paths, fiscal policy, yield curves | FRED series, rate expectations, full treasury curve, inflation breakdown, credit spreads | Anchors to historical macro regimes |
| **Geopolitical Analyst** | Conflicts, sanctions, elections, alliances | News search, news sentiment scoring, cross-asset momentum (safe haven pricing), economic calendar | Overweights tail risks and contagion |
| **Sentiment Analyst** | News tone, social sentiment, positioning, fear/greed | Fear/greed index, positioning data, options sentiment (VIX term structure), sector rotation, news sentiment, price data | Contrarian — pushes back when sentiment is extreme |
| **Energy Specialist** | OPEC dynamics, storage, supply chain | News search, price data, technicals, volatility, positioning data, cross-asset momentum, economic calendar | Spawned dynamically for oil/energy forecasts |
| **China Specialist** | PBoC policy, CNY intervention, trade balance | News search, news sentiment, FRED series, rate expectations, credit spreads, positioning data, economic calendar | Spawned dynamically for China-related forecasts |
| **Polling Specialist** | Election polling, prediction markets | News search, news sentiment, social sentiment, fear/greed, positioning data, sector rotation, economic calendar | Spawned dynamically for election forecasts |
| **Aggregator** | Synthesizes signals into final consensus forecast | Agent signals, debate transcript, calibration profiles, pre-computed metrics | No data tools — pure synthesis and judgment |

Each agent emits a typed `Signal` with direction, magnitude, confidence, evidence, and risks. No free text — every claim is grounded in cited data. Confidence levels are calibrated against the breadth of confirming evidence across an agent's full tool set — multiple converging data sources yield higher confidence, while mixed or conflicting signals force lower confidence.

---

## Tech Stack

**Backend**
- Python 3.10+ with OpenAI Agents SDK
- FastAPI (REST + WebSocket API)
- Pydantic v2 (structured signal protocol)
- SQLite + aiosqlite (persistence)
- structlog (structured logging)

**Frontend**
- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS v4
- Recharts (visualizations)

**Data Layer**
- MCP servers for FRED, market data, and news
- yfinance, Alpha Vantage, FRED API, NewsAPI/Tavily
- Cross-asset momentum, options sentiment, credit spreads, sector rotation, treasury curve tools

---

## Project Structure

```
isara-labs-pitch/
├── src/
│   ├── agents/          # Agent definitions (7 specialists + aggregator + triage)
│   ├── orchestrator/    # Swarm coordination, debate protocol, convergence
│   ├── signals/         # Signal schema, aggregation, calibration
│   ├── tools/           # Function tools for agents (market, economic, news, sentiment)
│   ├── mcp/             # MCP data servers (FRED, market, news, options, credit, sectors)
│   ├── persistence/     # SQLite database, agent memory
│   ├── api/             # FastAPI backend with REST + WebSocket routes
│   ├── config.py        # Environment and app configuration
│   ├── logging.py       # Structured logging setup
│   └── resilience.py    # Timeouts, token tracking, validation
│
├── frontend/
│   └── src/
│       ├── app/             # Next.js pages (dashboard, forecast detail, runs)
│       ├── components/      # UI components (10 components)
│       └── lib/             # API client, TypeScript types
│
├── scripts/
│   ├── run_forecast.py      # CLI: trigger a forecast run
│   ├── backtest.py          # Historical backtesting harness
│   └── seed_data.py         # Seed database with sample data
│
└── tests/                   # Pytest test suite
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- OpenAI API key (GPT-4.1 access)

### Setup

```bash
# Clone and install backend dependencies
cd isara-labs-pitch
pip install -e .

# Copy environment template and add your API keys
cp .env.example .env

# Initialize the database
python scripts/seed_data.py

# Install frontend dependencies
cd frontend
npm install
```

### Running

```bash
# Terminal 1: Start the backend API
uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Start the frontend
cd frontend
npm run dev
```

The dashboard will be available at `http://localhost:3000` and the API docs at `http://localhost:8000/docs`.

### CLI Usage

```bash
# Run a single forecast
python scripts/run_forecast.py --asset XAUUSD --horizon 30d

# Verbose mode (see debate exchanges)
python scripts/run_forecast.py --asset XAUUSD --horizon 30d -v

# Multi-asset correlated run
python scripts/run_forecast.py --asset XAUUSD,DXY,TLT --horizon 30d --correlated

# Backtest over historical dates
python scripts/backtest.py --asset XAUUSD --start 2025-01-01 --end 2025-10-01 --interval monthly
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | GPT-4.1 access for agents |
| `FRED_API_KEY` | No | Federal Reserve economic data |
| `ALPHA_VANTAGE_API_KEY` | No | Market data provider |
| `NEWS_API_KEY` | No | News search |
| `TAVILY_API_KEY` | No | Web search for agents |
| `DATABASE_URL` | No | SQLite path (default: `sqlite:///./data/forecasts.db`) |
| `MAX_DEBATE_ROUNDS` | No | Debate round cap (default: 2) |
| `AGENT_TIMEOUT_SECONDS` | No | Per-agent timeout (default: 60) |
| `AGENT_MODEL` | No | LLM for agents (default: gpt-4.1) |
| `FAST_MODEL` | No | LLM for summarization (default: gpt-4.1-mini) |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/forecasts` | Trigger a new forecast run |
| `GET` | `/forecasts` | List all forecasts (with filters) |
| `GET` | `/forecasts/{id}` | Get forecast with full signal chain |
| `GET` | `/forecasts/{id}/signals` | All agent signals for a run |
| `GET` | `/runs` | List all orchestration runs |
| `GET` | `/runs/{id}/debate` | Full debate transcript |
| `WS` | `/ws/forecast/{id}` | Live forecast progress stream |

---

## Signal Protocol

Every agent emits a structured `Signal` — not free text:

```python
Signal:
  agent_id: str               # Which agent produced this
  asset: str                   # What is being forecast
  direction: bullish | bearish | neutral
  magnitude: float             # Expected % move
  confidence: float            # 0.0 to 0.95 (capped)
  horizon: str                 # e.g. "7d", "30d", "90d"
  evidence: Evidence[]         # Grounded supporting data
  risks: str[]                 # What could invalidate this
  contrarian_note: str | None  # What consensus might be missing

Evidence:
  source: str                  # Data origin (e.g. "yfinance:XAUUSD", "FRED:DGS10")
  observation: str             # What the data shows
  relevance: float             # 0.0-1.0: How much this drives the signal
  timestamp: str               # ISO-8601 when observed
```

The final `Forecast` includes direction, expected move, 80% confidence interval, conviction level, consensus strength, key drivers, key risks, the strongest dissenting view, and the full debate summary.

### Evidence Tools

| Tool | Domain | What It Provides |
|------|--------|-----------------|
| `get_price_data` | Market | OHLCV price data, period returns, volume |
| `get_technical_indicators` | Market | RSI, moving averages, Bollinger bands, MACD, trend |
| `get_volatility` | Market | 5d/20d/60d/1y volatility, regime classification |
| `get_correlation_matrix` | Market | Cross-asset correlation matrix |
| `get_cross_asset_momentum` | Market | Relative performance vs peer group benchmarks |
| `get_fred_series` | Economic | FRED data series (GDP, CPI, unemployment, rates) |
| `get_rate_expectations` | Economic | Yield curve shape, rate trends |
| `get_treasury_curve` | Economic | Full curve slope, term premium, real rate proxy |
| `get_inflation_breakdown` | Economic | TIPS vs nominal spread, gold inflation signal |
| `get_credit_spreads` | Economic | HY vs IG vs Treasury spreads, risk appetite signal |
| `search_news` | News | Recent articles with sentiment and metadata |
| `get_news_sentiment` | News | Aggregated headline sentiment scoring |
| `get_fear_greed_index` | Sentiment | Composite fear/greed from VIX, S&P momentum, safe haven demand |
| `get_positioning_data` | Sentiment | ETF flow and volume positioning signals |
| `get_options_sentiment` | Sentiment | VIX term structure, vol ETF hedging activity |
| `get_sector_rotation` | Sentiment | Cyclical vs defensive sector leadership |
| `get_social_sentiment` | Sentiment | Crowd sentiment proxy |
| `get_economic_calendar` | Calendar | Upcoming high-impact economic events |

---

## Key Design Decisions

**Adversarial debate over ensemble averaging.** Agents actively challenge each other's signals. This prevents groupthink — the default failure mode of multi-agent systems.

**Intentional cognitive diversity.** Each agent has a deliberate analytical bias. The quant ignores narratives. The geopolitical analyst overweights tail risks. The sentiment agent is contrarian. This is ensemble design, not prompt variation.

**Evidence-driven confidence.** Each agent's confidence is calibrated against the breadth of its evidence. A quant signal backed by price action, volatility regime, cross-asset momentum, and correlation data carries higher confidence than one backed by technicals alone. Agents are instructed to lower confidence when their tools produce mixed or conflicting signals.

**Calibration tracking.** Confidence scores are tracked against actual outcomes. Agents that say 80% confidence should be right ~80% of the time. Miscalibrated agents get lower aggregation weight via Platt scaling.

**Graceful degradation.** If an agent times out or fails, the swarm continues with reduced coverage rather than failing entirely.

**Full transparency.** Every forecast includes the complete signal chain, debate transcript, and dissenting view. No black boxes.

---

## Supported Assets

`XAUUSD` (Gold), `CL1` (Oil), `SPX` (S&P 500), `DXY` (US Dollar Index), `BTC` (Bitcoin), `TLT` (Treasuries)

---

## License

Private — Isara Labs
