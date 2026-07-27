"""API tests for src/api/watchlist_routes.py.

Mocks add_to_watchlist/remove_from_watchlist/get_watchlist/fetch_current_price
so this never hits Postgres or yfinance.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from src.app import app


@pytest.fixture
def unauthed_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def client(unauthed_client) -> TestClient:
    resp = unauthed_client.post(
        "/auth/token",
        data={"username": "admin@portfolio.local", "password": "changeme123"},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    unauthed_client.headers["Authorization"] = f"Bearer {token}"
    return unauthed_client


class TestListWatchlist:
    def test_empty(self, client, monkeypatch):
        monkeypatch.setattr("src.api.watchlist_routes.get_watchlist", lambda: [])
        resp = client.get("/api/watchlist")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_populated_includes_live_price(self, client, monkeypatch):
        item = {
            "symbol": "RELIANCE",
            "name": "Reliance Industries",
            "asset_class": "equity_large_cap",
            "sector": "Energy",
            "target_price": 3000,
            "notes": None,
            "added_at": datetime(2026, 1, 1),
        }
        monkeypatch.setattr("src.api.watchlist_routes.get_watchlist", lambda: [item])
        monkeypatch.setattr("src.api.watchlist_routes.fetch_current_price", lambda symbol, asset_class: 2950.5)

        resp = client.get("/api/watchlist")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["symbol"] == "RELIANCE"
        assert body[0]["current_price"] == 2950.5
        assert body[0]["added_at"] == "2026-01-01T00:00:00"

    def test_failed_price_fetch_does_not_fail_the_request(self, client, monkeypatch):
        """fetch_current_price() returning None (its existing failure mode)
        must not 500 the whole watchlist — just that one item's price."""
        item = {
            "symbol": "DELISTED",
            "name": "Delisted Co",
            "asset_class": "equity_large_cap",
            "sector": None,
            "target_price": None,
            "notes": None,
            "added_at": datetime(2026, 1, 1),
        }
        monkeypatch.setattr("src.api.watchlist_routes.get_watchlist", lambda: [item])
        monkeypatch.setattr("src.api.watchlist_routes.fetch_current_price", lambda symbol, asset_class: None)

        resp = client.get("/api/watchlist")
        assert resp.status_code == 200
        assert resp.json()[0]["current_price"] is None

    def test_requires_auth(self, unauthed_client):
        resp = unauthed_client.get("/api/watchlist")
        assert resp.status_code == 401


class TestAddWatchlistItem:
    def test_valid_add_returns_ok(self, client, monkeypatch):
        monkeypatch.setattr("src.api.watchlist_routes.add_to_watchlist", lambda symbol, **kwargs: None)
        resp = client.post("/api/watchlist", json={"symbol": "RELIANCE", "target_price": 3000})
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_write_error_returns_400(self, client, monkeypatch):
        from src.db_portfolio import PortfolioWriteError

        def raise_write_error(symbol, **kwargs):
            raise PortfolioWriteError("name and asset_class are required")

        monkeypatch.setattr("src.api.watchlist_routes.add_to_watchlist", raise_write_error)
        resp = client.post("/api/watchlist", json={"symbol": "NEWCO"})
        assert resp.status_code == 400

    def test_db_error_returns_503(self, client, monkeypatch):
        def raise_db_error(symbol, **kwargs):
            raise ConnectionError("db unreachable")

        monkeypatch.setattr("src.api.watchlist_routes.add_to_watchlist", raise_db_error)
        resp = client.post("/api/watchlist", json={"symbol": "RELIANCE"})
        assert resp.status_code == 503

    def test_invalid_body_returns_422(self, client):
        resp = client.post("/api/watchlist", json={})
        assert resp.status_code == 422

    def test_requires_auth(self, unauthed_client):
        resp = unauthed_client.post("/api/watchlist", json={"symbol": "RELIANCE"})
        assert resp.status_code == 401


class TestDeleteWatchlistItem:
    def test_valid_delete_returns_ok(self, client, monkeypatch):
        monkeypatch.setattr("src.api.watchlist_routes.remove_from_watchlist", lambda symbol: None)
        resp = client.delete("/api/watchlist/RELIANCE")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_not_found_returns_404(self, client, monkeypatch):
        from src.db_watchlist import WatchlistItemNotFoundError

        def raise_not_found(symbol):
            raise WatchlistItemNotFoundError("not on watchlist")

        monkeypatch.setattr("src.api.watchlist_routes.remove_from_watchlist", raise_not_found)
        resp = client.delete("/api/watchlist/NOTREAL")
        assert resp.status_code == 404

    def test_requires_auth(self, unauthed_client):
        resp = unauthed_client.delete("/api/watchlist/RELIANCE")
        assert resp.status_code == 401
