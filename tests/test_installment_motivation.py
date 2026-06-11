import pytest

from src.report.installment_motivation import compute_motivation_stats


def test_buckets_counts_and_aov(base_con):
    stats = compute_motivation_stats(base_con)
    buckets = {b["bucket"]: b for b in stats["buckets"]}
    assert set(buckets) == {"1", "2-3", "4-6", "7+"}
    assert buckets["1"]["n_orders"] == 3  # o2, o3, o6
    assert buckets["1"]["aov"] == pytest.approx((50 + 30 + 60) / 3)
    assert buckets["2-3"]["n_orders"] == 1  # o5
    assert buckets["4-6"]["n_orders"] == 1  # o1 (max over rows = 4)
    assert buckets["4-6"]["aov"] == pytest.approx(120.0)  # 100 + 20
    assert buckets["7+"]["n_orders"] == 1  # o4


def test_share_multi_installment(base_con):
    stats = compute_motivation_stats(base_con)
    assert stats["share_multi_installment_orders"] == pytest.approx(0.5)  # 3 of 6
    assert stats["n_orders"] == 6


def test_credit_card_value_share(base_con):
    stats = compute_motivation_stats(base_con)
    assert stats["credit_card_value_share"] == pytest.approx(490.0 / 540.0)


def test_stats_are_deterministic(base_con):
    a = compute_motivation_stats(base_con)
    b = compute_motivation_stats(base_con)
    assert a == b
