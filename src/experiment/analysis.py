"""Inference: bootstrap CI for AOV, Welch t-test cross-check, two-proportion z for conversion."""

from collections.abc import Sequence

import numpy as np
from scipy import stats

from src.constants import ALPHA, BOOTSTRAP_RESAMPLES, SEED


def bootstrap_ci_diff_means(
    control: Sequence[float],
    treatment: Sequence[float],
    n_resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = SEED,
    alpha: float = ALPHA,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    c = np.asarray(control, dtype=float)
    t = np.asarray(treatment, dtype=float)
    diffs = np.empty(n_resamples, dtype=float)
    for i in range(n_resamples):
        cs = rng.choice(c, size=c.size, replace=True)
        ts = rng.choice(t, size=t.size, replace=True)
        diffs[i] = ts.mean() - cs.mean()
    lo = float(np.percentile(diffs, 100 * alpha / 2))
    hi = float(np.percentile(diffs, 100 * (1 - alpha / 2)))
    return lo, hi


def welch_ttest(
    control: Sequence[float], treatment: Sequence[float]
) -> tuple[float, float]:
    result = stats.ttest_ind(treatment, control, equal_var=False)
    return float(result.statistic), float(result.pvalue)


def two_proportion_ztest(
    x_control: int,
    n_control: int,
    x_treatment: int,
    n_treatment: int,
    alpha: float = ALPHA,
) -> tuple[float, float, float, float]:
    p1 = x_control / n_control
    p2 = x_treatment / n_treatment
    pool = (x_control + x_treatment) / (n_control + n_treatment)
    se = np.sqrt(pool * (1 - pool) * (1 / n_control + 1 / n_treatment))
    z = (p2 - p1) / se
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    z_crit = stats.norm.ppf(1 - alpha / 2)
    se_diff = np.sqrt(p1 * (1 - p1) / n_control + p2 * (1 - p2) / n_treatment)
    lo = (p2 - p1) - z_crit * se_diff
    hi = (p2 - p1) + z_crit * se_diff
    return float(z), float(p), float(lo), float(hi)
