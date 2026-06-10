"""Build a small, join-consistent, labeled Olist sample for CI/demo.

Anchors on a deterministic sample of orders, then filters dependent tables to the
referenced ids so every join in sql/experiment/cohort.sql stays intact.
Full data: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
"""

import sys
from pathlib import Path

import pandas as pd


def build_sample(
    raw_dir: Path, out_dir: Path, n_orders: int = 8000, seed: int = 42
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    orders = pd.read_csv(raw_dir / "olist_orders_dataset.csv")
    sample = orders.sample(n=min(n_orders, len(orders)), random_state=seed)
    order_ids = set(sample["order_id"])
    customer_ids = set(sample["customer_id"])

    customers = pd.read_csv(raw_dir / "olist_customers_dataset.csv")
    customers = customers[customers["customer_id"].isin(customer_ids)]

    payments = pd.read_csv(raw_dir / "olist_order_payments_dataset.csv")
    payments = payments[payments["order_id"].isin(order_ids)]

    items = pd.read_csv(raw_dir / "olist_order_items_dataset.csv")
    items = items[items["order_id"].isin(order_ids)]

    sample.to_csv(out_dir / "olist_orders_dataset.csv", index=False)
    customers.to_csv(out_dir / "olist_customers_dataset.csv", index=False)
    payments.to_csv(out_dir / "olist_order_payments_dataset.csv", index=False)
    items.to_csv(out_dir / "olist_order_items_dataset.csv", index=False)


if __name__ == "__main__":
    raw = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw/olist")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/sample")
    build_sample(raw, out)
    print(f"wrote sample to {out}")
