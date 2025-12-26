"""Market analyzer using LLM for relevance and direction prediction."""

import json
from pydantic import BaseModel
import structlog

from .client import OpenAIClient
from ...core.exceptions import LLMError

logger = structlog.get_logger()


class MarketAnalysis(BaseModel):
    """Result of analyzing a market against a message."""

    is_relevant: bool
    side: str  # "Yes" or "No"
    confidence: float  # 0.0 - 1.0
    reasoning: str


class MarketAnalyzer:
    """Analyzes messages against prediction markets using LLM."""

    ANALYSIS_PROMPT = """You are a prediction market analyst. Analyze if the given message is relevant to the prediction market and predict which outcome (Yes or No) the message suggests.

Message to analyze:
{message}

Prediction Market:
Question: {question}
{description_section}

Instructions:
1. Determine if the message provides information relevant to this prediction market
2. If relevant, predict which outcome (Yes or No) the message suggests
3. Rate your confidence from 0.0 (no confidence) to 1.0 (very confident)

Respond with valid JSON only:
{{
    "is_relevant": true/false,
    "side": "Yes" or "No",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation (1-2 sentences)"
}}"""

    KEYWORDS_PROMPT = """Extract 3-5 search keywords from this message that would be useful for finding relevant prediction markets. Focus on:
- Named entities (people, organizations, places)
- Key topics or events
- Time-sensitive terms

Message:
{message}

Respond with valid JSON only:
{{
    "keywords": ["keyword1", "keyword2", "keyword3"]
}}"""

    def __init__(self) -> None:
        self.client = OpenAIClient()

    async def analyze_market(
        self,
        message: str,
        question: str,
        description: str | None = None,
    ) -> MarketAnalysis:
        """Analyze if a message is relevant to a market and predict direction.

        Args:
            message: The message text to analyze
            question: The market question
            description: Optional market description

        Returns:
            MarketAnalysis with relevance, side, confidence, and reasoning
        """
        description_section = f"Description: {description}" if description else ""

        prompt = self.ANALYSIS_PROMPT.format(
            message=message,
            question=question,
            description_section=description_section,
        )

        try:
            response = await self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                json_response=True,
                temperature=0.2,
            )

            data = json.loads(response)

            # Validate and normalize
            side = data.get("side", "Yes")
            if side.lower() not in ("yes", "no"):
                side = "Yes"
            side = side.capitalize()

            confidence = float(data.get("confidence", 0.0))
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]

            return MarketAnalysis(
                is_relevant=data.get("is_relevant", False),
                side=side,
                confidence=confidence,
                reasoning=data.get("reasoning", ""),
            )

        except json.JSONDecodeError as e:
            logger.warning("llm_json_parse_error", error=str(e), response=response)
            return MarketAnalysis(
                is_relevant=False,
                side="Yes",
                confidence=0.0,
                reasoning="Failed to parse LLM response",
            )
        except Exception as e:
            logger.error("analyze_market_error", error=str(e))
            raise LLMError(f"Market analysis failed: {e}")

    async def extract_keywords(self, message: str) -> list[str]:
        """Extract search keywords from a message.

        Args:
            message: The message text

        Returns:
            List of keywords for market search
        """
        prompt = self.KEYWORDS_PROMPT.format(message=message)

        try:
            response = await self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                json_response=True,
                temperature=0.1,
            )

            data = json.loads(response)
            keywords = data.get("keywords", [])

            # Validate keywords
            return [str(k).strip() for k in keywords if k and str(k).strip()]

        except json.JSONDecodeError as e:
            logger.warning("keywords_json_error", error=str(e))
            return []
        except Exception as e:
            logger.error("extract_keywords_error", error=str(e))
            return []
