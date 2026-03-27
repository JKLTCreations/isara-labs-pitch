"""SQLite persistence layer for forecast runs, signals, debates, and calibration.

Uses aiosqlite for async access. All writes go through this module.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import aiosqlite

from src.config import DATA_DIR

DB_PATH = DATA_DIR / "forecasts.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS forecast_runs (
    id TEXT PRIMARY KEY,
    asset TEXT NOT NULL,
    horizon TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    agent_count INTEGER NOT NULL DEFAULT 0,
    debate_rounds INTEGER NOT NULL DEFAULT 0,
    elapsed_seconds REAL,
    created_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS signals (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES forecast_runs(id),
    agent_id TEXT NOT NULL,
    phase TEXT NOT NULL DEFAULT 'initial',
    direction TEXT NOT NULL,
    magnitude REAL NOT NULL,
    confidence REAL NOT NULL,
    horizon TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    risks_json TEXT NOT NULL,
    contrarian_note TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS debates (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES forecast_runs(id),
    round_number INTEGER NOT NULL,
    challenger_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    argument TEXT NOT NULL,
    evidence_gap TEXT NOT NULL,
    suggested_revision TEXT NOT NULL,
    response_type TEXT,
    response_text TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS forecasts (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL UNIQUE REFERENCES forecast_runs(id),
    asset TEXT NOT NULL,
    direction TEXT NOT NULL,
    expected_move REAL NOT NULL,
    ci_lower REAL NOT NULL,
    ci_upper REAL NOT NULL,
    horizon TEXT NOT NULL,
    conviction TEXT NOT NULL,
    consensus_strength REAL NOT NULL,
    key_drivers_json TEXT NOT NULL,
    key_risks_json TEXT NOT NULL,
    dissenting_view TEXT,
    debate_summary TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS calibration_log (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES forecast_runs(id),
    agent_id TEXT NOT NULL,
    asset TEXT NOT NULL,
    predicted_direction TEXT NOT NULL,
    predicted_confidence REAL NOT NULL,
    actual_direction TEXT,
    actual_move REAL,
    correct INTEGER,
    scored_at TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_signals_run ON signals(run_id);
CREATE INDEX IF NOT EXISTS idx_debates_run ON debates(run_id);
CREATE INDEX IF NOT EXISTS idx_calibration_agent ON calibration_log(agent_id);
CREATE INDEX IF NOT EXISTS idx_runs_asset ON forecast_runs(asset);
"""


async def init_db() -> None:
    """Initialize the database and create tables."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(str(DB_PATH)) as db:
        await db.executescript(SCHEMA)
        await db.commit()


def init_db_sync() -> None:
    """Synchronous version for scripts."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def _new_id() -> str:
    return str(uuid.uuid4())[:8]


async def create_run(asset: str, horizon: str, agent_count: int) -> str:
    """Create a new forecast run record. Returns run ID."""
    run_id = _new_id()
    async with aiosqlite.connect(str(DB_PATH)) as db:
        await db.execute(
            "INSERT INTO forecast_runs (id, asset, horizon, agent_count, created_at) VALUES (?, ?, ?, ?, ?)",
            (run_id, asset, horizon, agent_count, datetime.now().isoformat()),
        )
        await db.commit()
    return run_id


async def complete_run(run_id: str, status: str, debate_rounds: int, elapsed: float) -> None:
    """Mark a run as completed."""
    async with aiosqlite.connect(str(DB_PATH)) as db:
        await db.execute(
            "UPDATE forecast_runs SET status=?, debate_rounds=?, elapsed_seconds=?, completed_at=? WHERE id=?",
            (status, debate_rounds, elapsed, datetime.now().isoformat(), run_id),
        )
        await db.commit()


