"""Telegram authentication service."""
import logging
from pathlib import Path

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from ...config import Settings, get_settings

logger = logging.getLogger(__name__)


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

    def _get_session_path(self, settings: Settings) -> str:
        """Get session file path."""
        path = Path(settings.telegram_session_path)
        path.mkdir(parents=True, exist_ok=True)
        return str(path / "session")

    async def connect(self) -> dict:
        """Start authentication - sends verification code."""
        settings = get_settings()

        if not settings.telegram_api_id:
            return {"success": False, "error": "API ID not configured"}
        if not settings.telegram_api_hash:
            return {"success": False, "error": "API Hash not configured"}
        if not settings.telegram_phone:
            return {"success": False, "error": "Phone number not configured"}

        try:
            session_path = self._get_session_path(settings)
            self._client = TelegramClient(
                session_path,
                settings.telegram_api_id,
                settings.telegram_api_hash,
            )

            await self._client.connect()

            if await self._client.is_user_authorized():
                self._authenticated = True
                logger.info("[TELEGRAM] Already authenticated")
                return {"success": True, "authenticated": True}

            # Send verification code
            await self._client.send_code_request(settings.telegram_phone)
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

        settings = get_settings()

        try:
            await self._client.sign_in(settings.telegram_phone, code)
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
        settings = get_settings()
        session_path = self._get_session_path(settings)

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
        settings = get_settings()
        session_path = self._get_session_path(settings)
        session_file = Path(session_path + ".session")

        return {
            "authenticated": self._authenticated,
            "has_session": session_file.exists(),
            "awaiting_code": self._awaiting_code,
            "connected": self._client is not None and self._client.is_connected(),
            "error": self._error,
            "configured": bool(settings.telegram_api_id and settings.telegram_api_hash),
        }

    def get_client(self) -> TelegramClient | None:
        """Get the authenticated client."""
        if self._authenticated and self._client:
            return self._client
        return None


# Global instance
telegram_auth = TelegramAuth.get_instance()
