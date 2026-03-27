"""FastAPI application — Swarm Forecaster API.

Run with:
    uvicorn src.api.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import forecasts, runs, signals, ws
from src.persistence import database as db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize the database on startup."""
    await db.init_db()
    yield


app = FastAPI(
    title="Swarm Forecaster API",
    description=(
        "Multi-agent adversarial forecasting engine. "
        "Trigger forecast runs, inspect agent signals, replay debates, "
        "and stream live progress via WebSocket."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(forecasts.router)
app.include_router(signals.router)
app.include_router(runs.router)
app.include_router(ws.router)


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "swarm-forecaster"}
