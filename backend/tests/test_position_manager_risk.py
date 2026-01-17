import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.trading.position_manager import PositionManager
from app.services.trading.risk_manager import RiskConfig, RiskManager


@pytest.mark.asyncio
async def test_open_position_blocked_by_risk():
    """Position should not open if risk check fails."""
    with patch("app.services.trading.position_manager.risk_manager") as mock_rm:
        mock_rm.validate_trade.return_value = MagicMock(
            can_trade=False,
            errors=["Position size exceeds max"]
        )

        pm = PositionManager()
        db = AsyncMock()

        # Mock db.execute to return empty results for get_open_positions
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result

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
            size=50.0,
        )

        assert result is None  # Position not opened
        db.add.assert_not_called()
