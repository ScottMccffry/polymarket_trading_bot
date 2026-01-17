# Risk Management Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add pre-trade risk controls to protect capital and enforce trading discipline.

**Architecture:** A `RiskManager` service performs validation before any position is opened. It checks position sizing rules, daily loss limits, max drawdown, and max open positions. Risk config is stored in `data/settings.json` alongside trading settings.

**Tech Stack:** Python 3.12, SQLAlchemy async, pytest

---

## Task 1: Create RiskConfig Model

**Files:**
- Create: `backend/app/services/trading/risk_manager.py`
- Test: `backend/tests/test_risk_manager.py`

**Step 1: Write the failing test for RiskConfig**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_risk_manager.py::test_risk_config_defaults -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# backend/app/services/trading/risk_manager.py
"""
Risk Manager - Pre-trade risk validation.

Enforces position sizing, daily loss limits, and drawdown protection.
"""

from dataclasses import dataclass, field


@dataclass
class RiskConfig:
    """Risk management configuration."""
    # Position limits
    max_position_size: float = 100.0  # Max USD per position
    max_portfolio_risk_percent: float = 2.0  # Max % of capital per trade

    # Loss limits
    max_daily_loss: float = 200.0  # Max loss per day in USD
    max_drawdown_percent: float = 10.0  # Max % drawdown from peak

    # Position limits
    max_open_positions: int = 10  # Max concurrent positions

    # Master switch
    enabled: bool = True
```

**Step 4: Run test to verify it passes**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_risk_manager.py::test_risk_config_defaults -v`
Expected: PASS

**Step 5: Commit**

```bash
cd /Users/armandfatalot/polymarket_trading_bot
git add backend/app/services/trading/risk_manager.py backend/tests/test_risk_manager.py
git commit -m "feat(risk): add RiskConfig dataclass with defaults"
```

---

## Task 2: Add Position Size Validation

**Files:**
- Modify: `backend/app/services/trading/risk_manager.py`
- Test: `backend/tests/test_risk_manager.py`

**Step 1: Write the failing test for position size check**

```python
# Add to backend/tests/test_risk_manager.py

def test_validate_position_size_within_limit():
    config = RiskConfig(max_position_size=100.0)
    manager = RiskManager(config)

    is_valid, error = manager.validate_position_size(50.0, capital=1000.0)
    assert is_valid is True
    assert error == ""


def test_validate_position_size_exceeds_max():
    config = RiskConfig(max_position_size=100.0)
    manager = RiskManager(config)

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
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_risk_manager.py::test_validate_position_size_within_limit -v`
Expected: FAIL with "cannot import name 'RiskManager'"

**Step 3: Write minimal implementation**

```python
# Add to backend/app/services/trading/risk_manager.py after RiskConfig

class RiskManager:
    """
    Pre-trade risk validation.

    Call validate_* methods before opening positions.
    """

    def __init__(self, config: RiskConfig | None = None):
        self.config = config or RiskConfig()

    def validate_position_size(
        self,
        size_usd: float,
        capital: float,
    ) -> tuple[bool, str]:
        """
        Validate position size against limits.

        Args:
            size_usd: Proposed position size in USD
            capital: Total available capital

        Returns:
            (is_valid, error_message)
        """
        if not self.config.enabled:
            return True, ""

        # Check absolute max
        if size_usd > self.config.max_position_size:
            return False, f"Position size ${size_usd:.2f} exceeds max ${self.config.max_position_size:.2f}"

        # Check portfolio risk percentage
        if capital > 0:
            max_risk_amount = capital * (self.config.max_portfolio_risk_percent / 100)
            if size_usd > max_risk_amount:
                return False, (
                    f"Position size ${size_usd:.2f} exceeds portfolio risk limit "
                    f"({self.config.max_portfolio_risk_percent}% of ${capital:.2f} = ${max_risk_amount:.2f})"
                )

        return True, ""
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_risk_manager.py -v -k "position_size"`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
cd /Users/armandfatalot/polymarket_trading_bot
git add backend/app/services/trading/risk_manager.py backend/tests/test_risk_manager.py
git commit -m "feat(risk): add position size validation"
```

---

## Task 3: Add Daily Loss Tracking

**Files:**
- Modify: `backend/app/services/trading/risk_manager.py`
- Test: `backend/tests/test_risk_manager.py`

**Step 1: Write the failing test for daily loss check**

```python
# Add to backend/tests/test_risk_manager.py
from datetime import date


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
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_risk_manager.py::test_validate_daily_loss_within_limit -v`
Expected: FAIL with "has no attribute 'record_daily_pnl'"

**Step 3: Write minimal implementation**

```python
# Add imports at top of risk_manager.py
from datetime import date

