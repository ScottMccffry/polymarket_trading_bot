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
from ..services.trading.risk_manager import risk_manager, RiskConfig, SETTINGS_FILE
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


# ============================================================================
# Live Trading Control Endpoints
# ============================================================================

@router.get("/trading/status")
async def get_trading_status(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Get live trading status and configuration.

    Returns whether trading is configured and enabled,
    plus current safety limits.
    """
    from ..services.polymarket.trading_client import trading_client

    return {
        "configured": trading_client.is_configured(),
        "live_enabled": trading_client.is_live_enabled(),
        "max_position_size": trading_client.max_position_size,
        "max_open_positions": trading_client.max_open_positions,
        "chain_id": trading_client.chain_id,
        "signature_type": trading_client.signature_type,
        "funder_address": trading_client.funder_address[:10] + "..." if trading_client.funder_address else None,
    }


class TradingToggleRequest(BaseModel):
    enabled: bool


@router.post("/trading/enable")
async def enable_live_trading(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Enable live trading.

    Requires trading to be configured (private key and funder address set).
    """
    from ..services.polymarket.trading_client import trading_client, _save_settings, _load_saved_settings

    if not trading_client.is_configured():
        raise HTTPException(
            status_code=400,
            detail="Trading not configured. Set private key and funder address in settings first."
        )

    # Update settings
    saved = _load_saved_settings()
    saved["live_trading_enabled"] = True
    _save_settings(saved)

    # Reload settings in client
    trading_client.reload_settings()

    return {
        "status": "enabled",
        "message": "Live trading enabled. Real orders will now be placed.",
    }


@router.post("/trading/disable")
async def disable_live_trading(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Disable live trading.

    Switches back to paper trading mode.
    """
    from ..services.polymarket.trading_client import trading_client, _save_settings, _load_saved_settings

    saved = _load_saved_settings()
    saved["live_trading_enabled"] = False
    _save_settings(saved)

    trading_client.reload_settings()

    return {
        "status": "disabled",
        "message": "Live trading disabled. Positions will be paper traded.",
    }


@router.get("/trading/open-orders")
async def get_open_orders(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get all open orders on Polymarket CLOB."""
    from ..services.polymarket.trading_client import trading_client

    if not trading_client.is_configured():
        raise HTTPException(status_code=400, detail="Trading not configured")

    orders = trading_client.get_open_orders()
    return {"orders": orders, "count": len(orders)}


@router.post("/trading/cancel-order/{order_id}")
async def cancel_order(
    order_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Cancel an open order by ID."""
    from ..services.polymarket.trading_client import trading_client

    if not trading_client.is_configured():
        raise HTTPException(status_code=400, detail="Trading not configured")

    result = trading_client.cancel_order(order_id)

    if result.success:
        return {"status": "cancelled", "order_id": order_id}
    else:
        raise HTTPException(status_code=400, detail=result.error)


@router.post("/trading/cancel-all-orders")
async def cancel_all_orders(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Cancel all open orders."""
    from ..services.polymarket.trading_client import trading_client

    if not trading_client.is_configured():
        raise HTTPException(status_code=400, detail="Trading not configured")

    result = trading_client.cancel_all_orders()

    if result.success:
        return {"status": "all_cancelled", "message": "All orders cancelled"}
    else:
        raise HTTPException(status_code=400, detail=result.error)


@router.get("/trading/balances")
async def get_trading_balances(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get wallet balances (USDC, collateral)."""
    from ..services.polymarket.trading_client import trading_client

    if not trading_client.is_configured():
        raise HTTPException(status_code=400, detail="Trading not configured")

    return trading_client.get_balances()


class TradingSettingsUpdate(BaseModel):
    private_key: str | None = None
    funder_address: str | None = None
    max_position_size: float | None = None
    max_open_positions: int | None = None


@router.put("/trading/settings")
async def update_trading_settings(
    request: TradingSettingsUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Update trading settings.

    Private key is stored securely and never returned in API responses.
    """
    from ..services.polymarket.trading_client import trading_client, _save_settings, _load_saved_settings

    saved = _load_saved_settings()

    if request.private_key:
        saved["polymarket_private_key"] = request.private_key
    if request.funder_address:
        saved["polymarket_funder_address"] = request.funder_address
    if request.max_position_size is not None:
        saved["max_position_size"] = request.max_position_size
    if request.max_open_positions is not None:
        saved["max_open_positions"] = request.max_open_positions

    _save_settings(saved)
    trading_client.reload_settings()

    return {
        "status": "updated",
        "configured": trading_client.is_configured(),
        "message": "Trading settings updated",
    }


# ============================================================================
# Risk Management Endpoints
# ============================================================================

class RiskSettingsResponse(BaseModel):
    max_position_size: float
    max_portfolio_risk_percent: float
    max_daily_loss: float
    max_drawdown_percent: float
    max_open_positions: int
    enabled: bool
    daily_pnl: float


class RiskSettingsUpdate(BaseModel):
    max_position_size: float | None = None
    max_portfolio_risk_percent: float | None = None
    max_daily_loss: float | None = None
    max_drawdown_percent: float | None = None
    max_open_positions: int | None = None
    enabled: bool | None = None


@router.get("/risk", response_model=RiskSettingsResponse)
async def get_risk_settings():
    """Get current risk management settings."""
    config = risk_manager.config
    return RiskSettingsResponse(
        max_position_size=config.max_position_size,
        max_portfolio_risk_percent=config.max_portfolio_risk_percent,
        max_daily_loss=config.max_daily_loss,
        max_drawdown_percent=config.max_drawdown_percent,
        max_open_positions=config.max_open_positions,
        enabled=config.enabled,
        daily_pnl=risk_manager.get_daily_pnl(),
    )


@router.put("/risk", response_model=RiskSettingsResponse)
async def update_risk_settings(update: RiskSettingsUpdate):
    """Update risk management settings."""
    config = risk_manager.config

    if update.max_position_size is not None:
        config.max_position_size = update.max_position_size
    if update.max_portfolio_risk_percent is not None:
        config.max_portfolio_risk_percent = update.max_portfolio_risk_percent
    if update.max_daily_loss is not None:
        config.max_daily_loss = update.max_daily_loss
    if update.max_drawdown_percent is not None:
        config.max_drawdown_percent = update.max_drawdown_percent
    if update.max_open_positions is not None:
        config.max_open_positions = update.max_open_positions
    if update.enabled is not None:
        config.enabled = update.enabled

    # Save to file
    config.save_to_settings_file(SETTINGS_FILE)

    return await get_risk_settings()
