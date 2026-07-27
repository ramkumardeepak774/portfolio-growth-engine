"""API tests for src/api/data_routes.py."""

from __future__ import annotations

import pandas as pd
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


class TestGetPrices:
    def test_returns_pascal_case_fields_matching_frontend_contract(self, client, monkeypatch):
        """Regression test: collect_prices() returns lowercase pandas columns
        (date/open/high/low/close/volume) — the frontend's PricePoint type
        expects PascalCase (Date/Open/High/Low/Close/Volume). The mismatch
        crashed the analytics page (`topPrices[i].Date.split(...)` on
        undefined) and silently NaN'd the dashboard's NIFTY benchmark
        comparison. The route must remap columns before returning JSON."""
        fake_df = pd.DataFrame(
            {
                "date": ["2026-01-01", "2026-01-02"],
                "open": [100.0, 101.0],
                "high": [102.0, 103.0],
                "low": [99.0, 100.0],
                "close": [101.0, 102.0],
                "volume": [1000, 1100],
                "dividends": [0.0, 0.0],
                "stock_splits": [0.0, 0.0],
            }
        )
        monkeypatch.setattr(
            "src.api.data_routes.YahooCollector.collect_prices",
            lambda self, symbol, period="1y": fake_df,
        )
        resp = client.get("/api/data/prices/RELIANCE")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 2
        for key in ("Date", "Open", "High", "Low", "Close", "Volume"):
            assert key in body[0]
        assert body[0]["Close"] == 101.0

    def test_404_when_no_data(self, client, monkeypatch):
        monkeypatch.setattr(
            "src.api.data_routes.YahooCollector.collect_prices",
            lambda self, symbol, period="1y": None,
        )
        resp = client.get("/api/data/prices/NOTREAL")
        assert resp.status_code == 404
