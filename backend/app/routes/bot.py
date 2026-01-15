"""
Bot Control API Routes

Endpoints to start, stop, and monitor the trading bot.
"""

import asyncio
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ..auth.security import get_current_user
from ..models.user import User
from ..services.bot import bot_orchestrator, signal_trader
from ..services.trading import signal_generator
from ..database import get_db_context

router = APIRouter(
    prefix="/api/bot",
    tags=["bot"],
    dependencies=[Depends(get_current_user)],
)


class BotActionResponse(BaseModel):
    status: str
    message: str
    tasks: list[str] | None = None


class TaskToggleRequest(BaseModel):
    enabled: bool


@router.post("/start", response_model=BotActionResponse)
async def start_bot(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Start the trading bot.

    Starts all enabled tasks in the bot orchestrator.
    """
    result = await bot_orchestrator.start()
    return BotActionResponse(**result)


@router.post("/stop", response_model=BotActionResponse)
async def stop_bot(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Stop the trading bot.

    Gracefully stops all running tasks.
    """
    result = await bot_orchestrator.stop()
    return BotActionResponse(**result)


@router.get("/status")
async def get_bot_status(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get current bot status.

    Returns the bot state, uptime, and status of all registered tasks.
    """
    return bot_orchestrator.get_status()


@router.post("/tasks/{task_name}/enable")
async def enable_task(
    task_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Enable a specific bot task."""
    bot_orchestrator.enable_task(task_name)
    return {"message": f"Task '{task_name}' enabled"}


@router.post("/tasks/{task_name}/disable")
async def disable_task(
    task_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Disable a specific bot task."""
    bot_orchestrator.disable_task(task_name)
    return {"message": f"Task '{task_name}' disabled"}


@router.get("/tasks")
async def list_tasks(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List all registered bot tasks and their status."""
    status = bot_orchestrator.get_status()
    return {"tasks": status["tasks"]}


# ============================================================================
# Signal Trader Endpoints
# ============================================================================

class TestSignalRequest(BaseModel):
    message: str
    source: str = "test"


class TestSignalResponse(BaseModel):
    message: str
    markets_found: int
    signals_generated: int
    signals: list[dict]


@router.post("/signal-trader/test", response_model=TestSignalResponse)
async def test_signal_generation(
    request: TestSignalRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Test signal generation without opening positions.

    Useful for testing the Qdrant search and LLM analysis pipeline.
    """
    from ..services.qdrant.client import QdrantService
    from ..services.llm.analysis import market_analyzer

    qdrant = QdrantService()

    # Search for markets
    markets = qdrant.search(query=request.message, limit=10, score_threshold=0.3)

    signals = []
    for market in markets:
        # Analyze each market
        analysis = await market_analyzer.analyze(
            message=request.message,
            question=market.get("question", ""),
            description=market.get("description"),
            end_date=market.get("end_date_iso"),
        )

        if analysis.is_actionable(min_confidence=0.7):
            signals.append({
                "market_question": market.get("question"),
                "market_id": market.get("condition_id"),
                "similarity_score": market.get("similarity_score"),
                "direction": analysis.direction,
                "confidence": analysis.confidence,
                "relevance_score": analysis.relevance_score,
                "reasoning": analysis.reasoning,
                "message_type": analysis.message_type,
            })

    return TestSignalResponse(
        message=request.message[:200],
        markets_found=len(markets),
        signals_generated=len(signals),
        signals=signals,
    )


@router.get("/signal-trader/stats")
async def get_signal_trader_stats(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get signal trader statistics."""
    return signal_trader.get_stats()


# Background task for continuous monitoring
_monitoring_task: Optional[asyncio.Task] = None


@router.post("/signal-trader/start-monitoring")
async def start_signal_monitoring(
    background_tasks: BackgroundTasks,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Start continuous Telegram monitoring in the background.

    This will process messages as they arrive and generate signals/positions.
    """
    global _monitoring_task

    if _monitoring_task and not _monitoring_task.done():
        return {"status": "already_running", "message": "Signal monitoring is already running"}

    async def run_monitoring():
        try:
            await signal_trader.run()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Signal monitoring error: {e}")

    _monitoring_task = asyncio.create_task(run_monitoring())

    return {
        "status": "started",
        "message": "Signal monitoring started in background",
    }


@router.post("/signal-trader/stop-monitoring")
async def stop_signal_monitoring(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Stop continuous Telegram monitoring."""
    global _monitoring_task

    if not _monitoring_task or _monitoring_task.done():
        return {"status": "not_running", "message": "Signal monitoring is not running"}

    await signal_trader.stop()
    _monitoring_task.cancel()

    return {"status": "stopped", "message": "Signal monitoring stopped"}
