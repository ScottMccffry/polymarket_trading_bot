"""Tests for authentication API routes."""
import pytest

from app.models.user import User
from app.auth.security import get_password_hash


class TestAuthRoutes:
    """Test suite for authentication endpoints."""

    @pytest.mark.asyncio
    async def test_login_with_valid_credentials(self, client, db_session):
        """Test login with valid credentials."""
        # Create a test user
        hashed_password = get_password_hash("testpassword123")
        user = User(
            email="test@example.com",
            hashed_password=hashed_password,
        )
        db_session.add(user)
        await db_session.commit()

        # Attempt login
        response = await client.post(
            "/api/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_with_invalid_email(self, client):
        """Test login with non-existent email."""
        response = await client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_with_wrong_password(self, client, db_session):
        """Test login with incorrect password."""
        hashed_password = get_password_hash("correctpassword")
        user = User(
            email="test@example.com",
            hashed_password=hashed_password,
        )
        db_session.add(user)
        await db_session.commit()

        response = await client.post(
            "/api/auth/login",
            data={
                "username": "test@example.com",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_missing_credentials(self, client):
        """Test login with missing credentials."""
        response = await client.post("/api/auth/login", data={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_current_user(self, client, db_session):
        """Test getting current user with valid token."""
        # Create user and login
        hashed_password = get_password_hash("testpassword123")
        user = User(
            email="test@example.com",
            hashed_password=hashed_password,
        )
        db_session.add(user)
        await db_session.commit()

        # Login to get token
        login_response = await client.post(
            "/api/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpassword123"
            }
        )
        token = login_response.json()["access_token"]

        # Get current user
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["is_active"] == True

    @pytest.mark.asyncio
    async def test_get_current_user_without_token(self, client):
        """Test getting current user without authentication."""
        response = await client.get("/api/auth/me")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_with_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout(self, client):
        """Test logout endpoint."""
        response = await client.post("/api/auth/logout")
        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()
