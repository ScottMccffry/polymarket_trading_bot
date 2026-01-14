"""Tests for strategies API routes."""
import pytest
from datetime import datetime, UTC

from app.models.strategy import (
    CustomStrategy,
    AdvancedStrategy,
    AdvancedStrategySource,
    AdvancedStrategyPartialExit,
)


class TestCustomStrategiesRoutes:
    """Test suite for custom strategies endpoints."""

    @pytest.mark.asyncio
    async def test_get_custom_strategies_empty(self, client):
        """Test getting custom strategies when none exist."""
        response = await client.get("/api/strategies/custom")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_create_custom_strategy(self, client):
        """Test creating a new custom strategy."""
        strategy_data = {
            "name": "Test Strategy",
            "description": "A test strategy",
            "take_profit": 15.0,
            "stop_loss": -10.0,
            "trailing_stop": 5.0,
        }

        response = await client.post("/api/strategies/custom", json=strategy_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Strategy"
        assert data["take_profit"] == 15.0
        assert data["stop_loss"] == -10.0

    @pytest.mark.asyncio
    async def test_create_duplicate_custom_strategy(self, client, db_session):
        """Test creating a strategy with duplicate name fails."""
        now = datetime.now(UTC).isoformat()
        strategy = CustomStrategy(
            name="Existing Strategy",
            take_profit=10.0,
            stop_loss=-5.0,
            created_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()

        strategy_data = {
            "name": "Existing Strategy",
            "take_profit": 15.0,
            "stop_loss": -10.0,
        }

        response = await client.post("/api/strategies/custom", json=strategy_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_custom_strategy(self, client, db_session):
        """Test getting a specific custom strategy."""
        now = datetime.now(UTC).isoformat()
        strategy = CustomStrategy(
            name="Test Strategy",
            description="Test description",
            take_profit=20.0,
            stop_loss=-15.0,
            trailing_stop=8.0,
            partial_exit_percent=50.0,
            partial_exit_threshold=10.0,
            created_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        response = await client.get(f"/api/strategies/custom/{strategy.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Strategy"
        assert data["take_profit"] == 20.0

    @pytest.mark.asyncio
    async def test_get_custom_strategy_not_found(self, client):
        """Test getting non-existent strategy returns 404."""
        response = await client.get("/api/strategies/custom/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_custom_strategy(self, client, db_session):
        """Test updating a custom strategy."""
        now = datetime.now(UTC).isoformat()
        strategy = CustomStrategy(
            name="Original Name",
            take_profit=10.0,
            stop_loss=-5.0,
            created_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        update_data = {
            "name": "Updated Name",
            "take_profit": 25.0,
        }

        response = await client.put(
            f"/api/strategies/custom/{strategy.id}",
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["take_profit"] == 25.0

    @pytest.mark.asyncio
    async def test_delete_custom_strategy(self, client, db_session):
        """Test deleting a custom strategy."""
        now = datetime.now(UTC).isoformat()
        strategy = CustomStrategy(
            name="To Delete",
            take_profit=10.0,
            stop_loss=-5.0,
            created_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        response = await client.delete(f"/api/strategies/custom/{strategy.id}")
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Verify deletion
        response = await client.get(f"/api/strategies/custom/{strategy.id}")
        assert response.status_code == 404


class TestAdvancedStrategiesRoutes:
    """Test suite for advanced strategies endpoints."""

    @pytest.mark.asyncio
    async def test_get_advanced_strategies_empty(self, client):
        """Test getting advanced strategies when none exist."""
        response = await client.get("/api/strategies/advanced")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_create_advanced_strategy(self, client):
        """Test creating a new advanced strategy."""
        strategy_data = {
            "name": "Advanced Test",
            "description": "An advanced strategy",
            "default_take_profit": 20.0,
            "default_stop_loss": -10.0,
            "default_trailing_stop": 5.0,
            "dynamic_trailing_enabled": True,
            "dynamic_trailing_base": 20.0,
            "dynamic_trailing_tight": 5.0,
            "dynamic_trailing_threshold": 50.0,
            "time_trailing_enabled": False,
            "enabled": True,
        }

        response = await client.post("/api/strategies/advanced", json=strategy_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Advanced Test"
        assert data["default_take_profit"] == 20.0
        assert data["dynamic_trailing_enabled"] is True

    @pytest.mark.asyncio
    async def test_create_advanced_strategy_with_sources(self, client):
        """Test creating advanced strategy with sources."""
        strategy_data = {
            "name": "Strategy With Sources",
            "default_take_profit": 15.0,
            "default_stop_loss": -10.0,
            "enabled": True,
            "sources": [
                {
                    "source": "telegram",
                    "take_profit": 20.0,
                    "stop_loss": -12.0,
                    "trailing_stop": 6.0,
                    "position_size_multiplier": 1.5,
                },
                {
                    "source": "rss",
                    "take_profit": 18.0,
                    "stop_loss": -10.0,
                    "position_size_multiplier": 1.0,
                }
            ]
        }

        response = await client.post("/api/strategies/advanced", json=strategy_data)
        assert response.status_code == 200
        data = response.json()
        assert len(data["sources"]) == 2
        assert data["sources"][0]["source"] == "telegram"

    @pytest.mark.asyncio
    async def test_create_advanced_strategy_with_partial_exits(self, client):
        """Test creating advanced strategy with partial exits."""
        strategy_data = {
            "name": "Strategy With Exits",
            "default_take_profit": 15.0,
            "default_stop_loss": -10.0,
            "enabled": True,
            "partial_exits": [
                {"exit_order": 1, "exit_percent": 50.0, "threshold": 10.0},
                {"exit_order": 2, "exit_percent": 30.0, "threshold": 20.0},
            ]
        }

        response = await client.post("/api/strategies/advanced", json=strategy_data)
        assert response.status_code == 200
        data = response.json()
        assert len(data["partial_exits"]) == 2
        assert data["partial_exits"][0]["exit_order"] == 1

    @pytest.mark.asyncio
    async def test_get_advanced_strategy(self, client, db_session):
        """Test getting a specific advanced strategy."""
        now = datetime.now(UTC).isoformat()
        strategy = AdvancedStrategy(
            name="Test Advanced",
            description="Test description",
            default_take_profit=20.0,
            default_stop_loss=-15.0,
            default_trailing_stop=8.0,
            dynamic_trailing_enabled=1,
            time_trailing_enabled=0,
            enabled=1,
            created_at=now,
            updated_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        response = await client.get(f"/api/strategies/advanced/{strategy.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Advanced"
        assert data["default_take_profit"] == 20.0

    @pytest.mark.asyncio
    async def test_update_advanced_strategy(self, client, db_session):
        """Test updating an advanced strategy."""
        now = datetime.now(UTC).isoformat()
        strategy = AdvancedStrategy(
            name="Original",
            default_take_profit=10.0,
            default_stop_loss=-5.0,
            enabled=1,
            created_at=now,
            updated_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        update_data = {
            "name": "Updated Advanced",
            "default_take_profit": 25.0,
        }

        response = await client.put(
            f"/api/strategies/advanced/{strategy.id}",
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Advanced"
        assert data["default_take_profit"] == 25.0

    @pytest.mark.asyncio
    async def test_toggle_advanced_strategy(self, client, db_session):
        """Test toggling strategy enabled status."""
        now = datetime.now(UTC).isoformat()
        strategy = AdvancedStrategy(
            name="Toggle Test",
            default_take_profit=10.0,
            default_stop_loss=-5.0,
            enabled=1,
            created_at=now,
            updated_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        # Toggle to disabled
        response = await client.patch(f"/api/strategies/advanced/{strategy.id}/toggle")
        assert response.status_code == 200
        assert response.json()["enabled"] is False

        # Toggle back to enabled
        response = await client.patch(f"/api/strategies/advanced/{strategy.id}/toggle")
        assert response.status_code == 200
        assert response.json()["enabled"] is True

    @pytest.mark.asyncio
    async def test_delete_advanced_strategy(self, client, db_session):
        """Test deleting an advanced strategy."""
        now = datetime.now(UTC).isoformat()
        strategy = AdvancedStrategy(
            name="To Delete",
            default_take_profit=10.0,
            default_stop_loss=-5.0,
            enabled=1,
            created_at=now,
            updated_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        response = await client.delete(f"/api/strategies/advanced/{strategy.id}")
        assert response.status_code == 200

        # Verify deletion
        response = await client.get(f"/api/strategies/advanced/{strategy.id}")
        assert response.status_code == 404


class TestStrategySourcesRoutes:
    """Test suite for strategy sources endpoints."""

    @pytest.mark.asyncio
    async def test_get_strategy_sources(self, client, db_session):
        """Test getting sources for a strategy."""
        now = datetime.now(UTC).isoformat()
        strategy = AdvancedStrategy(
            name="Test",
            default_take_profit=10.0,
            default_stop_loss=-5.0,
            enabled=1,
            created_at=now,
            updated_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        # Add sources
        source1 = AdvancedStrategySource(
            strategy_id=strategy.id,
            source="telegram",
            take_profit=15.0,
            stop_loss=-8.0,
        )
        source2 = AdvancedStrategySource(
            strategy_id=strategy.id,
            source="rss",
            take_profit=12.0,
            stop_loss=-6.0,
        )
        db_session.add_all([source1, source2])
        await db_session.commit()

        response = await client.get(f"/api/strategies/advanced/{strategy.id}/sources")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_add_strategy_source(self, client, db_session):
        """Test adding a source to a strategy."""
        now = datetime.now(UTC).isoformat()
        strategy = AdvancedStrategy(
            name="Test",
            default_take_profit=10.0,
            default_stop_loss=-5.0,
            enabled=1,
            created_at=now,
            updated_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        source_data = {
            "source": "telegram",
            "take_profit": 15.0,
            "stop_loss": -8.0,
            "trailing_stop": 5.0,
            "position_size_multiplier": 1.5,
        }

        response = await client.post(
            f"/api/strategies/advanced/{strategy.id}/sources",
            json=source_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "telegram"
        assert data["take_profit"] == 15.0

    @pytest.mark.asyncio
    async def test_delete_strategy_source(self, client, db_session):
        """Test deleting a source from a strategy."""
        now = datetime.now(UTC).isoformat()
        strategy = AdvancedStrategy(
            name="Test",
            default_take_profit=10.0,
            default_stop_loss=-5.0,
            enabled=1,
            created_at=now,
            updated_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        source = AdvancedStrategySource(
            strategy_id=strategy.id,
            source="telegram",
            take_profit=15.0,
            stop_loss=-8.0,
        )
        db_session.add(source)
        await db_session.commit()
        await db_session.refresh(source)

        response = await client.delete(
            f"/api/strategies/advanced/{strategy.id}/sources/{source.id}"
        )
        assert response.status_code == 200


class TestPartialExitsRoutes:
    """Test suite for partial exits endpoints."""

    @pytest.mark.asyncio
    async def test_get_partial_exits(self, client, db_session):
        """Test getting partial exits for a strategy."""
        now = datetime.now(UTC).isoformat()
        strategy = AdvancedStrategy(
            name="Test",
            default_take_profit=10.0,
            default_stop_loss=-5.0,
            enabled=1,
            created_at=now,
            updated_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        # Add partial exits
        exit1 = AdvancedStrategyPartialExit(
            strategy_id=strategy.id,
            exit_order=1,
            exit_percent=50.0,
            threshold=10.0,
        )
        exit2 = AdvancedStrategyPartialExit(
            strategy_id=strategy.id,
            exit_order=2,
            exit_percent=30.0,
            threshold=20.0,
        )
        db_session.add_all([exit1, exit2])
        await db_session.commit()

        response = await client.get(
            f"/api/strategies/advanced/{strategy.id}/partial-exits"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["exit_order"] == 1

    @pytest.mark.asyncio
    async def test_add_partial_exit(self, client, db_session):
        """Test adding a partial exit to a strategy."""
        now = datetime.now(UTC).isoformat()
        strategy = AdvancedStrategy(
            name="Test",
            default_take_profit=10.0,
            default_stop_loss=-5.0,
            enabled=1,
            created_at=now,
            updated_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        exit_data = {
            "exit_order": 1,
            "exit_percent": 50.0,
            "threshold": 10.0,
        }

        response = await client.post(
            f"/api/strategies/advanced/{strategy.id}/partial-exits",
            json=exit_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["exit_order"] == 1
        assert data["exit_percent"] == 50.0

    @pytest.mark.asyncio
    async def test_delete_partial_exit(self, client, db_session):
        """Test deleting a partial exit from a strategy."""
        now = datetime.now(UTC).isoformat()
        strategy = AdvancedStrategy(
            name="Test",
            default_take_profit=10.0,
            default_stop_loss=-5.0,
            enabled=1,
            created_at=now,
            updated_at=now,
        )
        db_session.add(strategy)
        await db_session.commit()
        await db_session.refresh(strategy)

        partial_exit = AdvancedStrategyPartialExit(
            strategy_id=strategy.id,
            exit_order=1,
            exit_percent=50.0,
            threshold=10.0,
        )
        db_session.add(partial_exit)
        await db_session.commit()
        await db_session.refresh(partial_exit)

        response = await client.delete(
            f"/api/strategies/advanced/{strategy.id}/partial-exits/{partial_exit.id}"
        )
        assert response.status_code == 200


class TestCombinedStrategiesRoutes:
    """Test suite for combined strategies endpoint."""

    @pytest.mark.asyncio
    async def test_get_all_strategies(self, client, db_session):
        """Test getting all strategies (custom and advanced)."""
        now = datetime.now(UTC).isoformat()

        # Add custom strategy
        custom = CustomStrategy(
            name="Custom Strategy",
            take_profit=10.0,
            stop_loss=-5.0,
            created_at=now,
        )
        db_session.add(custom)

        # Add advanced strategy
        advanced = AdvancedStrategy(
            name="Advanced Strategy",
            default_take_profit=15.0,
            default_stop_loss=-8.0,
            enabled=1,
            created_at=now,
            updated_at=now,
        )
        db_session.add(advanced)

        await db_session.commit()

        response = await client.get("/api/strategies")
        assert response.status_code == 200
        data = response.json()

        assert "custom" in data
        assert "advanced" in data
        assert len(data["custom"]) == 1
        assert len(data["advanced"]) == 1
