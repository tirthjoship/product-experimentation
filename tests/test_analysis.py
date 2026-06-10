import numpy as np
import pytest

from src.constants import QUANTILES
from src.experiment.analysis import (
    bootstrap_ci_diff_means,
    quantile_lift,
    two_proportion_ztest,
    welch_ttest,
)


def test_bootstrap_bca_still_reproducible():
    a, b = [50.0, 200.0, 60.0, 90.0], [120.0, 30.0, 80.0, 140.0]
    first = bootstrap_ci_diff_means(a, b, n_resamples=2000, seed=42)
    second = bootstrap_ci_diff_means(a, b, n_resamples=2000, seed=42)
    assert first == second  # determinism preserved for the P3 contract


def test_bootstrap_bca_recovers_known_positive_effect():
    rng = np.random.default_rng(0)
    control = rng.normal(100, 5, 500)
    treatment = control + 10
    lo, hi = bootstrap_ci_diff_means(control, treatment, n_resamples=2000, seed=42)
    assert lo > 0
    assert lo <= 10 <= hi


def test_bootstrap_bca_skew_correction_shifts_interval():
    rng = np.random.default_rng(1)
    control = rng.lognormal(mean=3.0, sigma=1.0, size=400)
    treatment = rng.lognormal(mean=3.0, sigma=1.0, size=400) + 5.0
    lo, hi = bootstrap_ci_diff_means(control, treatment, n_resamples=3000, seed=42)
    assert hi > lo  # well-formed interval on skewed data


def test_bootstrap_is_reproducible():
    a, b = [50.0, 200.0, 60.0], [120.0, 30.0, 80.0]
    assert bootstrap_ci_diff_means(
        a, b, n_resamples=2000, seed=42
    ) == bootstrap_ci_diff_means(a, b, n_resamples=2000, seed=42)


def test_bootstrap_recovers_known_positive_effect():
    rng = np.random.default_rng(0)
    control = rng.normal(100, 5, 500)
    treatment = control + 10
    lo, hi = bootstrap_ci_diff_means(control, treatment, n_resamples=2000, seed=42)
    assert lo > 0  # effect is detected
    assert lo <= 10 <= hi  # true effect inside CI


def test_welch_matches_reference():
    t, p = welch_ttest([50.0, 200.0, 60.0], [120.0, 30.0, 80.0])
    assert t == pytest.approx(-0.485071, abs=1e-5)
    assert p == pytest.approx(0.660167, abs=1e-5)


def test_two_proportion_ztest_reference():
    z, p, lo, hi = two_proportion_ztest(2, 4, 4, 4)
    assert z == pytest.approx(1.632993, abs=1e-5)
    assert p == pytest.approx(0.10247, abs=1e-4)
    assert lo == pytest.approx(0.010009, abs=1e-4)
    assert hi == pytest.approx(0.989991, abs=1e-4)


def test_quantile_lift_constant_shift():
    control = [10.0, 20.0, 30.0, 40.0, 50.0]
    treatment = [15.0, 25.0, 35.0, 45.0, 55.0]  # +5 everywhere
    out = quantile_lift(control, treatment, QUANTILES)
    assert set(out) == set(QUANTILES)
    for q in QUANTILES:
        assert out[q] == pytest.approx(5.0, abs=1e-9)


def test_quantile_lift_detects_tail_only_effect():
    control = [10.0, 20.0, 30.0, 40.0, 1000.0]
    treatment = [10.0, 20.0, 30.0, 40.0, 1100.0]
    out = quantile_lift(control, treatment, (0.25, 0.90))
    assert out[0.25] == pytest.approx(0.0, abs=1e-9)
    assert out[0.90] > 0.0
