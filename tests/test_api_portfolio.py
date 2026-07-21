"""API integration tests for the portfolio routes.

These exercise the app against the real sample data in data/portfolio.yaml
and data/goals.yaml (load_portfolio() has no dependency-injection hook, so
route handlers always read that file). Assertions are kept structural
(status codes, keys, types) rather than pinned to specific sample values so
they don't break when the sample data is edited.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.app import app


@pytest.fixture
def unauthed_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def client(unauthed_client) -> TestClient:
    """Authenticated client — logs in with the dev default credentials from config.py."""
    resp = unauthed_client.post(
        "/auth/token",
        data={"username": "admin@portfolio.local", "password": "changeme123"},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    unauthed_client.headers["Authorization"] = f"Bearer {token}"
    return unauthed_client


class TestHealth:
    def test_health_ok(self, unauthed_client):
        resp = unauthed_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestAuthGate:
    def test_protected_route_rejects_no_token(self, unauthed_client):
        resp = unauthed_client.get("/api/portfolio/summary")
        assert resp.status_code == 401

    def test_protected_route_rejects_garbage_token(self, unauthed_client):
        unauthed_client.headers["Authorization"] = "Bearer not-a-real-token"
        resp = unauthed_client.get("/api/portfolio/summary")
        assert resp.status_code == 401

    def test_protected_route_accepts_valid_token(self, client):
        resp = client.get("/api/portfolio/summary")
        assert resp.status_code == 200


class TestPortfolioSummary:
    def test_returns_expected_keys(self, client):
        resp = client.get("/api/portfolio/summary")
        assert resp.status_code == 200
        body = resp.json()
        for key in ("total_invested", "total_value", "total_pnl", "total_pnl_pct", "cagr", "xirr", "holdings_count"):
            assert key in body

    def test_holdings_count_matches_positive_int(self, client):
        resp = client.get("/api/portfolio/summary")
        assert resp.json()["holdings_count"] >= 0


class TestPortfolioHoldings:
    def test_returns_list_of_records(self, client):
        resp = client.get("/api/portfolio/holdings")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        if body:
            assert "Symbol" in body[0]
            assert "XIRR %" in body[0]


class TestPortfolioAllocation:
    def test_returns_all_sections(self, client):
        resp = client.get("/api/portfolio/allocation")
        assert resp.status_code == 200
        body = resp.json()
        for key in ("by_asset_class", "by_sector", "concentration", "current_buckets"):
            assert key in body

    def test_concentration_has_top_holdings(self, client):
        resp = client.get("/api/portfolio/allocation")
        concentration = resp.json()["concentration"]
        assert "top_holdings" in concentration
        assert "top_percent" in concentration


class TestPortfolioRebalance:
    def test_returns_list_of_actions(self, client):
        resp = client.get("/api/portfolio/rebalance")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        if body:
            action = body[0]
            for key in ("bucket", "current_pct", "target_pct", "diff_pct", "action", "amount"):
                assert key in action
            assert action["action"] in ("BUY MORE", "REDUCE", "ON TARGET")


class TestPortfolioGoals:
    def test_returns_list_of_goal_progress(self, client):
        resp = client.get("/api/portfolio/goals")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        if body:
            goal = body[0]
            for key in ("name", "target_multiplier", "on_track", "completion_pct"):
                assert key in goal


class TestPortfolioGrowth:
    """Mocks portfolio_value_series so this never hits live Yahoo Finance or Postgres."""

    def test_returns_series_for_default_period(self, client, monkeypatch):
        fake_series = [{"date": "2026-01-01", "value": 1000.0}, {"date": "2026-01-02", "value": 1010.0}]
        monkeypatch.setattr("src.api.portfolio_routes.portfolio_value_series", lambda portfolio, period: fake_series)

        resp = client.get("/api/portfolio/growth")
        assert resp.status_code == 200
        body = resp.json()
        assert body["period"] == "1y"
        assert body["series"] == fake_series

    def test_rejects_invalid_period(self, client):
        resp = client.get("/api/portfolio/growth?period=3days")
        assert resp.status_code == 422

    def test_requires_auth(self, unauthed_client):
        resp = unauthed_client.get("/api/portfolio/growth")
        assert resp.status_code == 401


class TestCreateTransaction:
    """Mocks add_transaction so this never hits Postgres."""

    def test_valid_transaction_returns_ok(self, client, monkeypatch):
        monkeypatch.setattr("src.api.portfolio_routes.add_transaction", lambda **kwargs: None)
        resp = client.post(
            "/api/portfolio/transactions",
            json={"symbol": "RELIANCE", "type": "buy", "date": "2026-01-01", "quantity": 10, "price": 2500},
        )
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_write_error_returns_400(self, client, monkeypatch):
        from src.db_portfolio import PortfolioWriteError

        def raise_write_error(**kwargs):
            raise PortfolioWriteError("name and asset_class are required")

        monkeypatch.setattr("src.api.portfolio_routes.add_transaction", raise_write_error)
        resp = client.post(
            "/api/portfolio/transactions",
            json={"symbol": "NEWCO", "type": "buy", "date": "2026-01-01", "quantity": 10, "price": 100},
        )
        assert resp.status_code == 400

    def test_db_error_returns_503(self, client, monkeypatch):
        def raise_db_error(**kwargs):
            raise ConnectionError("db unreachable")

        monkeypatch.setattr("src.api.portfolio_routes.add_transaction", raise_db_error)
        resp = client.post(
            "/api/portfolio/transactions",
            json={"symbol": "RELIANCE", "type": "buy", "date": "2026-01-01", "quantity": 10, "price": 2500},
        )
        assert resp.status_code == 503

    def test_invalid_body_returns_422(self, client):
        resp = client.post("/api/portfolio/transactions", json={"symbol": "RELIANCE"})
        assert resp.status_code == 422

    def test_requires_auth(self, unauthed_client):
        resp = unauthed_client.post(
            "/api/portfolio/transactions",
            json={"symbol": "RELIANCE", "type": "buy", "date": "2026-01-01", "quantity": 10, "price": 2500},
        )
        assert resp.status_code == 401
