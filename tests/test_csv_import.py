"""Tests for src/csv_import.py — Zerodha Kite Holdings CSV import.

Mocks the DB session/existing-symbols lookup and add_transaction() so this
never hits Postgres — same pattern as test_db_portfolio.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.csv_import import commit_import, parse_holdings_csv
from src.db_portfolio import PortfolioWriteError

SAMPLE_CSV = """\"Instrument\",\"Qty.\",\"Avg. cost\",\"LTP\",\"Invested\",\"Cur. val\",\"P&L\",\"Net chg.\",\"Day chg.\",\"\"
\"GOLDBEES\",500,105.49,119.14,52745,59570,6825,12.94,1.2,\"\"
\"RELIANCE\",50,1362.6,1288.6,68130,64430,-3700,-5.43,-1.16,\"\"
\"Quant ELSS Tax Saver Fund\",461.091,401.2,464.794,184990.63,214312.33,29321.7,15.85,0.21,\"\"
"""


def _mock_existing_symbols(monkeypatch, symbols: set[str]):
    monkeypatch.setattr("src.csv_import._existing_symbols", lambda: symbols)


class TestParseHoldingsCsv:
    def test_parses_all_rows(self, monkeypatch):
        _mock_existing_symbols(monkeypatch, set())
        result = parse_holdings_csv(SAMPLE_CSV)
        assert len(result.rows) == 3
        assert result.errors == []

    def test_flags_new_vs_existing_symbols(self, monkeypatch):
        _mock_existing_symbols(monkeypatch, {"RELIANCE"})
        result = parse_holdings_csv(SAMPLE_CSV)
        by_symbol = {r.symbol: r for r in result.rows}
        assert by_symbol["RELIANCE"].is_new_holding is False
        assert by_symbol["GOLDBEES"].is_new_holding is True
        assert set(result.new_symbols) == {"GOLDBEES", "QUANT ELSS TAX SAVER FUND"}

    def test_infers_gold_asset_class_for_bees_etf(self, monkeypatch):
        _mock_existing_symbols(monkeypatch, set())
        result = parse_holdings_csv(SAMPLE_CSV)
        goldbees = next(r for r in result.rows if r.symbol == "GOLDBEES")
        assert goldbees.inferred_asset_class == "gold"

    def test_infers_elss_for_tax_saver_fund(self, monkeypatch):
        _mock_existing_symbols(monkeypatch, set())
        result = parse_holdings_csv(SAMPLE_CSV)
        elss = next(r for r in result.rows if "ELSS" in r.symbol)
        assert elss.inferred_asset_class == "mf_elss"

    def test_existing_holding_has_no_inferred_fields(self, monkeypatch):
        _mock_existing_symbols(monkeypatch, {"RELIANCE"})
        result = parse_holdings_csv(SAMPLE_CSV)
        reliance = next(r for r in result.rows if r.symbol == "RELIANCE")
        assert reliance.inferred_name is None
        assert reliance.inferred_asset_class is None

    def test_current_price_comes_from_ltp(self, monkeypatch):
        _mock_existing_symbols(monkeypatch, set())
        result = parse_holdings_csv(SAMPLE_CSV)
        reliance = next(r for r in result.rows if r.symbol == "RELIANCE")
        assert reliance.current_price == pytest.approx(1288.6)
        assert reliance.avg_cost == pytest.approx(1362.6)

    def test_missing_required_columns_raises(self, monkeypatch):
        _mock_existing_symbols(monkeypatch, set())
        with pytest.raises(PortfolioWriteError, match="missing expected columns"):
            parse_holdings_csv('"Symbol","Amount"\n"RELIANCE",100\n')

    def test_unparseable_row_becomes_an_error_not_a_crash(self, monkeypatch):
        _mock_existing_symbols(monkeypatch, set())
        bad_csv = (
            '"Instrument","Qty.","Avg. cost","LTP","Invested","Cur. val","P&L","Net chg.","Day chg.",""\n'
            '"BADROW","not-a-number",100,100,0,0,0,0,0,""\n'
        )
        result = parse_holdings_csv(bad_csv)
        assert result.rows == []
        assert len(result.errors) == 1
        assert result.errors[0].symbol == "BADROW"

    def test_blank_instrument_rows_are_skipped(self, monkeypatch):
        _mock_existing_symbols(monkeypatch, set())
        csv_with_blank = (
            '"Instrument","Qty.","Avg. cost","LTP","Invested","Cur. val","P&L","Net chg.","Day chg.",""\n'
            '"","",,,,,,,,\n'
            '"RELIANCE",50,1362.6,1288.6,68130,64430,-3700,-5.43,-1.16,""\n'
        )
        result = parse_holdings_csv(csv_with_blank)
        assert len(result.rows) == 1


class TestCommitImport:
    def test_calls_add_transaction_for_each_row(self, monkeypatch):
        _mock_existing_symbols(monkeypatch, {"RELIANCE"})
        calls = []
        monkeypatch.setattr(
            "src.csv_import.add_transaction", lambda **kwargs: calls.append(kwargs)
        )

        result = commit_import(SAMPLE_CSV)

        assert len(calls) == 3
        reliance_call = next(c for c in calls if c["symbol"] == "RELIANCE")
        assert reliance_call["txn_type"] == "buy"
        assert reliance_call["quantity"] == pytest.approx(50)
        assert reliance_call["price"] == pytest.approx(1362.6)
        assert reliance_call["current_price"] == pytest.approx(1288.6)
        assert reliance_call["name"] is None  # existing holding, no inference needed

        goldbees_call = next(c for c in calls if c["symbol"] == "GOLDBEES")
        assert goldbees_call["name"] == "GOLDBEES"
        assert goldbees_call["asset_class"] == "gold"

        assert len(result.rows) == 3
        assert result.errors == []

    def test_row_level_write_error_is_collected_not_raised(self, monkeypatch):
        _mock_existing_symbols(monkeypatch, set())

        def fake_add_transaction(**kwargs):
            if kwargs["symbol"] == "RELIANCE":
                raise PortfolioWriteError("boom")

        monkeypatch.setattr("src.csv_import.add_transaction", fake_add_transaction)

        result = commit_import(SAMPLE_CSV)

        assert len(result.errors) == 1
        assert result.errors[0].symbol == "RELIANCE"
        assert "RELIANCE" not in {r.symbol for r in result.rows}
        assert len(result.rows) == 2

    def test_unexpected_db_error_on_one_row_does_not_abort_the_batch(self, monkeypatch):
        """Regression test: a StringDataRightTruncation (or any non-PortfolioWriteError)
        on one row used to propagate uncaught and kill the whole import mid-batch,
        silently leaving later rows unimported with no error reported for any of them."""
        _mock_existing_symbols(monkeypatch, set())
        calls = []

        def fake_add_transaction(**kwargs):
            calls.append(kwargs["symbol"])
            if kwargs["symbol"] == "GOLDBEES":
                raise RuntimeError("value too long for type character varying(30)")

        monkeypatch.setattr("src.csv_import.add_transaction", fake_add_transaction)

        result = commit_import(SAMPLE_CSV)

        # every row was attempted, not just the ones before the failure
        assert calls == ["GOLDBEES", "RELIANCE", "QUANT ELSS TAX SAVER FUND"]
        assert len(result.errors) == 1
        assert result.errors[0].symbol == "GOLDBEES"
        assert len(result.rows) == 2
