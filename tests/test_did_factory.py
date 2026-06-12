"""Sanity checks on the synthetic DiD panel factory used by estimator/gate tests."""

import pandas as pd

from tests.did_factory import make_synthetic_panel


def test_factory_shape_and_columns():
    panel = make_synthetic_panel()
    assert set(panel.columns) >= {
        "customer_state",
        "week",
        "n_orders",
        "delivery_days",
        "treated",
        "post",
        "log_orders",
    }
    assert panel["treated"].sum() > 0 and (~panel["treated"]).sum() > 0
    assert panel["post"].sum() > 0 and (~panel["post"]).sum() > 0


def test_factory_deterministic():
    a = make_synthetic_panel(seed=42)
    b = make_synthetic_panel(seed=42)
    pd.testing.assert_frame_equal(a, b)
