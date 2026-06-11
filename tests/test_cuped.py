import numpy as np
import pytest

from src.experiment.cuped import cuped_adjust, cuped_theta


def test_theta_zero_when_uncorrelated():
    rng = np.random.default_rng(42)
    y = rng.normal(100, 10, 5000)
    x = rng.normal(50, 5, 5000)  # independent
    assert abs(cuped_theta(y, x)) < 0.1


def test_theta_recovers_known_slope():
    rng = np.random.default_rng(42)
    x = rng.normal(50, 5, 5000)
    y = 3.0 * x + rng.normal(0, 1, 5000)
    assert cuped_theta(y, x) == pytest.approx(3.0, abs=0.05)


def test_adjust_preserves_mean():
    rng = np.random.default_rng(42)
    x = rng.normal(50, 5, 5000)
    y = 3.0 * x + rng.normal(0, 1, 5000)
    theta = cuped_theta(y, x)
    y_adj = cuped_adjust(y, x, theta, float(x.mean()))
    assert y_adj.mean() == pytest.approx(y.mean(), rel=1e-9)


def test_adjust_reduces_variance():
    rng = np.random.default_rng(42)
    x = rng.normal(50, 5, 5000)
    y = 3.0 * x + rng.normal(0, 1, 5000)
    theta = cuped_theta(y, x)
    y_adj = cuped_adjust(y, x, theta, float(x.mean()))
    assert y_adj.var() < 0.2 * y.var()


def test_theta_zero_variance_x_raises():
    y = np.array([1.0, 2.0, 3.0])
    x = np.array([5.0, 5.0, 5.0])
    with pytest.raises(ValueError):
        cuped_theta(y, x)
