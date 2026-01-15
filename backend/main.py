import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db, async_session
from app.models.user import User
from app.auth.security import get_password_hash
from sqlalchemy import select
from app.routes import auth_router, signals_router, strategies_router, positions_router, markets_router, telegram_router, settings_router, bot_router, sources_router
from app.services.scheduler import start_scheduler, stop_scheduler
from app.websocket import websocket_router
from app.services.scheduler.jobs import get_scheduler_status, run_harvest_now
from app.services.bot import bot_orchestrator
from app.services.bot.orchestrator import register_default_tasks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    logger.info("Database initialized")

    # Start background scheduler
    start_scheduler(settings)

    # Register default bot tasks
    register_default_tasks()
    logger.info("Bot tasks registered")

    yield

    # Shutdown
    # Stop the trading bot if running
    if bot_orchestrator.is_running:
        await bot_orchestrator.stop()
        logger.info("Trading bot stopped")

    stop_scheduler()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

# CORS middleware - origins configurable via CORS_ORIGINS env var
# Use "*" to allow all origins (not recommended for production)
cors_origins_raw = settings.cors_origins.strip()
if cors_origins_raw == "*":
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True if cors_origins != ["*"] else False,  # credentials not allowed with wildcard
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(signals_router)
app.include_router(strategies_router)
app.include_router(positions_router)
app.include_router(markets_router)
app.include_router(telegram_router)
app.include_router(settings_router)
app.include_router(bot_router)
app.include_router(sources_router)
app.include_router(websocket_router)


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/scheduler/status")
async def scheduler_status():
    """Get background scheduler status and job information."""
    return get_scheduler_status()


@app.post("/scheduler/harvest")
async def trigger_harvest():
    """Manually trigger a market harvest job."""
    try:
        count = await run_harvest_now()
        return {"status": "success", "markets_harvested": count}
    except Exception as e:
        return {"status": "error", "message": str(e)}
