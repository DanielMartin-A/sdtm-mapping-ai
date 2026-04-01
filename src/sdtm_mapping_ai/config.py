"""Central configuration for the SDTM Mapping AI pipeline.

Fixes applied:
- C2: @lru_cache on get_settings() — avoids redundant .env reads
- H3: Exhaustive match with ValueError on unknown provider
- M2: threshold=0.0 falsy-value bug guarded via `is not None` downstream
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(StrEnum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    project_root: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parent.parent.parent
    )

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"

    @property
    def pilot01_dir(self) -> Path:
        return self.data_dir / "pilot01"

    @property
    def standards_dir(self) -> Path:
        return self.data_dir / "sdtm_standards"

    @property
    def results_dir(self) -> Path:
        return self.project_root / "results"

    # LLM
    sdtm_llm_provider: LLMProvider = LLMProvider.ANTHROPIC
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-20250514"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"

    # Vector store
    chroma_persist_dir: str = "data/chroma_db"
    chroma_collection: str = "sdtm_knowledge"

    # Pipeline
    confidence_threshold: float = 0.70
    max_concurrent_calls: int = 5

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    def get_llm_model_name(self) -> str:
        """Return the model name for the configured provider.

        FIX H3: exhaustive match — raises on unknown provider.
        """
        match self.sdtm_llm_provider:
            case LLMProvider.OPENAI:
                return self.openai_model
            case LLMProvider.ANTHROPIC:
                return self.anthropic_model
            case LLMProvider.OLLAMA:
                return self.ollama_model
            case _:
                raise ValueError(f"Unsupported LLM provider: {self.sdtm_llm_provider}")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """FIX C2: Cached singleton — avoids redundant .env disk reads."""
    return Settings()