# Add to RiskManager class __init__:
        self._daily_pnl: float = 0.0
        self._current_date: date = date.today()

# Add methods to RiskManager class:

    def _check_date_rollover(self) -> None:
        """Reset daily P&L if date changed."""
        today = date.today()
        if today != self._current_date:
            self._daily_pnl = 0.0
            self._current_date = today

    def record_daily_pnl(self, pnl: float) -> None:
        """
        Record realized P&L for daily tracking.

        Call this when a position is closed.
        """
        self._check_date_rollover()
        self._daily_pnl += pnl

    def validate_daily_loss(self) -> tuple[bool, str]:
        """
        Check if daily loss limit has been exceeded.

        Returns:
            (is_valid, error_message)
        """
        if not self.config.enabled:
            return True, ""

        self._check_date_rollover()

        if self._daily_pnl < 0 and abs(self._daily_pnl) >= self.config.max_daily_loss:
            return False, (
                f"Daily loss limit reached: ${abs(self._daily_pnl):.2f} "
                f"(max: ${self.config.max_daily_loss:.2f})"
            )

        return True, ""

    def get_daily_pnl(self) -> float:
        """Get current daily P&L."""
        self._check_date_rollover()
        return self._daily_pnl
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_risk_manager.py -v -k "daily_loss"`
Expected: All 3 tests PASS

**Step 5: Commit**

```bash
cd /Users/armandfatalot/polymarket_trading_bot
git add backend/app/services/trading/risk_manager.py backend/tests/test_risk_manager.py
git commit -m "feat(risk): add daily loss tracking and validation"
```

---

## Task 4: Add Max Drawdown Protection

**Files:**
- Modify: `backend/app/services/trading/risk_manager.py`
- Test: `backend/tests/test_risk_manager.py`

**Step 1: Write the failing test for drawdown check**

```python
# Add to backend/tests/test_risk_manager.py

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
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_risk_manager.py::test_validate_drawdown_within_limit -v`
Expected: FAIL with "has no attribute 'validate_drawdown'"

**Step 3: Write minimal implementation**

```python
# Add to RiskManager class:

    def validate_drawdown(
        self,
        current_equity: float,
        peak_equity: float,
    ) -> tuple[bool, str]:
        """
        Check if max drawdown has been exceeded.

        Args:
            current_equity: Current portfolio value
            peak_equity: Highest portfolio value recorded

        Returns:
            (is_valid, error_message)
        """
        if not self.config.enabled:
            return True, ""

        if peak_equity <= 0:
            return True, ""

        drawdown_pct = ((peak_equity - current_equity) / peak_equity) * 100

        if drawdown_pct >= self.config.max_drawdown_percent:
            return False, (
                f"Max drawdown exceeded: {drawdown_pct:.1f}% "
                f"(max: {self.config.max_drawdown_percent}%)"
            )

        return True, ""
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_risk_manager.py -v -k "drawdown"`
Expected: All 2 tests PASS

**Step 5: Commit**

```bash
cd /Users/armandfatalot/polymarket_trading_bot
git add backend/app/services/trading/risk_manager.py backend/tests/test_risk_manager.py
git commit -m "feat(risk): add max drawdown validation"
```

---

## Task 5: Add Max Open Positions Check

**Files:**
- Modify: `backend/app/services/trading/risk_manager.py`
- Test: `backend/tests/test_risk_manager.py`

**Step 1: Write the failing test**

```python
# Add to backend/tests/test_risk_manager.py

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
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_risk_manager.py::test_validate_open_positions_within_limit -v`
Expected: FAIL with "has no attribute 'validate_open_positions'"

**Step 3: Write minimal implementation**

```python
# Add to RiskManager class:

    def validate_open_positions(self, current_count: int) -> tuple[bool, str]:
        """
        Check if we can open another position.

        Args:
            current_count: Number of currently open positions

        Returns:
            (is_valid, error_message)
        """
        if not self.config.enabled:
            return True, ""

        if current_count >= self.config.max_open_positions:
            return False, (
                f"Max open positions reached: {current_count} "
                f"(max: {self.config.max_open_positions})"
            )

        return True, ""
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_risk_manager.py -v -k "open_positions"`
Expected: All 2 tests PASS

**Step 5: Commit**

```bash
cd /Users/armandfatalot/polymarket_trading_bot
git add backend/app/services/trading/risk_manager.py backend/tests/test_risk_manager.py
git commit -m "feat(risk): add max open positions validation"
```

---

## Task 6: Add Combined Pre-Trade Validation

**Files:**
- Modify: `backend/app/services/trading/risk_manager.py`
- Test: `backend/tests/test_risk_manager.py`

**Step 1: Write the failing test**

```python
# Add to backend/tests/test_risk_manager.py

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
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_risk_manager.py::test_validate_trade_all_checks_pass -v`
Expected: FAIL with "has no attribute 'validate_trade'"

**Step 3: Write minimal implementation**

```python
# Add after RiskConfig dataclass in risk_manager.py:

