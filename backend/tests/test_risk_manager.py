# backend/tests/test_risk_manager.py
import pytest
from app.services.trading.risk_manager import RiskConfig


def test_risk_config_defaults():
    config = RiskConfig()
    assert config.max_position_size == 100.0
    assert config.max_portfolio_risk_percent == 2.0
    assert config.max_daily_loss == 200.0
    assert config.max_drawdown_percent == 10.0
    assert config.max_open_positions == 10
    assert config.enabled is True
