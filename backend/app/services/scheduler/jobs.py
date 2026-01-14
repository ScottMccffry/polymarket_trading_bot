"""Background job scheduler for periodic tasks."""
import asyncio
import logging
from datetime import datetime, UTC

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, JobExecutionEvent
from sqlalchemy import select

from ...config import Settings, get_settings
from ...database import async_session
from ...models.position import Position
from ..polymarket import MarketHarvester
from ..trading import StrategyExecutor
from ...websocket import manager as ws_manager, EventType, WebSocketEvent

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler | None = None


async def harvest_markets_job():
    """Background job to harvest markets from Polymarket."""
    settings = get_settings()
    harvester = MarketHarvester(settings)

    logger.info("[SCHEDULER] Starting market harvest job...")
    start_time = datetime.now(UTC)

    try:
        async with async_session() as db:
            count = await harvester.harvest(
                db,
                max_markets=settings.market_harvest_max_markets
            )

        elapsed = (datetime.now(UTC) - start_time).total_seconds()
        logger.info(
            f"[SCHEDULER] Market harvest completed: {count} markets in {elapsed:.2f}s"
        )
        return count

    except Exception as e:
        logger.error(f"[SCHEDULER] Market harvest failed: {e}")
        raise


def job_listener(event: JobExecutionEvent):
    """Listen for job execution events."""
    if event.exception:
        logger.error(
            f"[SCHEDULER] Job {event.job_id} failed with exception: {event.exception}"
        )
    else:
        logger.info(
            f"[SCHEDULER] Job {event.job_id} executed successfully"
        )


def start_scheduler(settings: Settings | None = None) -> AsyncIOScheduler:
    """Start the background scheduler with configured jobs."""
    global scheduler

    if settings is None:
        settings = get_settings()

    if not settings.scheduler_enabled:
        logger.info("[SCHEDULER] Scheduler is disabled via settings")
        return None

    if scheduler is not None and scheduler.running:
        logger.warning("[SCHEDULER] Scheduler already running")
        return scheduler

    scheduler = AsyncIOScheduler()

    # Add job listener for logging
    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    # Schedule market harvest job
    scheduler.add_job(
        harvest_markets_job,
        trigger=IntervalTrigger(hours=settings.market_harvest_interval_hours),
        id="harvest_markets",
        name="Harvest markets from Polymarket",
        replace_existing=True,
        max_instances=1,  # Prevent overlapping runs
    )

    # Schedule position check job (every minute)
    scheduler.add_job(
        check_positions_job,
        trigger=IntervalTrigger(minutes=1),
        id="check_positions",
        name="Check positions for exit signals",
        replace_existing=True,
        max_instances=1,
    )

    scheduler.start()
    logger.info(
        f"[SCHEDULER] Started with market harvest every "
        f"{settings.market_harvest_interval_hours} hours, "
        f"position checks every 1 minute"
    )

    return scheduler


def stop_scheduler():
    """Stop the background scheduler."""
    global scheduler

    if scheduler is not None and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[SCHEDULER] Scheduler stopped")
        scheduler = None


async def run_harvest_now() -> int:
    """Manually trigger a market harvest (useful for testing or manual runs)."""
    return await harvest_markets_job()


async def check_positions_job():
    """Background job to check open positions for exit signals."""
    executor = StrategyExecutor()

    logger.info("[SCHEDULER] Starting position check job...")
    start_time = datetime.now(UTC)

    try:
        async with async_session() as db:
            exits = await executor.check_position_exits(db)

            # Fetch updated open positions for broadcast
            result = await db.execute(
                select(Position).where(Position.status == "open")
            )
            open_positions = list(result.scalars().all())

        elapsed = (datetime.now(UTC) - start_time).total_seconds()
        logger.info(
            f"[SCHEDULER] Position check completed: {len(exits)} exits in {elapsed:.2f}s"
        )

        # Broadcast updates via WebSocket
        await _broadcast_position_updates(open_positions, exits)

        return exits

    except Exception as e:
        logger.error(f"[SCHEDULER] Position check failed: {e}")
        raise


async def _broadcast_position_updates(positions: list[Position], exits: list[dict]):
    """Broadcast position updates to all WebSocket clients."""
    if ws_manager.connection_count == 0:
        return  # No clients connected

    try:
        # Broadcast individual exits
        for exit_info in exits:
            if exit_info.get("action") == "close":
                event = WebSocketEvent.create(
                    EventType.POSITION_CLOSED,
                    {
                        "position_id": exit_info["position_id"],
                        "exit_price": exit_info["exit_price"],
                        "realized_pnl": exit_info["pnl"],
                        "realized_pnl_percent": exit_info.get("pnl_percent", 0),
                        "reason": exit_info["reason"],
                    }
                )
                await ws_manager.broadcast(event.model_dump())

        # Broadcast batch position update
        positions_data = [
            {
                "position_id": p.id,
                "current_price": p.current_price,
                "unrealized_pnl": p.unrealized_pnl or 0,
                "unrealized_pnl_percent": p.unrealized_pnl_percent or 0,
            }
            for p in positions
            if p.current_price is not None
        ]

        if positions_data:
            event = WebSocketEvent.create(
                EventType.POSITIONS_BATCH,
                {"positions": positions_data}
            )
            await ws_manager.broadcast(event.model_dump())

        # Broadcast portfolio summary
        total_unrealized = sum(p.unrealized_pnl or 0 for p in positions)
        portfolio_event = WebSocketEvent.create(
            EventType.PORTFOLIO_UPDATE,
            {
                "unrealized_pnl": total_unrealized,
                "open_positions_count": len(positions),
            }
        )
        await ws_manager.broadcast(portfolio_event.model_dump())

        logger.debug(
            f"[WebSocket] Broadcast: {len(positions_data)} positions, "
            f"{len(exits)} exits, portfolio update"
        )

    except Exception as e:
        logger.error(f"[WebSocket] Broadcast failed: {e}")


async def run_position_check_now() -> list[dict]:
    """Manually trigger a position check."""
    return await check_positions_job()


def get_scheduler_status() -> dict:
    """Get current scheduler status and job info."""
    global scheduler

    if scheduler is None or not scheduler.running:
        return {
            "running": False,
            "jobs": [],
        }

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
        })

    return {
        "running": True,
        "jobs": jobs,
    }
