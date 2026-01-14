"""
Bot Control API Routes

Endpoints to start, stop, and monitor the trading bot.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth.security import get_current_user
from ..models.user import User
from ..services.bot import bot_orchestrator

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
