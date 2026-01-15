"""Telegram authentication service."""
import json
import logging
from pathlib import Path

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from ...config import get_settings

logger = logging.getLogger(__name__)

# Settings file path (same as in routes/settings.py)
SETTINGS_FILE = Path("data/settings.json")


def _load_saved_settings() -> dict:
    """Load settings from JSON file."""
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _get_effective_telegram_settings() -> dict:
    """Get effective Telegram settings, preferring saved over env."""
    saved = _load_saved_settings()
    env_settings = get_settings()

    return {
        "api_id": saved.get("telegram_api_id") or env_settings.telegram_api_id,
        "api_hash": saved.get("telegram_api_hash") or env_settings.telegram_api_hash,
        "phone": saved.get("telegram_phone") or env_settings.telegram_phone,
        "session_path": env_settings.telegram_session_path,
    }


class TelegramAuth:
    """Singleton for Telegram authentication."""

    _instance = None
    _client: TelegramClient | None = None
    _awaiting_code: bool = False
    _authenticated: bool = False
    _error: str | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "TelegramAuth":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_session_path(self, session_path: str) -> str:
        """Get session file path."""
        path = Path(session_path)
        path.mkdir(parents=True, exist_ok=True)
        return str(path / "session")

    async def connect(self) -> dict:
        """Start authentication - sends verification code."""
        tg_settings = _get_effective_telegram_settings()

        if not tg_settings["api_id"]:
            return {"success": False, "error": "API ID not configured"}
        if not tg_settings["api_hash"]:
            return {"success": False, "error": "API Hash not configured"}
        if not tg_settings["phone"]:
            return {"success": False, "error": "Phone number not configured"}

        try:
            session_path = self._get_session_path(tg_settings["session_path"])
            self._client = TelegramClient(
                session_path,
                tg_settings["api_id"],
                tg_settings["api_hash"],
            )

            await self._client.connect()

            if await self._client.is_user_authorized():
                self._authenticated = True
                logger.info("[TELEGRAM] Already authenticated")
                return {"success": True, "authenticated": True}

            # Send verification code
            await self._client.send_code_request(tg_settings["phone"])
            self._awaiting_code = True
            logger.info("[TELEGRAM] Verification code sent")

            return {
                "success": True,
                "authenticated": False,
                "awaiting_code": True,
                "message": "Verification code sent to your Telegram app",
            }

        except Exception as e:
            self._error = str(e)
            logger.error(f"[TELEGRAM] Connect error: {e}")
            return {"success": False, "error": str(e)}

    async def verify_code(self, code: str, password: str | None = None) -> dict:
        """Submit verification code (and optional 2FA password)."""
        if not self._client:
            return {"success": False, "error": "Not connected"}
        if not self._awaiting_code:
            return {"success": False, "error": "Not awaiting code"}

        tg_settings = _get_effective_telegram_settings()

        try:
            await self._client.sign_in(tg_settings["phone"], code)
            self._authenticated = True
            self._awaiting_code = False
            logger.info("[TELEGRAM] Authenticated successfully")
            return {"success": True, "authenticated": True}

        except SessionPasswordNeededError:
            if password:
                try:
                    await self._client.sign_in(password=password)
                    self._authenticated = True
                    self._awaiting_code = False
                    return {"success": True, "authenticated": True}
                except Exception as e:
                    return {"success": False, "error": f"2FA failed: {e}"}
            return {"success": False, "needs_2fa": True, "error": "2FA password required"}

        except Exception as e:
            self._error = str(e)
            return {"success": False, "error": str(e)}

    async def disconnect(self) -> dict:
        """Log out and delete session."""
        tg_settings = _get_effective_telegram_settings()
        session_path = self._get_session_path(tg_settings["session_path"])

        if self._client:
            try:
                if self._client.is_connected():
                    await self._client.log_out()
            except Exception as e:
                logger.warning(f"[TELEGRAM] Logout error: {e}")
            finally:
                try:
                    await self._client.disconnect()
                except:
                    pass
            self._client = None

        # Delete session file
        session_file = Path(session_path + ".session")
        if session_file.exists():
            session_file.unlink()
            logger.info(f"[TELEGRAM] Deleted session: {session_file}")

        self._authenticated = False
        self._awaiting_code = False
        self._error = None

        return {"success": True, "message": "Disconnected"}

    def status(self) -> dict:
        """Get current auth status."""
        tg_settings = _get_effective_telegram_settings()
        session_path = self._get_session_path(tg_settings["session_path"])
        session_file = Path(session_path + ".session")

        return {
            "authenticated": self._authenticated,
            "has_session": session_file.exists(),
            "awaiting_code": self._awaiting_code,
            "connected": self._client is not None and self._client.is_connected(),
            "error": self._error,
            "configured": bool(tg_settings["api_id"] and tg_settings["api_hash"]),
        }

    def get_client(self) -> TelegramClient | None:
        """Get the authenticated client."""
        if self._authenticated and self._client:
            return self._client
        return None


# Global instance
telegram_auth = TelegramAuth.get_instance()
