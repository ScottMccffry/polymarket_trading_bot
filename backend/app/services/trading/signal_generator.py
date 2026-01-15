"""
Signal Generator - Process messages and generate trading signals.

Pipeline: Message -> Qdrant Search -> LLM Analysis -> Signal
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signal import Signal, SignalCreate
from app.services.qdrant.client import QdrantService
from app.services.llm.analysis import MarketAnalyzer, MarketAnalysis

logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    Generates trading signals from messages.

    Process:
    1. Search Qdrant for semantically similar markets
    2. Analyze each market with LLM
    3. Create signals for actionable analyses
    """

    def __init__(
        self,
        qdrant: Optional[QdrantService] = None,
        analyzer: Optional[MarketAnalyzer] = None,
        min_confidence: float = 0.7,
        min_relevance: float = 0.5,
        search_limit: int = 10,
    ):
        self.qdrant = qdrant or QdrantService()
        self.analyzer = analyzer or MarketAnalyzer()
        self.min_confidence = min_confidence
        self.min_relevance = min_relevance
        self.search_limit = search_limit

    async def process_message(
        self,
        message: str,
        source: str,
        db: Optional[AsyncSession] = None,
    ) -> list[Signal]:
        """
        Process a message and generate signals.

        Args:
            message: The message text to process
            source: Source of the message (e.g., Telegram group name)
            db: Database session (if provided, signals are saved)

        Returns:
            List of generated Signal objects
        """
        if not self.qdrant.is_configured():
            logger.warning("Qdrant not configured, skipping signal generation")
            return []

        logger.info(f"[SIGNAL] Processing message from {source}: {message[:100]}...")

        # Step 1: Search Qdrant for matching markets
        markets = self.qdrant.search(
            query=message,
            limit=self.search_limit,
            score_threshold=0.3,
        )

        if not markets:
            logger.info("[SIGNAL] No matching markets found")
            return []

        logger.info(f"[SIGNAL] Found {len(markets)} potential markets")

        # Step 2: Analyze each market with LLM
        signals = []
        for market in markets:
            analysis = await self.analyzer.analyze(
                message=message,
                question=market.get("question", ""),
                description=market.get("description"),
                end_date=market.get("end_date_iso"),
            )

            # Step 3: Create signal if actionable
            if analysis.is_actionable(self.min_confidence):
                signal = self._create_signal(
                    message=message,
                    source=source,
                    market=market,
                    analysis=analysis,
                )
                signals.append(signal)

                logger.info(
                    f"[SIGNAL] Created signal: {signal.side} on "
                    f"'{market.get('question', '')[:50]}...' "
                    f"(conf={analysis.confidence:.2f})"
                )

                # Save to database if session provided
                if db:
                    db.add(signal)

        if db and signals:
            await db.commit()
            logger.info(f"[SIGNAL] Saved {len(signals)} signals to database")

        return signals

    def _create_signal(
        self,
        message: str,
        source: str,
        market: dict,
        analysis: MarketAnalysis,
    ) -> Signal:
        """Create a Signal object from analysis results."""
        signal_id = f"sig_{uuid.uuid4().hex[:12]}"

        return Signal(
            signal_id=signal_id,
            source=source,
            message_text=message[:2000],  # Truncate long messages
            keywords=None,  # Could extract keywords later
            market_id=market.get("condition_id"),
            token_id=None,  # Not available from Qdrant
            market_question=market.get("question"),
            side=analysis.direction,  # "BUY" or "SELL"
            confidence=analysis.confidence,
            price_at_signal=None,  # Could fetch current price
            created_at=datetime.utcnow().isoformat(),
        )

    async def analyze_single_market(
        self,
        message: str,
        market_question: str,
        market_description: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> MarketAnalysis:
        """
        Analyze a message against a single market.

        Useful for testing or manual analysis.
        """
        return await self.analyzer.analyze(
            message=message,
            question=market_question,
            description=market_description,
            end_date=end_date,
        )


# Singleton instance
signal_generator = SignalGenerator()
