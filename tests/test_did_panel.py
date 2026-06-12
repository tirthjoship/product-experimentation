"""Panel builder: SQL aggregation correctness + code-enforced post-period blinding."""

from pathlib import Path

import duckdb
import pandas as pd
import pytest

from src.did.catalog import get_event
from src.did.panel import build_panel, require_go
from src.exceptions import BlindingError

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def did_con():
    con = duckdb.connect(":memory:")
    for name in ["customers", "orders"]:
        df = pd.read_csv(FIXTURES / f"did_{name}.csv")
        for col in df.columns:
            if col.endswith("timestamp"):
                df[col] = pd.to_datetime(df[col])
        # order_delivered_customer_date stays a string; the SQL TRY_CASTs it
        con.register(name, df)
    yield con
    con.close()


EVENT = get_event("truckers_strike_2018")


def test_blinded_panel_has_no_post_rows(did_con):
    panel = build_panel(did_con, EVENT)
    assert (panel["week"] < pd.Timestamp(EVENT.boundary_date)).all()
    assert not panel["post"].any()


def test_excluded_states_dropped(did_con):
    panel = build_panel(did_con, EVENT)
    assert "GO" not in set(panel["customer_state"])  # Center-West donut hole


def test_aggregates_correct(did_con):
    panel = build_panel(did_con, EVENT)
    pa = panel[panel["customer_state"] == "PA"].iloc[0]
    # do1 (10 days) + do2 (12 days), same ISO week
    assert pa["n_orders"] == 2
    assert pa["delivery_days"] == pytest.approx(11.0)
    assert bool(pa["treated"]) is True
    sp = panel[panel["customer_state"] == "SP"].iloc[0]
    # do4 delivered (3 days); do5 not delivered -> excluded from AVG, counted in n
    assert sp["n_orders"] == 2
    assert sp["delivery_days"] == pytest.approx(3.0)
    assert bool(sp["treated"]) is False


def test_log_orders_column(did_con):
    panel = build_panel(did_con, EVENT)
    import numpy as np

    assert panel["log_orders"].tolist() == pytest.approx(
        np.log1p(panel["n_orders"]).tolist()
    )


def test_unblind_without_verdict_raises(did_con, tmp_path):
    with pytest.raises(BlindingError):
        build_panel(
            did_con, EVENT, unblind_post=True, verdict_path=tmp_path / "missing.json"
        )


def test_unblind_with_fail_verdict_raises(did_con, tmp_path):
    p = tmp_path / "v.json"
    p.write_text('{"event": "truckers_strike_2018", "verdict": "FAIL"}')
    with pytest.raises(BlindingError):
        build_panel(did_con, EVENT, unblind_post=True, verdict_path=p)


def test_unblind_with_go_verdict_includes_post(did_con, tmp_path):
    import json as _json

    p = tmp_path / "v.json"
    p.write_text(
        _json.dumps(
            {
                "event": "truckers_strike_2018",
                "verdict": "GO",
                "conditions": {
                    "dated_boundary": {"passed": True},
                    "exogenous_assignment": {"passed": True},
                    "parallel_pretrends": {"passed": True},
                    "adequate_n": {"passed": True},
                },
            }
        )
    )
    panel = build_panel(did_con, EVENT, unblind_post=True, verdict_path=p)
    assert panel["post"].any()


def test_unblind_with_forged_go_missing_conditions_raises(did_con, tmp_path):
    # a "GO" string without genuine passing conditions must NOT unlock
    p = tmp_path / "v.json"
    p.write_text('{"event": "truckers_strike_2018", "verdict": "GO"}')
    with pytest.raises(BlindingError):
        build_panel(did_con, EVENT, unblind_post=True, verdict_path=p)


def test_unblind_with_go_and_failing_condition_raises(did_con, tmp_path):
    import json as _json

    p = tmp_path / "v.json"
    p.write_text(
        _json.dumps(
            {
                "event": "truckers_strike_2018",
                "verdict": "GO",
                "conditions": {"parallel_pretrends": {"passed": False}},
            }
        )
    )
    with pytest.raises(BlindingError):
        build_panel(did_con, EVENT, unblind_post=True, verdict_path=p)


def test_go_verdict_for_wrong_event_raises(did_con, tmp_path):
    p = tmp_path / "v.json"
    p.write_text('{"event": "black_friday_2017", "verdict": "GO"}')
    with pytest.raises(BlindingError):
        require_go(p, "truckers_strike_2018")
