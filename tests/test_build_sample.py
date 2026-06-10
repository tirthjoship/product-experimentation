from pathlib import Path

import pandas as pd

from scripts.build_sample import build_sample

TABLES = ["orders", "order_items", "order_payments", "customers"]


def _make_raw(raw: Path) -> None:
    raw.mkdir(parents=True)
    pd.DataFrame(
        {
            "order_id": [f"o{i}" for i in range(20)],
            "customer_id": [f"c{i}" for i in range(20)],
            "order_status": ["delivered"] * 20,
            "order_purchase_timestamp": ["2017-05-01 10:00:00"] * 20,
        }
    ).to_csv(raw / "olist_orders_dataset.csv", index=False)
    pd.DataFrame(
        {
            "customer_id": [f"c{i}" for i in range(20)],
            "customer_unique_id": [f"u{i}" for i in range(20)],
            "customer_state": ["SP"] * 20,
        }
    ).to_csv(raw / "olist_customers_dataset.csv", index=False)
    pd.DataFrame(
        {
            "order_id": [f"o{i}" for i in range(20)],
            "payment_sequential": [1] * 20,
            "payment_type": ["credit_card"] * 20,
            "payment_value": [100.0] * 20,
        }
    ).to_csv(raw / "olist_order_payments_dataset.csv", index=False)
    pd.DataFrame(
        {
            "order_id": [f"o{i}" for i in range(20)],
            "product_id": [f"p{i}" for i in range(20)],
            "price": [50.0] * 20,
        }
    ).to_csv(raw / "olist_order_items_dataset.csv", index=False)


def test_sample_is_join_consistent(tmp_path: Path) -> None:
    raw, out = tmp_path / "raw", tmp_path / "sample"
    _make_raw(raw)
    build_sample(raw, out, n_orders=5, seed=42)
    orders = pd.read_csv(out / "olist_orders_dataset.csv")
    assert len(orders) == 5
    ids = set(orders["order_id"])
    cust_ids = set(orders["customer_id"])
    for tbl, key in [("order_payments", "order_id"), ("order_items", "order_id")]:
        child = pd.read_csv(out / f"olist_{tbl}_dataset.csv")
        assert set(child[key]).issubset(ids)
        assert set(child[key]) == ids  # every sampled order is represented
    customers = pd.read_csv(out / "olist_customers_dataset.csv")
    assert set(customers["customer_id"]) == cust_ids


def test_sample_is_deterministic(tmp_path: Path) -> None:
    raw, a, b = tmp_path / "raw", tmp_path / "a", tmp_path / "b"
    _make_raw(raw)
    build_sample(raw, a, n_orders=5, seed=42)
    build_sample(raw, b, n_orders=5, seed=42)
    left = pd.read_csv(a / "olist_orders_dataset.csv")["order_id"].tolist()
    right = pd.read_csv(b / "olist_orders_dataset.csv")["order_id"].tolist()
    assert left == right


def test_all_four_files_written(tmp_path: Path) -> None:
    raw, out = tmp_path / "raw", tmp_path / "sample"
    _make_raw(raw)
    build_sample(raw, out, n_orders=5, seed=42)
    for t in TABLES:
        assert (out / f"olist_{t}_dataset.csv").exists()
