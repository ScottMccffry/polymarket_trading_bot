"""OpenAI API client wrapper."""

from openai import AsyncOpenAI
import structlog

from ...config import get_settings
from ...core.exceptions import LLMError

logger = structlog.get_logger()


class OpenAIClient:
    """Wrapper for OpenAI API client."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        """Get or create the OpenAI client."""
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        return self._client

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.2,
        json_response: bool = False,
    ) -> str:
        """Make a chat completion request.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (defaults to settings)
            temperature: Sampling temperature
            json_response: Whether to request JSON output

        Returns:
            The assistant's response content
        """
        client = self._get_client()
        model = model or self.settings.openai_model

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"} if json_response else None,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("openai_error", error=str(e))
            raise LLMError(f"OpenAI API error: {e}")

    async def embed(self, text: str, model: str | None = None) -> list[float]:
        """Generate embeddings for text.

        Args:
            text: Text to embed
            model: Embedding model (defaults to settings)

        Returns:
            Embedding vector
        """
        client = self._get_client()
        model = model or self.settings.openai_embedding_model

        try:
            response = await client.embeddings.create(
                model=model,
                input=text,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error("embedding_error", error=str(e))
            raise LLMError(f"Embedding error: {e}")

    async def embed_batch(
        self,
        texts: list[str],
        model: str | None = None,
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            model: Embedding model

        Returns:
            List of embedding vectors
        """
        client = self._get_client()
        model = model or self.settings.openai_embedding_model

        try:
            response = await client.embeddings.create(
                model=model,
                input=texts,
            )
            return [d.embedding for d in response.data]
        except Exception as e:
            logger.error("batch_embedding_error", error=str(e))
            raise LLMError(f"Batch embedding error: {e}")
