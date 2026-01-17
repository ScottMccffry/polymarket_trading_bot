# backend/tests/test_risk_manager.py
from datetime import date

import pytest
from app.services.trading.risk_manager import RiskConfig, RiskManager


def test_risk_config_defaults():
    config = RiskConfig()
    assert config.max_position_size == 100.0
    assert config.max_portfolio_risk_percent == 2.0
    assert config.max_daily_loss == 200.0
    assert config.max_drawdown_percent == 10.0
    assert config.max_open_positions == 10
    assert config.enabled is True


def test_validate_position_size_within_limit():
    config = RiskConfig(max_position_size=100.0, max_portfolio_risk_percent=10.0)
    manager = RiskManager(config)

    # 10% of 1000 = 100, and max_position_size is 100, so 50 should pass both checks
    is_valid, error = manager.validate_position_size(50.0, capital=1000.0)
    assert is_valid is True
    assert error == ""


def test_validate_position_size_exceeds_max():
    config = RiskConfig(max_position_size=100.0, max_portfolio_risk_percent=20.0)
    manager = RiskManager(config)

    # 20% of 1000 = 200, so portfolio risk allows 150, but max_position_size is 100
    is_valid, error = manager.validate_position_size(150.0, capital=1000.0)
    assert is_valid is False
    assert "exceeds max" in error.lower()


def test_validate_position_size_exceeds_portfolio_risk():
    config = RiskConfig(max_position_size=100.0, max_portfolio_risk_percent=2.0)
    manager = RiskManager(config)

    # 2% of 1000 = 20, so 50 should fail
    is_valid, error = manager.validate_position_size(50.0, capital=1000.0)
    assert is_valid is False
    assert "portfolio risk" in error.lower()


def test_validate_daily_loss_within_limit():
    config = RiskConfig(max_daily_loss=200.0)
    manager = RiskManager(config)

    # Record some losses
    manager.record_daily_pnl(-50.0)
    manager.record_daily_pnl(-30.0)  # Total: -80

    is_valid, error = manager.validate_daily_loss()
    assert is_valid is True


def test_validate_daily_loss_exceeded():
    config = RiskConfig(max_daily_loss=200.0)
    manager = RiskManager(config)

    # Record losses exceeding limit
    manager.record_daily_pnl(-150.0)
    manager.record_daily_pnl(-100.0)  # Total: -250

    is_valid, error = manager.validate_daily_loss()
    assert is_valid is False
    assert "daily loss" in error.lower()


def test_daily_loss_resets_on_new_day():
    config = RiskConfig(max_daily_loss=200.0)
    manager = RiskManager(config)

    # Record loss
    manager.record_daily_pnl(-150.0)

    # Simulate new day
    manager._current_date = date(2020, 1, 1)  # Force old date
    manager._check_date_rollover()

    assert manager._daily_pnl == 0.0
