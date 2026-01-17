from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Doudinski Investment Fund API"
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str = "sqlite+aiosqlite:///./app.db"

    # Admin credentials
    default_admin_email: str = ""
    default_admin_password: str = ""

    # CORS - comma-separated list of allowed origins
    cors_origins: str = "http://localhost:3000,http://localhost:3001"

    # Polymarket API
    polymarket_clob_url: str = "https://clob.polymarket.com"
    polymarket_gamma_url: str = "https://gamma-api.polymarket.com"
    min_days_until_end: int = 7  # Minimum days before market ends

    # Polymarket Trading (Real Orders)
    polymarket_private_key: str = ""  # Wallet private key
    polymarket_funder_address: str = ""  # Wallet address (0x...)
    polymarket_chain_id: int = 137  # Polygon mainnet
    polymarket_signature_type: int = 0  # 0 = EOA (anonymous), 1 = Magic wallet
    live_trading_enabled: bool = False  # Safety: must explicitly enable
    max_position_size: float = 100.0  # Max USD per position
    max_open_positions: int = 10  # Max concurrent positions

    # Scheduler settings
    market_harvest_interval_hours: int = 12  # Harvest markets every N hours
    market_harvest_max_markets: int = 5000  # Max markets to fetch per harvest
    scheduler_enabled: bool = True  # Enable/disable background scheduler

    # Telegram settings
    telegram_api_id: int = 0
    telegram_api_hash: str = ""
    telegram_phone: str = ""
    telegram_session_path: str = "data/telegram"
    telegram_monitored_groups: str = ""  # Comma-separated group usernames
    telegram_check_interval: int = 180  # Seconds between checks

    # Qdrant settings
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_collection_name: str = "polymarket_markets"

    # OpenAI settings
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
