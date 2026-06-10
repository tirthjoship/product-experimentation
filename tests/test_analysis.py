import numpy as np
import pytest

from src.experiment.analysis import (
    bootstrap_ci_diff_means,
    two_proportion_ztest,
    welch_ttest,
)


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