@dataclass
class TradeValidationResult:
    """Result of pre-trade validation."""
    can_trade: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# Add to RiskManager class:

    def validate_trade(
        self,
        size_usd: float,
        capital: float,
        current_equity: float,
        peak_equity: float,
        open_position_count: int,
    ) -> TradeValidationResult:
        """
        Run all pre-trade validations.

        Args:
            size_usd: Proposed position size
            capital: Available trading capital
            current_equity: Current portfolio value
            peak_equity: Peak portfolio value
            open_position_count: Current open position count

        Returns:
            TradeValidationResult with can_trade flag and any errors
        """
        errors = []

        # Position size check
        valid, error = self.validate_position_size(size_usd, capital)
        if not valid:
            errors.append(error)

        # Daily loss check
        valid, error = self.validate_daily_loss()
        if not valid:
            errors.append(error)

        # Drawdown check
        valid, error = self.validate_drawdown(current_equity, peak_equity)
        if not valid:
            errors.append(error)

        # Open positions check
        valid, error = self.validate_open_positions(open_position_count)
        if not valid:
            errors.append(error)

        return TradeValidationResult(
            can_trade=len(errors) == 0,
            errors=errors,
        )
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_risk_manager.py -v -k "validate_trade"`
Expected: All 2 tests PASS

**Step 5: Commit**

```bash
cd /Users/armandfatalot/polymarket_trading_bot
git add backend/app/services/trading/risk_manager.py backend/tests/test_risk_manager.py
git commit -m "feat(risk): add combined pre-trade validation"
```

---

## Task 7: Add Settings Persistence

**Files:**
- Modify: `backend/app/services/trading/risk_manager.py`
- Test: `backend/tests/test_risk_manager.py`

**Step 1: Write the failing test**

```python
# Add to backend/tests/test_risk_manager.py
import json
from pathlib import Path
import tempfile


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
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_risk_manager.py::test_risk_config_load_from_settings -v`
Expected: FAIL with "has no attribute 'from_settings_file'"

**Step 3: Write minimal implementation**

```python
# Add imports at top of risk_manager.py:
import json
from pathlib import Path

