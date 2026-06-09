"""Minimum detectable effect at a target power. Documents experiment sensitivity."""

import numpy as np
from scipy import stats

from src.constants import ALPHA, POWER


def _z(alpha: float, power: float) -> tuple[float, float]:
    return float(stats.norm.ppf(1 - alpha / 2)), float(stats.norm.ppf(power))


def mde_proportion(
    p0: float, n: int, alpha: float = ALPHA, power: float = POWER
) -> float:
    za, zb = _z(alpha, power)
    return float((za + zb) * np.sqrt(2 * p0 * (1 - p0) / n))


def mde_mean(sd: float, n: int, alpha: float = ALPHA, power: float = POWER) -> float:
    za, zb = _z(alpha, power)
    return float((za + zb) * sd * np.sqrt(2 / n))
