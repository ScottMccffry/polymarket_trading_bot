"""Tests for Settings API routes."""
import json
import pytest
from pathlib import Path
from unittest.mock import patch

from app.routes.settings import SETTINGS_FILE, _mask_value


class TestSettingsHelpers:
    """Test helper functions."""

    def test_mask_value_empty(self):
        """Test masking empty string."""
        assert _mask_value("") == ""
        assert _mask_value(None) == ""

    def test_mask_value_short(self):
        """Test masking short string."""
        assert _mask_value("abc", show_chars=4) == "***"
        assert _mask_value("abcd", show_chars=4) == "****"

    def test_mask_value_long(self):
        """Test masking long string."""
        result = _mask_value("sk-1234567890abcdef", show_chars=4)
        assert result.endswith("cdef")
        assert result.startswith("*")


class TestSettingsRoutes:
    """Test settings API routes."""

    @pytest.mark.asyncio
    async def test_get_all_settings(self, client):
        """Test GET /api/settings returns all settings."""
        response = await client.get("/api/settings")
        assert response.status_code == 200
        data = response.json()

        assert "telegram" in data
        assert "llm" in data
        assert "qdrant" in data

        assert "api_id" in data["telegram"]
        assert "api_hash_masked" in data["telegram"]
        assert "phone" in data["telegram"]
        assert "monitored_groups" in data["telegram"]

        assert "openai_api_key_masked" in data["llm"]
        assert "model" in data["llm"]

        assert "url" in data["qdrant"]
        assert "api_key_masked" in data["qdrant"]
        assert "collection_name" in data["qdrant"]

    @pytest.mark.asyncio
    async def test_get_telegram_settings(self, client):
        """Test GET /api/settings/telegram."""
        response = await client.get("/api/settings/telegram")
        assert response.status_code == 200
        data = response.json()

        assert "api_id" in data
        assert "api_hash_masked" in data
        assert "phone" in data
        assert "monitored_groups" in data

    @pytest.mark.asyncio
    async def test_update_telegram_settings(self, client, tmp_path):
        """Test PUT /api/settings/telegram."""
        # Create temp settings file
        settings_file = tmp_path / "settings.json"

        with patch("app.routes.settings.SETTINGS_FILE", settings_file):
            response = await client.put(
                "/api/settings/telegram",
                json={
                    "api_id": 12345,
                    "phone": "+1234567890",
                    "monitored_groups": "group1,group2"
                }
            )
            assert response.status_code == 200
            data = response.json()

            assert data["api_id"] == 12345
            assert data["phone"] == "+1234567890"
            assert data["monitored_groups"] == "group1,group2"

    @pytest.mark.asyncio
    async def test_get_llm_settings(self, client):
        """Test GET /api/settings/llm."""
        response = await client.get("/api/settings/llm")
        assert response.status_code == 200
        data = response.json()

        assert "openai_api_key_masked" in data
        assert "model" in data

    @pytest.mark.asyncio
    async def test_update_llm_settings(self, client, tmp_path):
        """Test PUT /api/settings/llm."""
        settings_file = tmp_path / "settings.json"

        with patch("app.routes.settings.SETTINGS_FILE", settings_file):
            response = await client.put(
                "/api/settings/llm",
                json={
                    "model": "gpt-4o"
                }
            )
            assert response.status_code == 200
            data = response.json()

            assert data["model"] == "gpt-4o"

    @pytest.mark.asyncio
    async def test_get_qdrant_settings(self, client):
        """Test GET /api/settings/qdrant."""
        response = await client.get("/api/settings/qdrant")
        assert response.status_code == 200
        data = response.json()

        assert "url" in data
        assert "api_key_masked" in data
        assert "collection_name" in data

    @pytest.mark.asyncio
    async def test_update_qdrant_settings(self, client, tmp_path):
        """Test PUT /api/settings/qdrant."""
        settings_file = tmp_path / "settings.json"

        with patch("app.routes.settings.SETTINGS_FILE", settings_file):
            response = await client.put(
                "/api/settings/qdrant",
                json={
                    "url": "http://localhost:6333",
                    "collection_name": "test_collection"
                }
            )
            assert response.status_code == 200
            data = response.json()

            assert data["url"] == "http://localhost:6333"
            assert data["collection_name"] == "test_collection"
