"""Settings API routes."""
import json
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..config import get_settings
from ..auth.security import get_current_user

router = APIRouter(
    prefix="/api/settings",
    tags=["settings"],
    dependencies=[Depends(get_current_user)]
)

# Settings file path
SETTINGS_FILE = Path("data/settings.json")


def _ensure_data_dir():
    """Ensure data directory exists."""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_saved_settings() -> dict:
    """Load settings from JSON file."""
    _ensure_data_dir()
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_settings(settings: dict):
    """Save settings to JSON file."""
    _ensure_data_dir()
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)


def _mask_value(value: str, show_chars: int = 4) -> str:
    """Mask a sensitive value, showing only last N characters."""
    if not value or len(value) <= show_chars:
        return "*" * len(value) if value else ""
    return "*" * (len(value) - show_chars) + value[-show_chars:]


# Response models
class TelegramSettingsResponse(BaseModel):
    api_id: int
    api_hash_masked: str
    phone: str
    monitored_groups: str


class TelegramSettingsUpdate(BaseModel):
    api_id: int | None = None
    api_hash: str | None = None
    phone: str | None = None
    monitored_groups: str | None = None


class LLMSettingsResponse(BaseModel):
    openai_api_key_masked: str
    model: str


class LLMSettingsUpdate(BaseModel):
    openai_api_key: str | None = None
    model: str | None = None


class QdrantSettingsResponse(BaseModel):
    url: str
    api_key_masked: str
    collection_name: str


class QdrantSettingsUpdate(BaseModel):
    url: str | None = None
    api_key: str | None = None
    collection_name: str | None = None


class AllSettingsResponse(BaseModel):
    telegram: TelegramSettingsResponse
    llm: LLMSettingsResponse
    qdrant: QdrantSettingsResponse


def _get_effective_setting(key: str, saved: dict) -> str:
    """Get effective setting value, preferring saved over env."""
    env_settings = get_settings()
    # Check saved settings first, then fall back to env
    if key in saved and saved[key]:
        return saved[key]
    return getattr(env_settings, key, "")


@router.get("", response_model=AllSettingsResponse)
async def get_all_settings():
    """Get all settings (with sensitive values masked)."""
    saved = _load_saved_settings()
    env_settings = get_settings()

    # Telegram settings
    api_id = saved.get("telegram_api_id") or env_settings.telegram_api_id
    api_hash = saved.get("telegram_api_hash") or env_settings.telegram_api_hash
    phone = saved.get("telegram_phone") or env_settings.telegram_phone
    groups = saved.get("telegram_monitored_groups") or env_settings.telegram_monitored_groups

    # LLM settings
    openai_key = saved.get("openai_api_key") or env_settings.openai_api_key
    model = saved.get("openai_model") or "gpt-4o-mini"

    # Qdrant settings
    qdrant_url = saved.get("qdrant_url") or env_settings.qdrant_url
    qdrant_key = saved.get("qdrant_api_key") or env_settings.qdrant_api_key
    collection = saved.get("qdrant_collection_name") or env_settings.qdrant_collection_name

    return AllSettingsResponse(
        telegram=TelegramSettingsResponse(
            api_id=api_id,
            api_hash_masked=_mask_value(api_hash),
            phone=phone,
            monitored_groups=groups,
        ),
        llm=LLMSettingsResponse(
            openai_api_key_masked=_mask_value(openai_key),
            model=model,
        ),
        qdrant=QdrantSettingsResponse(
            url=qdrant_url,
            api_key_masked=_mask_value(qdrant_key),
            collection_name=collection,
        ),
    )


@router.get("/telegram", response_model=TelegramSettingsResponse)
async def get_telegram_settings():
    """Get Telegram settings."""
    saved = _load_saved_settings()
    env_settings = get_settings()

    api_id = saved.get("telegram_api_id") or env_settings.telegram_api_id
    api_hash = saved.get("telegram_api_hash") or env_settings.telegram_api_hash
    phone = saved.get("telegram_phone") or env_settings.telegram_phone
    groups = saved.get("telegram_monitored_groups") or env_settings.telegram_monitored_groups

    return TelegramSettingsResponse(
        api_id=api_id,
        api_hash_masked=_mask_value(api_hash),
        phone=phone,
        monitored_groups=groups,
    )


@router.put("/telegram", response_model=TelegramSettingsResponse)
async def update_telegram_settings(update: TelegramSettingsUpdate):
    """Update Telegram settings."""
    saved = _load_saved_settings()

    if update.api_id is not None:
        saved["telegram_api_id"] = update.api_id
    if update.api_hash is not None:
        saved["telegram_api_hash"] = update.api_hash
    if update.phone is not None:
        saved["telegram_phone"] = update.phone
    if update.monitored_groups is not None:
        saved["telegram_monitored_groups"] = update.monitored_groups

    _save_settings(saved)

    # Clear settings cache to pick up new values
    get_settings.cache_clear()

    return TelegramSettingsResponse(
        api_id=saved.get("telegram_api_id", 0),
        api_hash_masked=_mask_value(saved.get("telegram_api_hash", "")),
        phone=saved.get("telegram_phone", ""),
        monitored_groups=saved.get("telegram_monitored_groups", ""),
    )


@router.get("/llm", response_model=LLMSettingsResponse)
async def get_llm_settings():
    """Get LLM settings."""
    saved = _load_saved_settings()
    env_settings = get_settings()

    openai_key = saved.get("openai_api_key") or env_settings.openai_api_key
    model = saved.get("openai_model") or "gpt-4o-mini"

    return LLMSettingsResponse(
        openai_api_key_masked=_mask_value(openai_key),
        model=model,
    )


@router.put("/llm", response_model=LLMSettingsResponse)
async def update_llm_settings(update: LLMSettingsUpdate):
    """Update LLM settings."""
    saved = _load_saved_settings()

    if update.openai_api_key is not None:
        saved["openai_api_key"] = update.openai_api_key
    if update.model is not None:
        saved["openai_model"] = update.model

    _save_settings(saved)
    get_settings.cache_clear()

    return LLMSettingsResponse(
        openai_api_key_masked=_mask_value(saved.get("openai_api_key", "")),
        model=saved.get("openai_model", "gpt-4o-mini"),
    )


@router.get("/qdrant", response_model=QdrantSettingsResponse)
async def get_qdrant_settings():
    """Get Qdrant settings."""
    saved = _load_saved_settings()
    env_settings = get_settings()

    qdrant_url = saved.get("qdrant_url") or env_settings.qdrant_url
    qdrant_key = saved.get("qdrant_api_key") or env_settings.qdrant_api_key
    collection = saved.get("qdrant_collection_name") or env_settings.qdrant_collection_name

    return QdrantSettingsResponse(
        url=qdrant_url,
        api_key_masked=_mask_value(qdrant_key),
        collection_name=collection,
    )


@router.put("/qdrant", response_model=QdrantSettingsResponse)
async def update_qdrant_settings(update: QdrantSettingsUpdate):
    """Update Qdrant settings."""
    saved = _load_saved_settings()

    if update.url is not None:
        saved["qdrant_url"] = update.url
    if update.api_key is not None:
        saved["qdrant_api_key"] = update.api_key
    if update.collection_name is not None:
        saved["qdrant_collection_name"] = update.collection_name

    _save_settings(saved)
    get_settings.cache_clear()

    return QdrantSettingsResponse(
        url=saved.get("qdrant_url", ""),
        api_key_masked=_mask_value(saved.get("qdrant_api_key", "")),
        collection_name=saved.get("qdrant_collection_name", "polymarket_markets"),
    )
