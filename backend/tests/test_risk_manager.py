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


def test_validate_drawdown_within_limit():
    config = RiskConfig(max_drawdown_percent=10.0)
    manager = RiskManager(config)

    # Peak was 1000, now 950 (5% drawdown)
    is_valid, error = manager.validate_drawdown(
        current_equity=950.0,
        peak_equity=1000.0
    )
    assert is_valid is True


def test_validate_drawdown_exceeded():
    config = RiskConfig(max_drawdown_percent=10.0)
    manager = RiskManager(config)

    # Peak was 1000, now 850 (15% drawdown)
    is_valid, error = manager.validate_drawdown(
        current_equity=850.0,
        peak_equity=1000.0
    )
    assert is_valid is False
    assert "drawdown" in error.lower()


def test_validate_open_positions_within_limit():
    config = RiskConfig(max_open_positions=10)
    manager = RiskManager(config)

    is_valid, error = manager.validate_open_positions(current_count=5)
    assert is_valid is True


def test_validate_open_positions_at_limit():
    config = RiskConfig(max_open_positions=10)
    manager = RiskManager(config)

    is_valid, error = manager.validate_open_positions(current_count=10)
    assert is_valid is False
    assert "max open positions" in error.lower()


def test_validate_trade_all_checks_pass():
    config = RiskConfig(
        max_position_size=100.0,
        max_portfolio_risk_percent=5.0,
        max_daily_loss=200.0,
        max_drawdown_percent=10.0,
        max_open_positions=10,
    )
    manager = RiskManager(config)

    result = manager.validate_trade(
        size_usd=50.0,
        capital=1000.0,
        current_equity=950.0,
        peak_equity=1000.0,
        open_position_count=3,
    )

    assert result.can_trade is True
    assert result.errors == []


def test_validate_trade_multiple_failures():
    config = RiskConfig(
        max_position_size=50.0,
        max_daily_loss=100.0,
        max_open_positions=5,
    )
    manager = RiskManager(config)
    manager.record_daily_pnl(-150.0)  # Exceed daily loss

    result = manager.validate_trade(
        size_usd=75.0,  # Exceeds max position
        capital=1000.0,
        current_equity=1000.0,
        peak_equity=1000.0,
        open_position_count=5,  # At limit
    )

    assert result.can_trade is False
    assert len(result.errors) == 3  # position size, daily loss, open positions


# Tests for settings file persistence
import json
from pathlib import Path


def test_risk_config_load_from_settings(tmp_path):
    # Create temp settings file
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(json.dumps({
        "risk_max_position_size": 75.0,
        "risk_max_daily_loss": 150.0,
        "risk_enabled": True,
    }))

    config = RiskConfig.from_settings_file(settings_file)

    assert config.max_position_size == 75.0
    assert config.max_daily_loss == 150.0
    assert config.enabled is True


def test_risk_config_save_to_settings(tmp_path):
    settings_file = tmp_path / "settings.json"
    settings_file.write_text("{}")

    config = RiskConfig(max_position_size=80.0, max_daily_loss=300.0)
    config.save_to_settings_file(settings_file)

    saved = json.loads(settings_file.read_text())
    assert saved["risk_max_position_size"] == 80.0
    assert saved["risk_max_daily_loss"] == 300.0
