"""Configuration management using Pydantic Settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/polymarket.db"

    # Telegram
    telegram_api_id: int = 0
    telegram_api_hash: str = ""
    telegram_phone: str = ""
    telegram_groups: list[str] = []
    telegram_check_interval: int = 180

    # Polymarket
    polymarket_gamma_url: str = "https://gamma-api.polymarket.com"
    polymarket_clob_url: str = "https://clob.polymarket.com"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # Qdrant (optional)
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_collection: str = "polymarket_markets"

    # Trading Parameters
    initial_capital: float = 10000.0
    position_size_percent: float = 0.01
    min_confidence: float = 0.75
    max_spread_percent: float = 15.0
    min_entry_price: float = 0.03
    max_entry_price: float = 0.80
    min_days_until_end: int = 7

    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = "change-this-to-a-random-string"

    # Logging
    log_level: str = "INFO"

    @property
    def telegram_configured(self) -> bool:
        """Check if Telegram is properly configured."""
        return bool(
            self.telegram_api_id
            and self.telegram_api_hash
            and self.telegram_phone
        )

    @property
    def qdrant_configured(self) -> bool:
        """Check if Qdrant is properly configured."""
        return bool(self.qdrant_url and self.qdrant_api_key)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
