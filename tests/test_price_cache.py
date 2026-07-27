"""Unit tests for src/price_cache.py's NaN-close-price filtering.

Regression coverage for a real production incident: Yahoo Finance can
return NaN for a still-forming intraday bar (e.g. queried before the day's
close is final). That NaN, once cached, poisoned every downstream sum in
portfolio_value_series() (NaN + anything is NaN) and crashed JSON
serialization outright — "Out of range float values are not JSON
compliant: nan".
"""

from __future__ import annotations

import math

import pandas as pd
import pytest

from src.price_cache import _hist_to_frame


class TestHistToFrame:
    def test_drops_nan_close_rows(self):
        hist = pd.DataFrame(
            {"Close": [100.0, float("nan"), 102.0]},
            index=pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
        )
        df = _hist_to_frame(hist)
        assert len(df) == 2
        assert not df["Close"].isna().any()
        assert list(df["Close"]) == [100.0, 102.0]

    def test_keeps_all_rows_when_no_nan(self):
        hist = pd.DataFrame(
            {"Close": [100.0, 101.0, 102.0]},
            index=pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
        )
        df = _hist_to_frame(hist)
        assert len(df) == 3

    def test_all_nan_returns_empty_frame(self):
        hist = pd.DataFrame(
            {"Close": [float("nan"), float("nan")]},
            index=pd.to_datetime(["2026-01-01", "2026-01-02"]),
        )
        df = _hist_to_frame(hist)
        assert df.empty

    def test_result_columns_are_date_and_close(self):
        hist = pd.DataFrame({"Close": [100.0]}, index=pd.to_datetime(["2026-01-01"]))
        df = _hist_to_frame(hist)
        assert list(df.columns) == ["Date", "Close"]
