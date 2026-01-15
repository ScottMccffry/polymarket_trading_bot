"""Market analysis using LLM."""

import logging
from dataclasses import dataclass
from typing import Optional

from .client import LLMClient, llm_client

logger = logging.getLogger(__name__)

DEFAULT_ANALYSIS_PROMPT = """You are a prediction market analyst. Analyze if this message provides actionable intelligence for this prediction market.

MESSAGE FROM TELEGRAM:
"{message}"

PREDICTION MARKET:
Question: "{question}"
Description: {description}
End date: {end_date}
Current YES price: {yes_price}

ANALYSIS GUIDELINES:
- BUY = message suggests YES outcome is MORE likely than current price implies
- SELL = message suggests NO outcome is MORE likely than current price implies
- NEUTRAL = no clear signal or message is irrelevant

Consider:
1. Is this message directly relevant to the market question?
2. Does it provide new information not yet priced in?
3. Is there enough time before market end for the signal to play out?
4. How credible is this information (official announcement vs speculation)?

Return JSON only:
{{
    "direction": "BUY" or "SELL" or "NEUTRAL",
    "confidence": 0.0-1.0,
    "relevance_score": 0.0-1.0,
    "reasoning": "brief explanation (1-2 sentences)",
    "message_type": "official_announcement" or "news" or "rumor" or "speculation" or "irrelevant",
    "time_span_appropriate": true/false,
    "days_until_end": number or null
}}"""


@dataclass
class MarketAnalysis:
    """Result of LLM market analysis."""

    direction: str  # "BUY", "SELL", or "NEUTRAL"
    confidence: float  # 0.0 - 1.0
    relevance_score: float  # 0.0 - 1.0
    reasoning: str
    message_type: str
    time_span_appropriate: bool
    days_until_end: Optional[int]

    def is_actionable(self, min_confidence: float = 0.7) -> bool:
        """Check if analysis suggests taking action."""
        return (
            self.direction in ("BUY", "SELL")
            and self.confidence >= min_confidence
            and self.relevance_score >= 0.5
            and self.time_span_appropriate
            and self.message_type != "irrelevant"
        )


class MarketAnalyzer:
    """Analyzes messages against prediction markets using LLM."""

    def __init__(self, client: Optional[LLMClient] = None):
        self.client = client or llm_client

    async def analyze(
        self,
        message: str,
        question: str,
        description: Optional[str] = None,
        end_date: Optional[str] = None,
        yes_price: Optional[float] = None,
    ) -> MarketAnalysis:
        """
        Analyze a message's relevance and signal for a market.

        Args:
            message: The message text to analyze
            question: The market question
            description: Market description (optional)
            end_date: Market end date (optional)
            yes_price: Current YES price 0.0-1.0 (optional)

        Returns:
            MarketAnalysis with direction, confidence, etc.
        """
        if not self.client.is_configured():
            logger.warning("LLM not configured, returning neutral analysis")
            return self._neutral_analysis("LLM not configured")

        prompt = DEFAULT_ANALYSIS_PROMPT.format(
            message=message[:2000],  # Truncate long messages
            question=question,
            description=description or "N/A",
            end_date=end_date or "N/A",
            yes_price=f"{yes_price:.2%}" if yes_price is not None else "N/A",
        )

        try:
            result = await self.client.complete_json(prompt)

            analysis = MarketAnalysis(
                direction=result.get("direction", "NEUTRAL").upper(),
                confidence=float(result.get("confidence", 0.0)),
                relevance_score=float(result.get("relevance_score", 0.0)),
                reasoning=result.get("reasoning", ""),
                message_type=result.get("message_type", "speculation"),
                time_span_appropriate=result.get("time_span_appropriate", True),
                days_until_end=result.get("days_until_end"),
            )

            logger.info(
                f"Market analysis: {question[:50]}... -> "
                f"{analysis.direction} (conf={analysis.confidence:.2f}, "
                f"rel={analysis.relevance_score:.2f})"
            )

            return analysis

        except Exception as e:
            logger.error(f"Analysis error for market '{question[:50]}...': {e}")
            return self._neutral_analysis(f"Error: {e}")

    def _neutral_analysis(self, reason: str) -> MarketAnalysis:
        """Return a neutral/error analysis."""
        return MarketAnalysis(
            direction="NEUTRAL",
            confidence=0.0,
            relevance_score=0.0,
            reasoning=reason,
            message_type="irrelevant",
            time_span_appropriate=False,
            days_until_end=None,
        )


# Singleton instance
market_analyzer = MarketAnalyzer()
