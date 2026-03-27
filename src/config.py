"""Application configuration loaded from environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    openai_api_key: str = field(repr=False, default="")
    alpha_vantage_api_key: str = field(repr=False, default="")
    fred_api_key: str = field(repr=False, default="")
    news_api_key: str = field(repr=False, default="")
    tavily_api_key: str = field(repr=False, default="")

    database_url: str = "sqlite:///./data/forecasts.db"
    log_level: str = "INFO"
    max_debate_rounds: int = 2
    agent_timeout_seconds: int = 60

    # Models
    agent_model: str = "gpt-4.1"
    fast_model: str = "gpt-4.1-mini"

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
            alpha_vantage_api_key=os.environ.get("ALPHA_VANTAGE_API_KEY", ""),
            fred_api_key=os.environ.get("FRED_API_KEY", ""),
            news_api_key=os.environ.get("NEWS_API_KEY", ""),
            tavily_api_key=os.environ.get("TAVILY_API_KEY", ""),
            database_url=os.environ.get("DATABASE_URL", "sqlite:///./data/forecasts.db"),
            log_level=os.environ.get("LOG_LEVEL", "INFO"),
            max_debate_rounds=int(os.environ.get("MAX_DEBATE_ROUNDS", "2")),
            agent_timeout_seconds=int(os.environ.get("AGENT_TIMEOUT_SECONDS", "60")),
            agent_model=os.environ.get("AGENT_MODEL", "gpt-4.1"),
            fast_model=os.environ.get("FAST_MODEL", "gpt-4.1-mini"),
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required")
        return errors


# Singleton
_config: Config | None = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