# Add class methods to RiskConfig:

    @classmethod
    def from_settings_file(cls, path: Path) -> "RiskConfig":
        """Load risk config from settings file."""
        if not path.exists():
            return cls()

        try:
            with open(path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return cls()

        return cls(
            max_position_size=data.get("risk_max_position_size", 100.0),
            max_portfolio_risk_percent=data.get("risk_max_portfolio_risk_percent", 2.0),
            max_daily_loss=data.get("risk_max_daily_loss", 200.0),
            max_drawdown_percent=data.get("risk_max_drawdown_percent", 10.0),
            max_open_positions=data.get("risk_max_open_positions", 10),
            enabled=data.get("risk_enabled", True),
        )

    def save_to_settings_file(self, path: Path) -> None:
        """Save risk config to settings file."""
        # Load existing settings
        data = {}
        if path.exists():
            try:
                with open(path) as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                data = {}

        # Update risk settings
        data["risk_max_position_size"] = self.max_position_size
        data["risk_max_portfolio_risk_percent"] = self.max_portfolio_risk_percent
        data["risk_max_daily_loss"] = self.max_daily_loss
        data["risk_max_drawdown_percent"] = self.max_drawdown_percent
        data["risk_max_open_positions"] = self.max_open_positions
        data["risk_enabled"] = self.enabled

        # Write back
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_risk_manager.py -v -k "settings"`
Expected: All 2 tests PASS

**Step 5: Commit**

```bash
cd /Users/armandfatalot/polymarket_trading_bot
git add backend/app/services/trading/risk_manager.py backend/tests/test_risk_manager.py
git commit -m "feat(risk): add settings file persistence"
```

---

## Task 8: Create Singleton and Integration Helper

**Files:**
- Modify: `backend/app/services/trading/risk_manager.py`

**Step 1: Write the failing test**

```python
# Add to backend/tests/test_risk_manager.py

def test_risk_manager_singleton():
    from app.services.trading.risk_manager import risk_manager

    assert risk_manager is not None
    assert isinstance(risk_manager, RiskManager)


def test_risk_manager_reload_config():
    from app.services.trading.risk_manager import risk_manager

    # Should not raise
    risk_manager.reload_config()
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_risk_manager.py::test_risk_manager_singleton -v`
Expected: FAIL with "cannot import name 'risk_manager'"

**Step 3: Write minimal implementation**

```python
# Add at bottom of risk_manager.py:

SETTINGS_FILE = Path("data/settings.json")


# Add method to RiskManager class:

    def reload_config(self) -> None:
        """Reload config from settings file."""
        self.config = RiskConfig.from_settings_file(SETTINGS_FILE)


# Singleton instance
risk_manager = RiskManager(RiskConfig.from_settings_file(SETTINGS_FILE))
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_risk_manager.py -v -k "singleton or reload"`
Expected: All 2 tests PASS

**Step 5: Commit**

```bash
cd /Users/armandfatalot/polymarket_trading_bot
git add backend/app/services/trading/risk_manager.py backend/tests/test_risk_manager.py
git commit -m "feat(risk): add singleton instance and reload"
```

---

## Task 9: Integrate with PositionManager

**Files:**
- Modify: `backend/app/services/trading/position_manager.py`
- Test: `backend/tests/test_position_manager_risk.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_position_manager_risk.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.trading.position_manager import PositionManager
from app.services.trading.risk_manager import RiskConfig, RiskManager


@pytest.mark.asyncio
async def test_open_position_blocked_by_risk():
    """Position should not open if risk check fails."""
    # Create manager with strict risk config
    config = RiskConfig(max_position_size=30.0)

    with patch("app.services.trading.position_manager.risk_manager") as mock_rm:
        mock_rm.validate_trade.return_value = MagicMock(
            can_trade=False,
            errors=["Position size exceeds max"]
        )

        pm = PositionManager()
        db = AsyncMock()
        signal = MagicMock(
            signal_id="test-1",
            market_id="market-1",
            token_id="token-1",
            side="BUY",
            price_at_signal=0.5,
            source="test",
            market_question="Test?"
        )

        result = await pm.open_position(
            db=db,
            signal=signal,
            size=50.0,  # Exceeds max
        )

        assert result is None  # Position not opened
        db.add.assert_not_called()
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_position_manager_risk.py -v`
Expected: FAIL (returns Position instead of None)

**Step 3: Modify position_manager.py**

```python
# Add import at top of position_manager.py:
from app.services.trading.risk_manager import risk_manager

# Modify open_position method, add after line 57 (size = size or self.DEFAULT_POSITION_SIZE):

        # Run risk validation
        open_positions = await self.get_open_positions(db)
        risk_result = risk_manager.validate_trade(
            size_usd=size,
            capital=10000.0,  # TODO: Get from portfolio tracker
            current_equity=10000.0,  # TODO: Get from portfolio tracker
            peak_equity=10000.0,  # TODO: Get from portfolio tracker
            open_position_count=len(open_positions),
        )

        if not risk_result.can_trade:
            logger.warning(
                f"[POSITION] Risk check failed for signal {signal.signal_id}: "
                f"{', '.join(risk_result.errors)}"
            )
            return None
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_position_manager_risk.py -v`
Expected: PASS

**Step 5: Commit**

```bash
cd /Users/armandfatalot/polymarket_trading_bot
git add backend/app/services/trading/position_manager.py backend/tests/test_position_manager_risk.py
git commit -m "feat(risk): integrate risk checks into position opening"
```

---

## Task 10: Add Risk Settings API Endpoint

**Files:**
- Modify: `backend/app/routes/bot.py`
- Test: `backend/tests/test_bot_routes.py`

**Step 1: Write the failing test**

```python
# Add to backend/tests/test_bot_routes.py (or create if doesn't exist)
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_risk_settings(client: AsyncClient, auth_headers):
    response = await client.get("/api/bot/risk", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "max_position_size" in data
    assert "max_daily_loss" in data
    assert "enabled" in data


@pytest.mark.asyncio
async def test_update_risk_settings(client: AsyncClient, auth_headers):
    response = await client.put(
        "/api/bot/risk",
        headers=auth_headers,
        json={
            "max_position_size": 75.0,
            "max_daily_loss": 150.0,
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["max_position_size"] == 75.0
```

**Step 2: Run test to verify it fails**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_bot_routes.py::test_get_risk_settings -v`
Expected: FAIL with 404

**Step 3: Add endpoints to bot.py**

```python
# Add imports at top of backend/app/routes/bot.py:
from ..services.trading.risk_manager import risk_manager, RiskConfig, SETTINGS_FILE
from pydantic import BaseModel

# Add Pydantic models:
class RiskSettingsResponse(BaseModel):
    max_position_size: float
    max_portfolio_risk_percent: float
    max_daily_loss: float
    max_drawdown_percent: float
    max_open_positions: int
    enabled: bool
    daily_pnl: float


class RiskSettingsUpdate(BaseModel):
    max_position_size: float | None = None
    max_portfolio_risk_percent: float | None = None
    max_daily_loss: float | None = None
    max_drawdown_percent: float | None = None
    max_open_positions: int | None = None
    enabled: bool | None = None


# Add endpoints:
@router.get("/risk", response_model=RiskSettingsResponse)
async def get_risk_settings():
    """Get current risk management settings."""
    config = risk_manager.config
    return RiskSettingsResponse(
        max_position_size=config.max_position_size,
        max_portfolio_risk_percent=config.max_portfolio_risk_percent,
        max_daily_loss=config.max_daily_loss,
        max_drawdown_percent=config.max_drawdown_percent,
        max_open_positions=config.max_open_positions,
        enabled=config.enabled,
        daily_pnl=risk_manager.get_daily_pnl(),
    )


@router.put("/risk", response_model=RiskSettingsResponse)
async def update_risk_settings(update: RiskSettingsUpdate):
    """Update risk management settings."""
    config = risk_manager.config

    if update.max_position_size is not None:
        config.max_position_size = update.max_position_size
    if update.max_portfolio_risk_percent is not None:
        config.max_portfolio_risk_percent = update.max_portfolio_risk_percent
    if update.max_daily_loss is not None:
        config.max_daily_loss = update.max_daily_loss
    if update.max_drawdown_percent is not None:
        config.max_drawdown_percent = update.max_drawdown_percent
    if update.max_open_positions is not None:
        config.max_open_positions = update.max_open_positions
    if update.enabled is not None:
        config.enabled = update.enabled

    # Save to file
    config.save_to_settings_file(SETTINGS_FILE)

    return await get_risk_settings()
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_bot_routes.py -v -k "risk"`
Expected: All 2 tests PASS

**Step 5: Commit**

```bash
cd /Users/armandfatalot/polymarket_trading_bot
git add backend/app/routes/bot.py backend/tests/test_bot_routes.py
git commit -m "feat(api): add risk settings endpoints"
```

---

## Task 11: Run Full Test Suite

**Files:**
- None (verification only)

**Step 1: Run all risk-related tests**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest tests/test_risk_manager.py tests/test_position_manager_risk.py -v`
Expected: All tests PASS

**Step 2: Run full test suite to check for regressions**

Run: `cd /Users/armandfatalot/polymarket_trading_bot/backend && python -m pytest -v`
Expected: All existing tests still PASS

**Step 3: Commit any fixes if needed**

If tests fail, fix issues and commit:
```bash
git add -A
git commit -m "fix: address test regressions"
```

---

## Summary

After completing all tasks, you will have:

1. **RiskConfig** - Configuration dataclass with defaults
2. **RiskManager** - Service with validation methods:
   - `validate_position_size()` - Check absolute and portfolio % limits
   - `validate_daily_loss()` - Track and check daily P&L
   - `validate_drawdown()` - Check max drawdown
   - `validate_open_positions()` - Check position count
   - `validate_trade()` - Combined pre-trade check
3. **Settings persistence** - Save/load from `data/settings.json`
4. **Integration** - Risk checks in `PositionManager.open_position()`
5. **API endpoints** - GET/PUT `/api/bot/risk`

Future enhancements (not in this plan):
- Portfolio equity tracking service
- Correlation checks between markets
- Per-source risk limits
- Risk dashboard in frontend
