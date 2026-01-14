"""Telegram authentication and management routes."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..services.telegram import telegram_auth, TelegramService
from ..config import get_settings
from ..auth.security import get_current_user

router = APIRouter(
    prefix="/api/telegram",
    tags=["telegram"],
    dependencies=[Depends(get_current_user)]
)


class VerifyCodeRequest(BaseModel):
    code: str
    password: str | None = None


@router.get("/status")
async def get_status():
    """Get current Telegram auth status."""
    return telegram_auth.status()


@router.post("/connect")
async def connect():
    """Start Telegram authentication (sends verification code)."""
    result = await telegram_auth.connect()
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Connection failed"))
    return result


@router.post("/verify")
async def verify_code(request: VerifyCodeRequest):
    """Submit verification code (and optional 2FA password)."""
    result = await telegram_auth.verify_code(request.code, request.password)
    if not result["success"]:
        raise HTTPException(
            status_code=400 if not result.get("needs_2fa") else 401,
            detail=result.get("error", "Verification failed")
        )
    return result


@router.post("/disconnect")
async def disconnect():
    """Disconnect and log out from Telegram."""
    result = await telegram_auth.disconnect()
    return result


@router.get("/groups")
async def get_groups():
    """Get list of monitored groups from config."""
    settings = get_settings()
    groups = []
    if settings.telegram_monitored_groups:
        groups = [g.strip() for g in settings.telegram_monitored_groups.split(",") if g.strip()]
    return {"groups": groups}


@router.get("/messages/{group}")
async def get_messages(group: str, limit: int = 10):
    """Get recent messages from a group (requires authentication)."""
    status = telegram_auth.status()
    if not status["authenticated"]:
        raise HTTPException(status_code=401, detail="Telegram not authenticated")

    settings = get_settings()
    service = TelegramService(settings)

    try:
        await service.start()
        messages = await service.get_recent_messages(group, limit=limit)
        return {
            "group": group,
            "messages": [
                {
                    "message_id": m.message_id,
                    "chat_title": m.chat_title,
                    "text": m.text,
                    "timestamp": m.timestamp.isoformat(),
                }
                for m in messages
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await service.disconnect()
