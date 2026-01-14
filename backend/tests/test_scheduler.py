"""Tests for background scheduler."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.scheduler.jobs import (
    start_scheduler,
    stop_scheduler,
    get_scheduler_status,
    harvest_markets_job,
    scheduler,
)
from app.config import Settings


class TestScheduler:
    """Test suite for background scheduler."""

    def test_start_scheduler(self):
        """Test scheduler starts correctly."""
        settings = Settings(scheduler_enabled=True, market_harvest_interval_hours=12)

        sched = start_scheduler(settings)
        assert sched is not None
        assert sched.running

        # Verify jobs were added (harvest_markets and check_positions)
        jobs = sched.get_jobs()
        assert len(jobs) == 2
        job_ids = [job.id for job in jobs]
        assert "harvest_markets" in job_ids
        assert "check_positions" in job_ids

        stop_scheduler()

    def test_start_scheduler_disabled(self):
        """Test scheduler doesn't start when disabled."""
        settings = Settings(scheduler_enabled=False)

        sched = start_scheduler(settings)
        assert sched is None

    def test_stop_scheduler(self):
        """Test scheduler stops correctly."""
        settings = Settings(scheduler_enabled=True, market_harvest_interval_hours=12)

        start_scheduler(settings)
        stop_scheduler()

        status = get_scheduler_status()
        assert status["running"] is False

    def test_get_scheduler_status_not_running(self):
        """Test status when scheduler not running."""
        stop_scheduler()  # Ensure stopped
        status = get_scheduler_status()
        assert status["running"] is False
        assert status["jobs"] == []

    def test_get_scheduler_status_running(self):
        """Test status when scheduler is running."""
        settings = Settings(scheduler_enabled=True, market_harvest_interval_hours=6)

        start_scheduler(settings)
        status = get_scheduler_status()

        assert status["running"] is True
        assert len(status["jobs"]) == 2
        job_ids = [job["id"] for job in status["jobs"]]
        assert "harvest_markets" in job_ids
        assert "check_positions" in job_ids
        assert all(job["next_run"] is not None for job in status["jobs"])

        stop_scheduler()

    @patch("app.services.scheduler.jobs.MarketHarvester")
    @patch("app.services.scheduler.jobs.async_session")
    @pytest.mark.asyncio
    async def test_harvest_markets_job(self, mock_session, mock_harvester_class):
        """Test harvest job executes correctly."""
        # Setup mocks
        mock_db = AsyncMock()
        mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_harvester = MagicMock()
        mock_harvester.harvest = AsyncMock(return_value=150)
        mock_harvester_class.return_value = mock_harvester

        # Execute job
        count = await harvest_markets_job()

        assert count == 150
        mock_harvester.harvest.assert_called_once()

    @patch("app.services.scheduler.jobs.MarketHarvester")
    @patch("app.services.scheduler.jobs.async_session")
    @pytest.mark.asyncio
    async def test_harvest_markets_job_error(self, mock_session, mock_harvester_class):
        """Test harvest job handles errors."""
        mock_db = AsyncMock()
        mock_session.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session.return_value.__aexit__ = AsyncMock(return_value=None)

        mock_harvester = MagicMock()
        mock_harvester.harvest = AsyncMock(side_effect=Exception("API error"))
        mock_harvester_class.return_value = mock_harvester

        with pytest.raises(Exception, match="API error"):
            await harvest_markets_job()


class TestSchedulerEndpoints:
    """Test scheduler API endpoints."""

    @pytest.mark.asyncio
    async def test_scheduler_status_endpoint(self, client):
        """Test /scheduler/status endpoint."""
        response = await client.get("/scheduler/status")
        assert response.status_code == 200
        data = response.json()
        assert "running" in data
        assert "jobs" in data

    @patch("main.run_harvest_now")
    @pytest.mark.asyncio
    async def test_trigger_harvest_endpoint(self, mock_harvest, client):
        """Test /scheduler/harvest endpoint."""
        mock_harvest.return_value = 200

        response = await client.post("/scheduler/harvest")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["markets_harvested"] == 200

    @patch("main.run_harvest_now")
    @pytest.mark.asyncio
    async def test_trigger_harvest_endpoint_error(self, mock_harvest, client):
        """Test /scheduler/harvest endpoint handles errors."""
        mock_harvest.side_effect = Exception("Harvest failed")

        response = await client.post("/scheduler/harvest")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "Harvest failed" in data["message"]
