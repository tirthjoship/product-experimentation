import pytest

from src.experiment.power import mde_mean, mde_proportion


def test_mde_proportion_reference():
    assert mde_proportion(0.5, 100) == pytest.approx(0.198102, abs=1e-5)


def test_mde_mean_reference():
    assert mde_mean(10.0, 100) == pytest.approx(3.96204, abs=1e-5)


def test_mde_shrinks_with_n():
    assert mde_mean(10.0, 1000) < mde_mean(10.0, 100)
