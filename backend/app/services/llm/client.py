"""LLM client wrapper for OpenAI API."""

import json
import logging
from pathlib import Path
from typing import Optional

from openai import AsyncOpenAI

from app.config import get_settings

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


class LLMClient:
    """Async OpenAI client wrapper."""

    def __init__(self):
        self.env_settings = get_settings()
        self._saved_settings = _load_saved_settings()

        # Get effective settings (saved > env)
        self.openai_api_key = self._saved_settings.get("openai_api_key") or self.env_settings.openai_api_key
        self.openai_model = self._saved_settings.get("openai_model") or self.env_settings.openai_model

        self._client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> AsyncOpenAI:
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY not configured")
            self._client = AsyncOpenAI(api_key=self.openai_api_key)
        return self._client

    def is_configured(self) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(self.openai_api_key)

    async def complete(self, prompt: str, json_mode: bool = False) -> str:
        """
        Send a completion request to OpenAI.

        Args:
            prompt: The prompt to send
            json_mode: If True, request JSON response format

        Returns:
            The completion text
        """
        kwargs = {
            "model": self.openai_model,
            "messages": [{"role": "user", "content": prompt}],
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        logger.debug(f"LLM request: model={self.openai_model}, json_mode={json_mode}")

        response = await self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content

        logger.debug(f"LLM response length: {len(content) if content else 0}")
        return content or ""

    async def complete_json(self, prompt: str) -> dict:
        """
        Send completion and parse JSON response.

        Args:
            prompt: The prompt to send (should request JSON output)

        Returns:
            Parsed JSON dict
        """
        text = await self.complete(prompt, json_mode=True)
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}\nResponse: {text[:500]}")
            raise


# Singleton instance
llm_client = LLMClient()
