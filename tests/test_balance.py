import pandas as pd
import pytest

from src.exceptions import ImbalanceError
from src.experiment.balance import check_balance, check_metric_balance


def _metric_frame(ctrl_vals, treat_vals):
    return pd.DataFrame(
        {
            "variant": ["control"] * len(ctrl_vals) + ["treatment"] * len(treat_vals),
            "order_value": list(ctrl_vals) + list(treat_vals),
        }
    )


def test_balanced_frame_passes(frame):
    check_balance(frame)  # 3 vs 3, no raise


def test_imbalanced_frame_raises():
    df = pd.DataFrame({"variant": ["control"] * 10 + ["treatment"] * 2})
    with pytest.raises(ImbalanceError):
        check_balance(df)


def test_metric_balance_passes_small_gap():
    f = _metric_frame([100.0, 102.0], [101.0, 103.0])  # ~1% gap
    gap = check_metric_balance(f, "order_value")
    assert 0.0 <= gap < 0.05


def test_metric_balance_raises_large_gap():
    f = _metric_frame([100.0, 100.0], [120.0, 120.0])  # 20% gap
    with pytest.raises(ImbalanceError):
        check_metric_balance(f, "order_value")


def test_check_balance_empty_frame_raises():
    df = pd.DataFrame({"variant": pd.Series([], dtype=str)})
    with pytest.raises(ImbalanceError):
        check_balance(df)


def test_metric_balance_zero_control_mean_raises():
    f = _metric_frame([0.0, 0.0], [10.0, 10.0])
    with pytest.raises(ImbalanceError):
        check_metric_balance(f, "order_value")
