"""Unit tests for src/collectors/yahoo_collector.py's symbol mapping."""

from __future__ import annotations

from src.collectors.yahoo_collector import _yahoo_symbol


class TestYahooSymbol:
    def test_appends_ns_suffix_for_plain_equity(self):
        assert _yahoo_symbol("RELIANCE") == "RELIANCE.NS"

    def test_leaves_already_suffixed_symbol_alone(self):
        assert _yahoo_symbol("RELIANCE.BO") == "RELIANCE.BO"

    def test_index_ticker_is_not_suffixed(self):
        """Regression test: ^NSEI (NIFTY 50) is already the correct Yahoo
        Finance symbol — appending .NS produced the nonexistent ticker
        ^NSEI.NS, which 404'd (and took ~48s to fail) in production."""
        assert _yahoo_symbol("^NSEI") == "^NSEI"

    def test_other_index_ticker_is_not_suffixed(self):
        assert _yahoo_symbol("^BSESN") == "^BSESN"
