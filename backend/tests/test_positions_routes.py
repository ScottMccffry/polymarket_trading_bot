"""Tests for positions API routes."""
import pytest
from datetime import datetime, UTC

from app.models.position import Position


class TestPositionsRoutes:
    """Test suite for positions endpoints."""

    @pytest.mark.asyncio
    async def test_get_positions_empty(self, client):
        """Test getting positions when none exist."""
        response = await client.get("/api/positions")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_positions(self, client, db_session):
        """Test getting all positions."""
        now = datetime.now(UTC).isoformat()
        positions = [
            Position(
                signal_id=f"sig_{i}",
                strategy_id=1,
                strategy_name="Test Strategy",
                market_question=f"Market {i}?",
                side="Yes",
                entry_price=0.5 + i * 0.1,
                size=100.0,
                status="open",
                opened_at=now,
            )
            for i in range(3)
        ]
        for pos in positions:
            db_session.add(pos)
        await db_session.commit()

        response = await client.get("/api/positions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_get_positions_with_status_filter(self, client, db_session):
        """Test filtering positions by status."""
        now = datetime.now(UTC).isoformat()
        positions = [
            Position(
                signal_id=f"sig_{i}",
                status="open" if i < 2 else "closed",
                entry_price=0.5,
                size=100.0,
                opened_at=now,
                closed_at=now if i >= 2 else None,
            )
            for i in range(4)
        ]
        for pos in positions:
            db_session.add(pos)
        await db_session.commit()

        # Get open positions
        response = await client.get("/api/positions?status=open")
        assert response.status_code == 200
        assert len(response.json()) == 2

        # Get closed positions
        response = await client.get("/api/positions?status=closed")
        assert response.status_code == 200
        assert len(response.json()) == 2

    @pytest.mark.asyncio
    async def test_get_positions_with_strategy_filter(self, client, db_session):
        """Test filtering positions by strategy_id."""
        now = datetime.now(UTC).isoformat()
        positions = [
            Position(
                signal_id=f"sig_{i}",
                strategy_id=1 if i < 2 else 2,
                status="open",
                entry_price=0.5,
                size=100.0,
                opened_at=now,
            )
            for i in range(4)
        ]
        for pos in positions:
            db_session.add(pos)
        await db_session.commit()

        response = await client.get("/api/positions?strategy_id=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(p["strategy_id"] == 1 for p in data)

    @pytest.mark.asyncio
    async def test_get_open_positions(self, client, db_session):
        """Test getting only open positions."""
        now = datetime.now(UTC).isoformat()
        positions = [
            Position(
                signal_id=f"sig_{i}",
                status="open" if i < 3 else "closed",
                entry_price=0.5,
                size=100.0,
                opened_at=now,
            )
            for i in range(5)
        ]
        for pos in positions:
            db_session.add(pos)
        await db_session.commit()

        response = await client.get("/api/positions/open")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(p["status"] == "open" for p in data)

    @pytest.mark.asyncio
    async def test_get_closed_positions(self, client, db_session):
        """Test getting only closed positions."""
        now = datetime.now(UTC).isoformat()
        positions = [
            Position(
                signal_id=f"sig_{i}",
                status="closed" if i < 2 else "open",
                entry_price=0.5,
                exit_price=0.6 if i < 2 else None,
                size=100.0,
                opened_at=now,
                closed_at=now if i < 2 else None,
            )
            for i in range(5)
        ]
        for pos in positions:
            db_session.add(pos)
        await db_session.commit()

        response = await client.get("/api/positions/closed")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(p["status"] == "closed" for p in data)

    @pytest.mark.asyncio
    async def test_get_single_position(self, client, db_session):
        """Test getting a specific position by ID."""
        now = datetime.now(UTC).isoformat()
        position = Position(
            signal_id="test_signal",
            strategy_id=1,
            strategy_name="Test Strategy",
            market_question="Test market?",
            side="Yes",
            entry_price=0.55,
            current_price=0.60,
            size=100.0,
            status="open",
            unrealized_pnl=5.0,
            unrealized_pnl_percent=5.0,
            opened_at=now,
        )
        db_session.add(position)
        await db_session.commit()
        await db_session.refresh(position)

        response = await client.get(f"/api/positions/{position.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == position.id
        assert data["signal_id"] == "test_signal"
        assert data["entry_price"] == 0.55

    @pytest.mark.asyncio
    async def test_get_position_not_found(self, client):
        """Test getting non-existent position returns 404."""
        response = await client.get("/api/positions/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_positions_by_strategy(self, client, db_session):
        """Test getting positions for a specific strategy with overview."""
        now = datetime.now(UTC).isoformat()

        # Create open positions
        for i in range(3):
            position = Position(
                signal_id=f"sig_open_{i}",
                strategy_id=1,
                strategy_name="Test Strategy",
                entry_price=0.50,
                current_price=0.55,
                size=100.0,
                status="open",
                unrealized_pnl=10.0,
                unrealized_pnl_percent=10.0,
                opened_at=now,
            )
            db_session.add(position)

        # Create closed positions
        for i in range(2):
            position = Position(
                signal_id=f"sig_closed_{i}",
                strategy_id=1,
                strategy_name="Test Strategy",
                entry_price=0.50,
                exit_price=0.60,
                size=100.0,
                status="closed",
                realized_pnl=20.0,
                realized_pnl_percent=20.0,
                opened_at=now,
                closed_at=now,
            )
            db_session.add(position)

        await db_session.commit()

        response = await client.get("/api/positions/strategy/1")
        assert response.status_code == 200
        data = response.json()

        assert "overview" in data
        assert "open_positions" in data
        assert "closed_positions" in data

        overview = data["overview"]
        assert overview["strategy_id"] == 1
        assert overview["total_positions"] == 5
        assert overview["open_positions_count"] == 3
        assert overview["closed_positions_count"] == 2

    @pytest.mark.asyncio
    async def test_get_all_strategies_overview(self, client, db_session):
        """Test getting overview for all strategies."""
        now = datetime.now(UTC).isoformat()

        # Strategy 1 positions
        for i in range(2):
            position = Position(
                signal_id=f"sig_s1_{i}",
                strategy_id=1,
                strategy_name="Strategy 1",
                entry_price=0.50,
                size=100.0,
                status="open",
                opened_at=now,
            )
            db_session.add(position)

        # Strategy 2 positions
        for i in range(3):
            position = Position(
                signal_id=f"sig_s2_{i}",
                strategy_id=2,
                strategy_name="Strategy 2",
                entry_price=0.50,
                size=100.0,
                status="closed",
                realized_pnl=10.0,
                opened_at=now,
                closed_at=now,
            )
            db_session.add(position)

        await db_session.commit()

        response = await client.get("/api/positions/overview")
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 2
        strategy_ids = [s["strategy_id"] for s in data]
        assert 1 in strategy_ids
        assert 2 in strategy_ids

    @pytest.mark.asyncio
    async def test_position_pnl_calculations(self, client, db_session):
        """Test that P&L calculations are correct in response."""
        now = datetime.now(UTC).isoformat()

        # Profitable position
        profitable = Position(
            signal_id="profitable",
            entry_price=0.50,
            exit_price=0.60,
            size=100.0,
            status="closed",
            realized_pnl=20.0,
            realized_pnl_percent=20.0,
            opened_at=now,
            closed_at=now,
        )
        db_session.add(profitable)

        # Losing position
        losing = Position(
            signal_id="losing",
            entry_price=0.50,
            exit_price=0.40,
            size=100.0,
            status="closed",
            realized_pnl=-20.0,
            realized_pnl_percent=-20.0,
            opened_at=now,
            closed_at=now,
        )
        db_session.add(losing)

        await db_session.commit()

        response = await client.get("/api/positions/closed")
        assert response.status_code == 200
        data = response.json()

        profitable_pos = next(p for p in data if p["signal_id"] == "profitable")
        assert profitable_pos["realized_pnl"] == 20.0

        losing_pos = next(p for p in data if p["signal_id"] == "losing")
        assert losing_pos["realized_pnl"] == -20.0
