"""Tests for trading strategies."""

import pytest
from datetime import datetime, timezone

from polybot.trading.strategies.builtin.general import GeneralStrategy
from polybot.trading.strategies.builtin.conservative import ConservativeStrategy
from polybot.trading.strategies.builtin.aggressive import AggressiveStrategy
from polybot.trading.strategies.builtin.trailing import TrailingStopStrategy
from polybot.trading.strategies.base import PositionContext


@pytest.fixture
def general_strategy():
    return GeneralStrategy()


@pytest.fixture
def conservative_strategy():
    return ConservativeStrategy()


@pytest.fixture
def aggressive_strategy():
    return AggressiveStrategy()


@pytest.fixture
def trailing_strategy():
    return TrailingStopStrategy()


def make_context(
    entry_price: float = 0.5,
    current_price: float = 0.5,
    side: str = "Yes",
    peak_price: float | None = None,
) -> PositionContext:
    """Helper to create position context."""
    return PositionContext(
        position_id="test",
        entry_price=entry_price,
        current_price=current_price,
        size=100,
        capital_allocated=50,
        side=side,
        peak_price=peak_price or entry_price,
        opened_at=datetime.now(timezone.utc),
        hours_open=1.0,
    )


class TestGeneralStrategy:
    def test_should_enter_valid(self, general_strategy):
        result = general_strategy.should_enter(
            confidence=0.8,
            spread=5.0,
            price=0.5,
        )
        assert result is True

    def test_should_enter_low_confidence(self, general_strategy):
        result = general_strategy.should_enter(
            confidence=0.5,
            spread=5.0,
            price=0.5,
        )
        assert result is False

    def test_should_enter_high_spread(self, general_strategy):
        result = general_strategy.should_enter(
            confidence=0.8,
            spread=20.0,
            price=0.5,
        )
        assert result is False

    def test_take_profit_yes(self, general_strategy):
        ctx = make_context(entry_price=0.5, current_price=0.8, side="Yes")
        decision = general_strategy.should_exit(ctx)
        assert decision.should_exit is True
        assert decision.reason == "take_profit"

    def test_stop_loss_yes(self, general_strategy):
        ctx = make_context(entry_price=0.5, current_price=0.35, side="Yes")
        decision = general_strategy.should_exit(ctx)
        assert decision.should_exit is True
        assert decision.reason == "stop_loss"

    def test_hold_yes(self, general_strategy):
        ctx = make_context(entry_price=0.5, current_price=0.55, side="Yes")
        decision = general_strategy.should_exit(ctx)
        assert decision.should_exit is False

    def test_take_profit_no(self, general_strategy):
        # For NO side, profit when price goes DOWN
        ctx = make_context(entry_price=0.5, current_price=0.2, side="No")
        decision = general_strategy.should_exit(ctx)
        assert decision.should_exit is True
        assert decision.reason == "take_profit"


class TestConservativeStrategy:
    def test_requires_higher_confidence(self, conservative_strategy):
        # Should reject 75% confidence
        result = conservative_strategy.should_enter(
            confidence=0.75,
            spread=3.0,
            price=0.5,
        )
        assert result is False

        # Should accept 85% confidence
        result = conservative_strategy.should_enter(
            confidence=0.85,
            spread=3.0,
            price=0.5,
        )
        assert result is True

    def test_tighter_stop_loss(self, conservative_strategy):
        # -15% stop loss vs general's -25%
        ctx = make_context(entry_price=0.5, current_price=0.42, side="Yes")
        decision = conservative_strategy.should_exit(ctx)
        assert decision.should_exit is True
        assert decision.reason == "stop_loss"


class TestAggressiveStrategy:
    def test_accepts_lower_confidence(self, aggressive_strategy):
        result = aggressive_strategy.should_enter(
            confidence=0.7,
            spread=5.0,
            price=0.5,
        )
        assert result is True

    def test_wider_stop_loss(self, aggressive_strategy):
        # -40% stop loss - should NOT exit at -30%
        ctx = make_context(entry_price=0.5, current_price=0.35, side="Yes")
        decision = aggressive_strategy.should_exit(ctx)
        assert decision.should_exit is False

        # Should exit at -45%
        ctx = make_context(entry_price=0.5, current_price=0.25, side="Yes")
        decision = aggressive_strategy.should_exit(ctx)
        assert decision.should_exit is True


class TestTrailingStopStrategy:
    def test_trailing_from_peak(self, trailing_strategy):
        # Price went up to 0.8 (60% gain), now at 0.6 (20% drop from peak)
        ctx = make_context(
            entry_price=0.5,
            current_price=0.6,
            peak_price=0.8,
            side="Yes",
        )
        decision = trailing_strategy.should_exit(ctx)
        assert decision.should_exit is True
        assert decision.reason == "trailing_stop"

    def test_no_trail_if_never_profitable(self, trailing_strategy):
        # Never went above entry, so no trailing
        ctx = make_context(
            entry_price=0.5,
            current_price=0.45,
            peak_price=0.5,
            side="Yes",
        )
        decision = trailing_strategy.should_exit(ctx)
        # Should hit initial stop loss instead
        assert decision.should_exit is False  # -10% not enough for -25% initial stop
