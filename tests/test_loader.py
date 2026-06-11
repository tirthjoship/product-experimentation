import duckdb
import pandas as pd
import pytest

from src.exceptions import EmptyCohortError
from src.io.loader import build_experiment_frame


def test_frame_columns_and_size(base_con):
    df = build_experiment_frame(base_con)
    assert set(df.columns) == {
        "order_id",
        "customer_unique_id",
        "order_status",
        "order_value",
        "freight_value",
        "order_purchase_timestamp",
        "variant",
    }
    assert len(df) == 6


def test_order_value_aggregates_multi_payment(base_con):
    df = build_experiment_frame(base_con)
    assert df.loc[df["order_id"] == "o1", "order_value"].iloc[0] == pytest.approx(120.0)


def test_variants_match_seed_42(base_con):
    df = build_experiment_frame(base_con).set_index("order_id")
    assert df.loc["o1", "variant"] == "treatment"  # u1
    assert df.loc["o2", "variant"] == "control"  # u2


def test_person_orders_share_one_variant(base_con):
    df = build_experiment_frame(base_con)
    per_person = df.groupby("customer_unique_id")["variant"].nunique()
    assert (per_person == 1).all()


def test_empty_cohort_raises():
    con = duckdb.connect(":memory:")
    empty_orders = pd.DataFrame(
        columns=["order_id", "customer_id", "order_status", "order_purchase_timestamp"]
    )
    empty_customers = pd.DataFrame(
        columns=["customer_id", "customer_unique_id", "customer_state"]
    )
    empty_payments = pd.DataFrame(
        columns=["order_id", "payment_sequential", "payment_type", "payment_value"]
    )
    empty_items = pd.DataFrame(
        columns=[
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "price",
            "freight_value",
        ]
    )
    con.register("orders", empty_orders)
    con.register("customers", empty_customers)
    con.register("order_payments", empty_payments)
    con.register("order_items", empty_items)
    with pytest.raises(EmptyCohortError):
        build_experiment_frame(con)
    con.close()


def test_freight_value_sums_per_order(base_con):
    df = build_experiment_frame(base_con).set_index("order_id")
    assert df.loc["o1", "freight_value"] == pytest.approx(15.5)


def test_freight_value_zero_when_no_items(base_con):
    df = build_experiment_frame(base_con).set_index("order_id")
    assert df.loc["o6", "freight_value"] == pytest.approx(0.0)


def test_experiment_frame_row_order_is_deterministic(base_con):
    a = build_experiment_frame(base_con)["order_id"].tolist()
    b = build_experiment_frame(base_con)["order_id"].tolist()
    assert a == b
