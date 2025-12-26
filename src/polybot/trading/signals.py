"""Signal generator for creating trading signals from messages."""

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from ..models.market import Market
from ..models.signal import Signal
from ..services.llm.analyzer import MarketAnalyzer
from ..services.qdrant.client import QdrantService
from ..services.polymarket.client import PolymarketClient
from ..config import get_settings
from ..core.events import SignalCreated
from ..core.bus import EventBus

logger = structlog.get_logger()


class SignalGenerator:
    """Generates trading signals from messages."""

    def __init__(
        self,
        session: AsyncSession,
        event_bus: EventBus | None = None,
    ) -> None:
        self.session = session
        self.event_bus = event_bus
        self.settings = get_settings()
        self.analyzer = MarketAnalyzer()
        self.qdrant = QdrantService()
        self.polymarket = PolymarketClient()

    async def process_message(
        self,
        text: str,
        source: str,
    ) -> list[Signal]:
        """Process a message and generate signals.

        Args:
            text: Message text
            source: Source identifier (e.g., "telegram:GroupName")

        Returns:
            List of created signals
        """
        logger.debug("processing_message", source=source, text_length=len(text))

        # Find relevant markets
        markets = await self._find_markets(text)
        if not markets:
            logger.debug("no_markets_found", source=source)
            return []

        logger.debug("markets_found", count=len(markets))

        # Analyze each market and create signals
        signals = []
        for market in markets[:10]:  # Limit to top 10
            signal = await self._analyze_and_create_signal(text, market, source)
            if signal:
                signals.append(signal)

        if signals:
            logger.info("signals_created", source=source, count=len(signals))

        return signals

    async def _find_markets(self, text: str) -> list[Market]:
        """Find relevant markets for the message."""

        # Try semantic search first
        if self.qdrant.is_available:
            results = await self.qdrant.search(text, limit=10)
            if results:
                condition_ids = [r["condition_id"] for r in results]
                stmt = select(Market).where(
                    Market.condition_id.in_(condition_ids),
                    Market.active == True,
                )
                result = await self.session.execute(stmt)
                return list(result.scalars().all())

        # Fallback to keyword search
        keywords = await self.analyzer.extract_keywords(text)
        if not keywords:
            return []

        # Simple keyword matching
        stmt = select(Market).where(Market.active == True)
        result = await self.session.execute(stmt)
        all_markets = result.scalars().all()

        matched = []
        for market in all_markets:
            market_text = market.question.lower()
            if any(kw.lower() in market_text for kw in keywords):
                matched.append(market)

        return matched[:10]

    async def _analyze_and_create_signal(
        self,
        text: str,
        market: Market,
        source: str,
    ) -> Signal | None:
        """Analyze a market and create a signal if appropriate."""

        # Analyze with LLM
        analysis = await self.analyzer.analyze_market(
            message=text,
            question=market.question,
            description=market.description,
        )

        if not analysis.is_relevant:
            return None

        if analysis.confidence < self.settings.min_confidence:
            logger.debug(
                "signal_low_confidence",
                market_id=market.condition_id,
                confidence=analysis.confidence,
            )
            return None

        # Get token ID for the predicted side
        token_id = market.get_token_id(analysis.side)
        if not token_id:
            logger.warning("no_token_id", market_id=market.condition_id, side=analysis.side)
            return None

        # Get price and check spread
        try:
            bid, ask = await self.polymarket.get_best_prices(token_id)
            spread = ((ask - bid) / ask * 100) if ask > 0 else 100

            if spread > self.settings.max_spread_percent:
                logger.debug(
                    "signal_high_spread",
                    market_id=market.condition_id,
                    spread=spread,
                )
                return None

            price = ask  # Entry at ask price
            if not (self.settings.min_entry_price <= price <= self.settings.max_entry_price):
                logger.debug(
                    "signal_bad_price",
                    market_id=market.condition_id,
                    price=price,
                )
                return None

        except Exception as e:
            logger.error("price_fetch_error", market_id=market.condition_id, error=str(e))
            return None

        # Create signal
        signal = Signal(
            id=str(uuid.uuid4()),
            market_id=market.condition_id,
            token_id=token_id,
            market_question=market.question,
            side=analysis.side,
            confidence=analysis.confidence,
            price_at_signal=price,
            source=source,
            message_text=text,
            keywords=[],
        )

        self.session.add(signal)
        await self.session.flush()

        # Publish event
        if self.event_bus:
            await self.event_bus.publish(SignalCreated(
                signal_id=signal.id,
                market_id=signal.market_id,
                market_question=signal.market_question,
                side=signal.side,
                confidence=signal.confidence,
                price=signal.price_at_signal,
                source=signal.source,
            ))

        logger.info(
            "signal_created",
            signal_id=signal.id,
            market=market.question[:50],
            side=signal.side,
            confidence=signal.confidence,
        )

        return signal

    async def close(self) -> None:
        """Clean up resources."""
        await self.polymarket.close()
        await self.qdrant.close()
