"""Tests for trading executor service."""
import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, AsyncMock, patch

from app.models.position import Position
from app.models.strategy import CustomStrategy, AdvancedStrategy
from app.services.trading.executor import StrategyExecutor


class TestStrategyExecutor:
    """Test suite for StrategyExecutor."""

    @pytest.mark.asyncio
    async def test_executor_initialization(self):
        """Test executor initializes correctly."""
        executor = StrategyExecutor(initial_capital=10000.0)
        assert executor.simulation is not None
        assert executor.polymarket is not None
        assert executor._strategy_cache == {}

    @pytest.mark.asyncio
    async def test_load_custom_strategy(self, db_session):
        """Test loading a custom strategy from database."""
        now = datetime.now(UTC).isoformat()
        strategy = CustomStrategy(
            name="Test Strategy",
            take_profit=15.0,
            stop_loss=-10.0,
            trailing_stop=5.0,
            created_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        executor = StrategyExecutor()
        loaded = await executor.load_custom_strategy(db_session, strategy.id)

        assert loaded is not None
        assert loaded.name == "Test Strategy"
        assert loaded.take_profit == 15.0
        assert loaded.stop_loss == -10.0

    @pytest.mark.asyncio
    async def test_load_custom_strategy_caches(self, db_session):
        """Test that loaded strategies are cached."""
        now = datetime.now(UTC).isoformat()
        strategy = CustomStrategy(
            name="Test Strategy",
            take_profit=15.0,
            stop_loss=-10.0,
            created_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        executor = StrategyExecutor()

        # Load twice
        loaded1 = await executor.load_custom_strategy(db_session, strategy.id)
        loaded2 = await executor.load_custom_strategy(db_session, strategy.id)

        # Should be same instance (cached)
        assert loaded1 is loaded2

    @pytest.mark.asyncio
    async def test_load_nonexistent_strategy(self, db_session):
        """Test loading non-existent strategy returns None."""
        executor = StrategyExecutor()
        loaded = await executor.load_custom_strategy(db_session, 99999)
        assert loaded is None

    @pytest.mark.asyncio
    async def test_load_advanced_strategy(self, db_session):
        """Test loading an advanced strategy from database."""
        now = datetime.now(UTC).isoformat()
        strategy = AdvancedStrategy(
            name="Advanced Test",
            default_take_profit=20.0,
            default_stop_loss=-15.0,
            default_trailing_stop=8.0,
            enabled=1,
            created_at=now,
            updated_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        executor = StrategyExecutor()
        loaded = await executor.load_advanced_strategy(db_session, strategy.id)

        assert loaded is not None
        assert loaded.config.name == "Advanced Test"
        assert loaded.config.default_take_profit == 20.0

    @pytest.mark.asyncio
    async def test_load_disabled_advanced_strategy(self, db_session):
        """Test loading a disabled advanced strategy returns None."""
        now = datetime.now(UTC).isoformat()
        strategy = AdvancedStrategy(
            name="Disabled",
            default_take_profit=20.0,
            default_stop_loss=-15.0,
            enabled=0,  # Disabled
            created_at=now,
            updated_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        executor = StrategyExecutor()
        loaded = await executor.load_advanced_strategy(db_session, strategy.id)
        assert loaded is None

    @pytest.mark.asyncio
    async def test_check_position_exits_empty(self, db_session):
        """Test checking positions when none exist."""
        executor = StrategyExecutor()
        exits = await executor.check_position_exits(db_session)
        assert exits == []

    @pytest.mark.asyncio
    async def test_check_position_exits_no_strategy(self, db_session):
        """Test position without strategy is skipped."""
        now = datetime.now(UTC).isoformat()
        position = Position(
            signal_id="test",
            strategy_id=None,  # No strategy
            entry_price=0.50,
            size=100.0,
            status="open",
            opened_at=now,
        )
        db_session.add(position)
        await db_session.commit()

        executor = StrategyExecutor()
        exits = await executor.check_position_exits(db_session)
        assert exits == []

    @pytest.mark.asyncio
    @patch('app.services.trading.executor.PolymarketClient')
    async def test_check_position_take_profit_hit(self, mock_client_class, db_session):
        """Test position closes when take profit is hit."""
        now = datetime.now(UTC).isoformat()

        # Create strategy
        strategy = CustomStrategy(
            name="Test",
            take_profit=20.0,  # 20% profit target
            stop_loss=10.0,   # Exit if loss exceeds 10%
            created_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        # Create position
        position = Position(
            signal_id="test",
            strategy_id=strategy.id,
            token_id="token123",
            entry_price=0.50,
            size=100.0,
            status="open",
            opened_at=now,
        )
        db_session.add(position)
        await db_session.commit()

        # Mock price data (25% gain)
        mock_client = Mock()
        mock_client.get_price.return_value = {"price": "0.625"}
        mock_client_class.return_value = mock_client

        executor = StrategyExecutor()
        executor.polymarket = mock_client

        exits = await executor.check_position_exits(db_session)

        # Should have exited due to take profit
        assert len(exits) == 1
        assert exits[0]["action"] == "close"
        assert "profit" in exits[0]["reason"].lower()

    @pytest.mark.asyncio
    @patch('app.services.trading.executor.PolymarketClient')
    async def test_check_position_stop_loss_hit(self, mock_client_class, db_session):
        """Test position closes when stop loss is hit."""
        now = datetime.now(UTC).isoformat()

        # Create strategy
        strategy = CustomStrategy(
            name="Test",
            take_profit=20.0,
            stop_loss=10.0,  # Exit if loss exceeds 10%
            created_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        # Create position
        position = Position(
            signal_id="test",
            strategy_id=strategy.id,
            token_id="token123",
            entry_price=0.50,
            size=100.0,
            status="open",
            opened_at=now,
        )
        db_session.add(position)
        await db_session.commit()

        # Mock price data (-15% loss)
        mock_client = Mock()
        mock_client.get_price.return_value = {"price": "0.425"}
        mock_client_class.return_value = mock_client

        executor = StrategyExecutor()
        executor.polymarket = mock_client

        exits = await executor.check_position_exits(db_session)

        # Should have exited due to stop loss
        assert len(exits) == 1
        assert exits[0]["action"] == "close"
        assert "stop" in exits[0]["reason"].lower()

    @pytest.mark.asyncio
    @patch('app.services.trading.executor.PolymarketClient')
    async def test_check_position_updates_unrealized_pnl(self, mock_client_class, db_session):
        """Test that unrealized P&L is updated for open positions."""
        now = datetime.now(UTC).isoformat()

        # Create strategy with high thresholds so position stays open
        strategy = CustomStrategy(
            name="Test",
            take_profit=50.0,  # High target so it doesn't close
            stop_loss=50.0,   # Positive value - exit if loss exceeds 50%
            created_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        # Create position
        position = Position(
            signal_id="test",
            strategy_id=strategy.id,
            token_id="token123",
            entry_price=0.50,
            size=100.0,
            status="open",
            opened_at=now,
        )
        db_session.add(position)
        await db_session.commit()
        await db_session.refresh(position)

        # Mock price data (small gain, shouldn't trigger exit)
        mock_client = Mock()
        mock_client.get_price.return_value = {"price": "0.55"}
        mock_client_class.return_value = mock_client

        executor = StrategyExecutor()
        executor.polymarket = mock_client

        await executor.check_position_exits(db_session)
        await db_session.refresh(position)

        # Position should still be open with updated unrealized P&L
        assert position.status == "open"
        assert position.unrealized_pnl is not None
        assert position.current_price == 0.55

    @pytest.mark.asyncio
    @patch('app.services.trading.executor.PolymarketClient')
    async def test_check_position_partial_exit(self, mock_client_class, db_session):
        """Test partial exit functionality."""
        now = datetime.now(UTC).isoformat()

        # Create strategy with partial exit
        strategy = CustomStrategy(
            name="Test",
            take_profit=50.0,
            stop_loss=50.0,  # Positive value - exit if loss exceeds 50%
            partial_exit_percent=50.0,  # Exit 50%
            partial_exit_threshold=10.0,  # At 10% profit
            created_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        # Create position
        position = Position(
            signal_id="test",
            strategy_id=strategy.id,
            token_id="token123",
            entry_price=0.50,
            size=100.0,
            status="open",
            opened_at=now,
        )
        db_session.add(position)
        await db_session.commit()

        # Mock price data (12% gain, triggers partial exit)
        mock_client = Mock()
        mock_client.get_price.return_value = {"price": "0.56"}
        mock_client_class.return_value = mock_client

        executor = StrategyExecutor()
        executor.polymarket = mock_client

        exits = await executor.check_position_exits(db_session)

        # Should have partial exit
        assert len(exits) == 1
        assert exits[0]["action"] == "partial_exit"
        assert exits[0]["exit_percent"] == 0.5

    @pytest.mark.asyncio
    @patch('app.services.trading.executor.PolymarketClient')
    async def test_check_position_price_fetch_error(self, mock_client_class, db_session):
        """Test handling of price fetch errors."""
        now = datetime.now(UTC).isoformat()

        # Create strategy and position
        strategy = CustomStrategy(
            name="Test",
            take_profit=20.0,
            stop_loss=10.0,  # Exit if loss exceeds 10%
            created_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        position = Position(
            signal_id="test",
            strategy_id=strategy.id,
            token_id="token123",
            entry_price=0.50,
            size=100.0,
            status="open",
            opened_at=now,
        )
        db_session.add(position)
        await db_session.commit()

        # Mock price fetch error
        mock_client = Mock()
        mock_client.get_price.side_effect = Exception("API error")
        mock_client_class.return_value = mock_client

        executor = StrategyExecutor()
        executor.polymarket = mock_client

        exits = await executor.check_position_exits(db_session)

        # Should handle error gracefully, no exits
        assert exits == []

    @pytest.mark.asyncio
    async def test_clear_cache(self):
        """Test clearing strategy cache."""
        executor = StrategyExecutor()
        executor._strategy_cache[1] = Mock()
        executor._strategy_cache[2] = Mock()

        assert len(executor._strategy_cache) == 2

        executor.clear_cache()

        assert len(executor._strategy_cache) == 0
