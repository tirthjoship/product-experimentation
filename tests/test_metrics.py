import pandas as pd
import pytest

from src.metrics.aov import aov_by_variant
from src.metrics.conversion import conversion_by_variant
from src.metrics.d7_repeat import d7_repeat_by_variant


def _pandas_conversion(frame: pd.DataFrame) -> dict[str, float]:
    delivered = frame["order_status"] == "delivered"
    return frame.assign(d=delivered).groupby("variant")["d"].mean().to_dict()


def test_conversion_matches_pandas(frame_con, frame):
    sql_result = conversion_by_variant(frame_con)
    pd_result = _pandas_conversion(frame)
    assert sql_result["control"] == pytest.approx(pd_result["control"])
    assert sql_result["treatment"] == pytest.approx(pd_result["treatment"])


def test_conversion_known_values(frame_con):
    r = conversion_by_variant(frame_con)
    assert r["control"] == pytest.approx(1 / 3)
    assert r["treatment"] == pytest.approx(1.0)


def _pandas_aov(frame: pd.DataFrame) -> dict[str, float]:
    return frame.groupby("variant")["order_value"].mean().to_dict()


def test_aov_matches_pandas(frame_con, frame):
    sql_result = aov_by_variant(frame_con)
    pd_result = _pandas_aov(frame)
    assert sql_result["control"] == pytest.approx(pd_result["control"])
    assert sql_result["treatment"] == pytest.approx(pd_result["treatment"])


def test_aov_known_values(frame_con):
    r = aov_by_variant(frame_con)
    assert r["control"] == pytest.approx(310 / 3)
    assert r["treatment"] == pytest.approx(230 / 3)


def test_d7_known_values(frame_con):
    r = d7_repeat_by_variant(frame_con)
    assert r["treatment"] == pytest.approx(0.5)
    assert r["control"] == pytest.approx(0.0)