async def save_signal(
    run_id: str,
    agent_id: str,
    direction: str,
    magnitude: float,
    confidence: float,
    horizon: str,
    evidence: list[dict],
    risks: list[str],
    contrarian_note: str | None = None,
    phase: str = "initial",
) -> str:
    """Save an agent signal. Returns signal ID."""
    signal_id = _new_id()
    async with aiosqlite.connect(str(DB_PATH)) as db:
        await db.execute(
            """INSERT INTO signals
            (id, run_id, agent_id, phase, direction, magnitude, confidence, horizon,
             evidence_json, risks_json, contrarian_note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (signal_id, run_id, agent_id, phase, direction, magnitude, confidence, horizon,
             json.dumps(evidence), json.dumps(risks), contrarian_note, datetime.now().isoformat()),
        )
        await db.commit()
    return signal_id


async def save_debate(
    run_id: str,
    round_number: int,
    challenger_id: str,
    target_id: str,
    argument: str,
    evidence_gap: str,
    suggested_revision: str,
    response_type: str | None = None,
    response_text: str | None = None,
) -> str:
    """Save a debate challenge/response. Returns debate ID."""
    debate_id = _new_id()
    async with aiosqlite.connect(str(DB_PATH)) as db:
        await db.execute(
            """INSERT INTO debates
            (id, run_id, round_number, challenger_id, target_id, argument,
             evidence_gap, suggested_revision, response_type, response_text, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (debate_id, run_id, round_number, challenger_id, target_id, argument,
             evidence_gap, suggested_revision, response_type, response_text,
             datetime.now().isoformat()),
        )
        await db.commit()
    return debate_id


async def save_forecast(
    run_id: str,
    asset: str,
    direction: str,
    expected_move: float,
    ci_lower: float,
    ci_upper: float,
    horizon: str,
    conviction: str,
    consensus_strength: float,
    key_drivers: list[str],
    key_risks: list[str],
    dissenting_view: str | None,
    debate_summary: str,
) -> str:
    """Save the aggregated forecast. Returns forecast ID."""
    forecast_id = _new_id()
    async with aiosqlite.connect(str(DB_PATH)) as db:
        await db.execute(
            """INSERT INTO forecasts
            (id, run_id, asset, direction, expected_move, ci_lower, ci_upper, horizon,
             conviction, consensus_strength, key_drivers_json, key_risks_json,
             dissenting_view, debate_summary, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (forecast_id, run_id, asset, direction, expected_move, ci_lower, ci_upper, horizon,
             conviction, consensus_strength, json.dumps(key_drivers), json.dumps(key_risks),
             dissenting_view, debate_summary, datetime.now().isoformat()),
        )
        await db.commit()
    return forecast_id


async def save_calibration_entry(
    run_id: str,
    agent_id: str,
    asset: str,
    predicted_direction: str,
    predicted_confidence: float,
) -> str:
    """Log a prediction for future calibration scoring. Returns entry ID."""
    entry_id = _new_id()
    async with aiosqlite.connect(str(DB_PATH)) as db:
        await db.execute(
            """INSERT INTO calibration_log
            (id, run_id, agent_id, asset, predicted_direction, predicted_confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (entry_id, run_id, agent_id, asset, predicted_direction, predicted_confidence,
             datetime.now().isoformat()),
        )
        await db.commit()
    return entry_id


async def score_calibration(
    run_id: str,
    actual_direction: str,
    actual_move: float,
) -> None:
    """Score all calibration entries for a run against actual outcome."""
    async with aiosqlite.connect(str(DB_PATH)) as db:
        rows = await db.execute_fetchall(
            "SELECT id, predicted_direction FROM calibration_log WHERE run_id=?", (run_id,)
        )
        for row_id, predicted in rows:
            correct = 1 if predicted == actual_direction else 0
            await db.execute(
                "UPDATE calibration_log SET actual_direction=?, actual_move=?, correct=?, scored_at=? WHERE id=?",
                (actual_direction, actual_move, correct, datetime.now().isoformat(), row_id),
            )
        await db.commit()


async def get_agent_calibration(agent_id: str, asset: str | None = None) -> dict:
    """Get calibration stats for an agent."""
    async with aiosqlite.connect(str(DB_PATH)) as db:
        if asset:
            rows = await db.execute_fetchall(
                "SELECT predicted_confidence, correct FROM calibration_log WHERE agent_id=? AND asset=? AND correct IS NOT NULL",
                (agent_id, asset),
            )
        else:
            rows = await db.execute_fetchall(
                "SELECT predicted_confidence, correct FROM calibration_log WHERE agent_id=? AND correct IS NOT NULL",
                (agent_id,),
            )

    if not rows:
        return {"agent_id": agent_id, "total": 0, "accuracy": None, "calibration": None}

    total = len(rows)
    correct = sum(1 for _, c in rows if c == 1)
    accuracy = correct / total

    # Calibration by confidence bucket
    buckets: dict[str, list[int]] = {}
    for conf, c in rows:
        bucket = f"{int(conf * 10) * 10}-{int(conf * 10) * 10 + 10}%"
        buckets.setdefault(bucket, []).append(c)

    calibration = {}
    for bucket, outcomes in buckets.items():
        calibration[bucket] = {
            "count": len(outcomes),
            "actual_accuracy": round(sum(outcomes) / len(outcomes), 3),
        }

    return {
        "agent_id": agent_id,
        "asset": asset,
        "total": total,
        "correct": correct,
        "accuracy": round(accuracy, 3),
        "calibration_by_bucket": calibration,
    }


async def get_run(run_id: str) -> dict | None:
    """Fetch a single run with its forecast."""
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        row = await db.execute_fetchall(
            "SELECT * FROM forecast_runs WHERE id=?", (run_id,)
        )
        if not row:
            return None
        return dict(row[0])


async def list_runs(asset: str | None = None, limit: int = 50) -> list[dict]:
    """List forecast runs, optionally filtered by asset."""
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row
        if asset:
            rows = await db.execute_fetchall(
                "SELECT * FROM forecast_runs WHERE asset=? ORDER BY created_at DESC LIMIT ?",
                (asset, limit),
            )
        else:
            rows = await db.execute_fetchall(
                "SELECT * FROM forecast_runs ORDER BY created_at DESC LIMIT ?", (limit,)
            )
        return [dict(r) for r in rows]
