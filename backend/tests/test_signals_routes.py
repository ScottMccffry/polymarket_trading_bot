"""Tests for signals API routes."""
import pytest
from datetime import datetime, UTC

from app.models.signal import Signal


class TestSignalsRoutes:
    """Test suite for signals endpoints."""

    @pytest.mark.asyncio
    async def test_get_signals_empty(self, client):
        """Test getting signals when none exist."""
        response = await client.get("/api/signals")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_signals(self, client, db_session):
        """Test getting all signals."""
        now = datetime.now(UTC).isoformat()
        signals = [
            Signal(
                signal_id=f"sig_{i}",
                source="telegram",
                message_text=f"Test signal {i}",
                market_question=f"Market {i}?",
                side="Yes",
                confidence=0.8,
                price_at_signal=0.55,
                created_at=now,
            )
            for i in range(3)
        ]
        for signal in signals:
            db_session.add(signal)
        await db_session.commit()

        response = await client.get("/api/signals")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_get_signals_with_pagination(self, client, db_session):
        """Test pagination of signals."""
        now = datetime.now(UTC).isoformat()
        for i in range(15):
            signal = Signal(
                signal_id=f"sig_{i}",
                source="telegram",
                created_at=now,
            )
            db_session.add(signal)
        await db_session.commit()

        # Get first page
        response = await client.get("/api/signals?limit=5&offset=0")
        assert response.status_code == 200
        assert len(response.json()) == 5

        # Get second page
        response = await client.get("/api/signals?limit=5&offset=5")
        assert response.status_code == 200
        assert len(response.json()) == 5

    @pytest.mark.asyncio
    async def test_get_recent_signals(self, client, db_session):
        """Test getting recent signals."""
        now = datetime.now(UTC).isoformat()
        for i in range(15):
            signal = Signal(
                signal_id=f"sig_{i}",
                source="telegram",
                created_at=now,
            )
            db_session.add(signal)
        await db_session.commit()

        response = await client.get("/api/signals/recent?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

    @pytest.mark.asyncio
    async def test_get_single_signal(self, client, db_session):
        """Test getting a specific signal by ID."""
        now = datetime.now(UTC).isoformat()
        signal = Signal(
            signal_id="test_signal_123",
            source="telegram",
            message_text="Test message",
            market_question="Will this test pass?",
            side="Yes",
            confidence=0.9,
            created_at=now,
        )
        db_session.add(signal)
        await db_session.commit()

        response = await client.get("/api/signals/test_signal_123")
        assert response.status_code == 200
        data = response.json()
        assert data["signal_id"] == "test_signal_123"
        assert data["market_question"] == "Will this test pass?"

    @pytest.mark.asyncio
    async def test_get_signal_not_found(self, client):
        """Test getting non-existent signal returns 404."""
        response = await client.get("/api/signals/nonexistent_signal")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_signal_fields(self, client, db_session):
        """Test that signal contains all expected fields."""
        now = datetime.now(UTC).isoformat()
        signal = Signal(
            signal_id="full_signal",
            source="telegram",
            message_text="Full test message",
            keywords="bitcoin,crypto,market",
            market_id="0xmarket123",
            token_id="token456",
            market_question="Complete market question?",
            side="No",
            confidence=0.75,
            price_at_signal=0.42,
            created_at=now,
        )
        db_session.add(signal)
        await db_session.commit()

        response = await client.get("/api/signals/full_signal")
        assert response.status_code == 200
        data = response.json()

        assert data["signal_id"] == "full_signal"
        assert data["source"] == "telegram"
        assert data["message_text"] == "Full test message"
        assert data["keywords"] == "bitcoin,crypto,market"
        assert data["market_id"] == "0xmarket123"
        assert data["token_id"] == "token456"
        assert data["side"] == "No"
        assert data["confidence"] == 0.75
        assert data["price_at_signal"] == 0.42
