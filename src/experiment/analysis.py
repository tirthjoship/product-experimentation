"""Inference: bootstrap CI for AOV, Welch t-test cross-check, two-proportion z for conversion."""

from collections.abc import Sequence

import numpy as np
import numpy.typing as npt
from scipy import stats

from src.constants import ALPHA, BOOTSTRAP_RESAMPLES, SEED


def bootstrap_ci_diff_means(
    control: Sequence[float],
    treatment: Sequence[float],
    n_resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = SEED,
    alpha: float = ALPHA,
) -> tuple[float, float]:
    """BCa bootstrap CI on (treatment mean - control mean).

    Bias-corrected-and-accelerated: corrects the percentile interval for median
    bias (z0) and skew-driven acceleration (a, via jackknife). Preferred over the
    percentile method because AOV is heavily right-skewed, where percentile
    intervals undercover. Deterministic given a fixed seed (the P3 contract).
    """
    c = np.asarray(control, dtype=float)
    t = np.asarray(treatment, dtype=float)

    def _stat(
        cs: npt.NDArray[np.float64],
        ts: npt.NDArray[np.float64],
        axis: int = -1,
    ) -> npt.NDArray[np.float64]:
        result: npt.NDArray[np.float64] = ts.mean(axis=axis) - cs.mean(axis=axis)
        return result

    res = stats.bootstrap(
        (c, t),
        _stat,
        n_resamples=n_resamples,
        confidence_level=1 - alpha,
        method="BCa",
        vectorized=True,
        paired=False,
        random_state=np.random.default_rng(seed),
    )
    return float(res.confidence_interval.low), float(res.confidence_interval.high)


def welch_ttest(
    control: Sequence[float], treatment: Sequence[float]
) -> tuple[float, float]:
    result = stats.ttest_ind(treatment, control, equal_var=False)
    return float(result.statistic), float(result.pvalue)


def quantile_lift(
    control: Sequence[float],
    treatment: Sequence[float],
    quantiles: Sequence[float],
) -> dict[float, float]:
    """Per-quantile treatment effect: q-th quantile(treatment) - q-th quantile(control).

    Shows *where* a mean lift lands. A mean AOV difference can be driven entirely by
    the tail (high-value 'whale' orders); the quantile view exposes that instead of
    hiding it behind the mean.
    """
    c = np.asarray(control, dtype=float)
    t = np.asarray(treatment, dtype=float)
    return {float(q): float(np.quantile(t, q) - np.quantile(c, q)) for q in quantiles}


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
