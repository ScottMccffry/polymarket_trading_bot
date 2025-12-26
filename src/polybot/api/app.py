"""FastAPI application factory."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import structlog

from ..db.session import init_db, close_db
from ..config import get_settings
from .routes import dashboard, positions, signals, strategies, bot

logger = structlog.get_logger()

# Templates
templates_path = Path(__file__).parent.parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("api_starting")
    await init_db()
    yield
    await close_db()
    logger.info("api_stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Polymarket Trading Bot",
        description="Paper trading bot for Polymarket prediction markets",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Include routers
    app.include_router(dashboard.router, prefix="/ui", tags=["UI"])
    app.include_router(positions.router, prefix="/api/positions", tags=["Positions"])
    app.include_router(signals.router, prefix="/api/signals", tags=["Signals"])
    app.include_router(strategies.router, prefix="/api/strategies", tags=["Strategies"])
    app.include_router(bot.router, prefix="/api/bot", tags=["Bot"])

    # Health check
    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app


# Default app instance
app = create_app()
