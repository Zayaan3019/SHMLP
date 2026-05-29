from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SHMLRP_",
        env_file=".env",
        extra="ignore",
    )

    artifacts_dir: Path = Field(default=Path("artifacts"))
    random_seed: int = 42
    sample_size: int = 2000
    drift_probability: float = 0.3

    drift_threshold: float = 0.2
    performance_drop_threshold: float = 0.03
    canary_min_improvement: float = 0.01
    max_missing_rate: float = 0.05

    api_host: str = "127.0.0.1"
    api_port: int = 8000
    log_level: str = "INFO"


def load_config() -> AppConfig:
    return AppConfig()
