"""Tests for the persistence layer."""

import asyncio
import os
import tempfile

import pytest

from src.persistence import database as db


@pytest.fixture(autouse=True)
async def _use_temp_db(monkeypatch, tmp_path):
    """Use a temporary database for each test."""
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", test_db)
    await db.init_db()


class TestRunLifecycle:
    @pytest.mark.asyncio
    async def test_create_and_complete_run(self):
        run_id = await db.create_run("XAUUSD", "30d", 4)
        assert run_id
        assert len(run_id) == 8

        await db.complete_run(run_id, "completed", 2, 45.3)

        run = await db.get_run(run_id)
        assert run is not None
        assert run["asset"] == "XAUUSD"
        assert run["status"] == "completed"
        assert run["debate_rounds"] == 2

    @pytest.mark.asyncio
    async def test_list_runs(self):
        await db.create_run("XAUUSD", "30d", 4)
        await db.create_run("CL1", "7d", 4)
        await db.create_run("XAUUSD", "90d", 4)

        all_runs = await db.list_runs()
        assert len(all_runs) == 3

        gold_runs = await db.list_runs(asset="XAUUSD")
        assert len(gold_runs) == 2


class TestSignals:
    @pytest.mark.asyncio
    async def test_save_signal(self):
        run_id = await db.create_run("XAUUSD", "30d", 4)
        signal_id = await db.save_signal(
            run_id=run_id,
            agent_id="quant_analyst",
            direction="bullish",
            magnitude=0.05,
            confidence=0.7,
            horizon="30d",
            evidence=[{"source": "test", "observation": "test", "relevance": 0.8, "timestamp": "2026-01-01"}],
            risks=["test risk"],
            phase="initial",
        )
        assert signal_id
        assert len(signal_id) == 8


class TestCalibration:
    @pytest.mark.asyncio
    async def test_calibration_lifecycle(self):
        run_id = await db.create_run("XAUUSD", "30d", 4)

        await db.save_calibration_entry(
            run_id=run_id, agent_id="quant_analyst",
            asset="XAUUSD", predicted_direction="bullish", predicted_confidence=0.8,
        )
        await db.save_calibration_entry(
            run_id=run_id, agent_id="macro_economist",
            asset="XAUUSD", predicted_direction="bearish", predicted_confidence=0.6,
        )

        # Score against actual outcome
        await db.score_calibration(run_id, "bullish", 0.03)

        # Check quant was correct
        stats = await db.get_agent_calibration("quant_analyst")
        assert stats["total"] == 1
        assert stats["correct"] == 1
        assert stats["accuracy"] == 1.0

        # Check macro was wrong
        stats = await db.get_agent_calibration("macro_economist")
        assert stats["total"] == 1
        assert stats["correct"] == 0
        assert stats["accuracy"] == 0.0

    @pytest.mark.asyncio
    async def test_empty_calibration(self):
        stats = await db.get_agent_calibration("nonexistent_agent")
        assert stats["total"] == 0
        assert stats["accuracy"] is None


class TestDebates:
    @pytest.mark.asyncio
    async def test_save_debate(self):
        run_id = await db.create_run("XAUUSD", "30d", 4)
        debate_id = await db.save_debate(
            run_id=run_id, round_number=1,
            challenger_id="quant_analyst", target_id="macro_economist",
            argument="Your rate analysis ignores recent data",
            evidence_gap="Missing last week's FRED release",
            suggested_revision="Lower confidence from 0.8 to 0.5",
            response_type="defense",
            response_text="My thesis holds despite the new data",
        )
        assert debate_id
        assert len(debate_id) == 8


class TestForecasts:
    @pytest.mark.asyncio
    async def test_save_forecast(self):
        run_id = await db.create_run("XAUUSD", "30d", 4)
        forecast_id = await db.save_forecast(
            run_id=run_id, asset="XAUUSD", direction="bullish",
            expected_move=0.05, ci_lower=0.01, ci_upper=0.09,
            horizon="30d", conviction="high", consensus_strength=0.85,
            key_drivers=["Rate cut expectations", "Geopolitical risk"],
            key_risks=["USD strength", "Hawkish surprise"],
            dissenting_view="Quant sees bearish technicals",
            debate_summary="Macro and geo agreed bullish, quant dissented.",
        )
        assert forecast_id
        assert len(forecast_id) == 8
