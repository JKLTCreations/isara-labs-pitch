"""FastAPI application — Swarm Forecaster API.

Includes structured logging, error handling middleware, and request tracing.

Run with:
    uvicorn src.api.main:app --reload
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import forecasts, runs, signals, ws
from src.logging import get_logger, setup_logging
from src.persistence import database as db

log = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize logging and database on startup."""
    setup_logging()
    await db.init_db()
    log.info("app_started", service="swarm-forecaster")
    yield
    log.info("app_shutdown", service="swarm-forecaster")


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


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log every request with timing."""
    start = time.monotonic()
    try:
        response = await call_next(request)
        elapsed = round(time.monotonic() - start, 3)
        log.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            elapsed_seconds=elapsed,
        )
        return response
    except Exception as e:
        elapsed = round(time.monotonic() - start, 3)
        log.error(
            "http_request_error",
            method=request.method,
            path=request.url.path,
            error=str(e),
            error_type=type(e).__name__,
            elapsed_seconds=elapsed,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
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
