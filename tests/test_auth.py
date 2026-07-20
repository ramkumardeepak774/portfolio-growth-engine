"""Unit and API tests for src/auth.py and the /auth/token endpoint."""

from __future__ import annotations

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.app import app
from src.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    verify_password,
)
from src.config import get_settings

DEV_USERNAME = "admin@portfolio.local"
DEV_PASSWORD = "changeme123"


class TestPasswordHashing:
    def test_correct_password_verifies(self):
        settings = get_settings()
        assert verify_password(DEV_PASSWORD, settings.auth_password_hash) is True

    def test_wrong_password_fails(self):
        settings = get_settings()
        assert verify_password("wrong-password", settings.auth_password_hash) is False


class TestAuthenticateUser:
    def test_valid_credentials(self):
        assert authenticate_user(DEV_USERNAME, DEV_PASSWORD) is True

    def test_wrong_password(self):
        assert authenticate_user(DEV_USERNAME, "wrong-password") is False

    def test_wrong_username(self):
        assert authenticate_user("someone-else@example.com", DEV_PASSWORD) is False


class TestAccessToken:
    def test_create_and_decode(self):
        settings = get_settings()
        token = create_access_token(subject=DEV_USERNAME)
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == DEV_USERNAME
        assert "exp" in payload

    @pytest.mark.asyncio
    async def test_get_current_user_with_valid_token(self):
        token = create_access_token(subject=DEV_USERNAME)
        subject = await get_current_user(token=token)
        assert subject == DEV_USERNAME

    @pytest.mark.asyncio
    async def test_get_current_user_with_no_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=None)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_with_garbage_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="not-a-real-token")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_with_expired_token_raises_401(self):
        settings = get_settings()
        expired = jwt.encode(
            {"sub": DEV_USERNAME, "exp": 1},  # epoch second 1 — long expired
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=expired)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_with_wrong_secret_raises_401(self):
        token = jwt.encode({"sub": DEV_USERNAME, "exp": 9999999999}, "wrong-secret-that-is-long-enough", algorithm="HS256")
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token)
        assert exc_info.value.status_code == 401


class TestAuthTokenEndpoint:
    @pytest.fixture
    def client(self) -> TestClient:
        return TestClient(app)

    def test_valid_login_returns_token(self, client):
        resp = client.post("/auth/token", data={"username": DEV_USERNAME, "password": DEV_PASSWORD})
        assert resp.status_code == 200
        body = resp.json()
        assert body["token_type"] == "bearer"
        assert body["access_token"]

    def test_wrong_password_returns_401(self, client):
        resp = client.post("/auth/token", data={"username": DEV_USERNAME, "password": "wrong"})
        assert resp.status_code == 401

    def test_wrong_username_returns_401(self, client):
        resp = client.post("/auth/token", data={"username": "nobody@example.com", "password": DEV_PASSWORD})
        assert resp.status_code == 401

    def test_token_actually_authorizes_a_protected_route(self, client):
        login = client.post("/auth/token", data={"username": DEV_USERNAME, "password": DEV_PASSWORD})
        token = login.json()["access_token"]
        resp = client.get("/api/portfolio/summary", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
