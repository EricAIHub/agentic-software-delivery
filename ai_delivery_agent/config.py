from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment or .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    agent_runs_dir: str = ".agent_runs"
    max_file_bytes: int = 20_000
    max_context_chars: int = 30_000

    @property
    def runs_dir_path(self) -> Path:
        return Path(self.agent_runs_dir).expanduser().resolve()


def get_settings() -> Settings:
    return Settings()
