"""Unit tests for src/allocator.py — rebalancing engine."""

from __future__ import annotations

import pytest

from src.allocator import (
    AGGRESSIVE_GROWTH,
    age_based_allocation,
    calculate_rebalance,
    get_current_allocation,
    suggest_monthly_sip_allocation,
)


class TestAgeBasedAllocation:
    def test_young_investor_gets_high_equity(self):
        alloc = age_based_allocation(25)
        equity = alloc["equity_direct"] + alloc["mf_small_mid"] + alloc["mf_index_large"] + alloc["mf_international"]
        assert equity == pytest.approx(75.0)  # 100 - 25, capped at 90

    def test_old_investor_equity_floor_is_20(self):
        alloc = age_based_allocation(95)
        equity = alloc["equity_direct"] + alloc["mf_small_mid"] + alloc["mf_index_large"] + alloc["mf_international"]
        assert equity == pytest.approx(20.0)

    def test_equity_capped_at_90(self):
        alloc = age_based_allocation(5)
        equity = alloc["equity_direct"] + alloc["mf_small_mid"] + alloc["mf_index_large"] + alloc["mf_international"]
        assert equity == pytest.approx(90.0)

    def test_buckets_sum_to_100(self):
        alloc = age_based_allocation(40)
        assert sum(alloc.values()) == pytest.approx(100.0)


class TestGetCurrentAllocation:
    def test_buckets_percentages_by_asset_class(self, sample_portfolio):
        current = get_current_allocation(sample_portfolio)
        assert current["equity_direct"] == pytest.approx(15000 / 20500 * 100, abs=0.01)
        assert current["gold"] == pytest.approx(5500 / 20500 * 100, abs=0.01)

    def test_empty_portfolio_returns_empty_dict(self, empty_portfolio):
        assert get_current_allocation(empty_portfolio) == {}


class TestCalculateRebalance:
    def test_empty_portfolio_returns_no_actions(self, empty_portfolio):
        assert calculate_rebalance(empty_portfolio) == []

    def test_covers_all_buckets_in_target_and_current(self, sample_portfolio):
        actions = calculate_rebalance(sample_portfolio)
        bucket_names = {a.bucket for a in actions}
        assert bucket_names == set(AGGRESSIVE_GROWTH.keys()) | {"equity_direct", "gold"}

    def test_sorted_by_absolute_diff_descending(self, sample_portfolio):
        actions = calculate_rebalance(sample_portfolio)
        diffs = [abs(a.diff_percent) for a in actions]
        assert diffs == sorted(diffs, reverse=True)

    def test_action_label_matches_diff_sign(self, sample_portfolio):
        actions = calculate_rebalance(sample_portfolio)
        for a in actions:
            if abs(a.diff_percent) < 1.0:
                assert a.action == "ON TARGET"
            elif a.diff_percent > 0:
                assert a.action == "BUY MORE"
            else:
                assert a.action == "REDUCE"

    def test_custom_target_is_respected(self, sample_portfolio):
        custom_target = {"gold": 100}
        actions = calculate_rebalance(sample_portfolio, target=custom_target)
        gold_action = next(a for a in actions if a.bucket == "gold")
        assert gold_action.target_percent == pytest.approx(100.0)
        assert gold_action.action == "BUY MORE"


class TestSuggestMonthlySipAllocation:
    def test_splits_amount_by_target_percentages(self):
        result = suggest_monthly_sip_allocation(10000, target={"equity_direct": 60, "gold": 40})
        assert result["equity_direct"] == pytest.approx(6000)
        assert result["gold"] == pytest.approx(4000)

    def test_uses_aggressive_growth_by_default(self):
        result = suggest_monthly_sip_allocation(10000)
        assert set(result.keys()) == set(AGGRESSIVE_GROWTH.keys())
        assert sum(result.values()) == pytest.approx(10000, abs=10)
