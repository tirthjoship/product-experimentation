# Data Dictionary — Olist (from Phase 0 EDA)

Column notes observed while executing `notebooks/00_eda_gate.ipynb`. Raw CSVs live in
`data/raw/olist/` (gitignored). Row counts and null rates are measured, not assumed.

## `olist_orders_dataset.csv` — 99,441 rows (funnel spine)

| Column | Type | Notes |
|---|---|---|
| `order_id` | str | PK. Unique. |
| `customer_id` | str | FK → customers. **Per-order**, not per-person. |
| `order_status` | str | 8 values; `delivered` = 97.02%. Terminal-fail: `canceled`, `unavailable`. In-flight: `shipped`, `invoiced`, `processing`, `created`, `approved`. |
| `order_purchase_timestamp` | datetime | 0 nulls. Span 2016-09-04 → 2018-10-17. Cohort anchor. |
| `order_approved_at` | datetime | some nulls (unapproved/canceled). |
| `order_delivered_carrier_date` | datetime | 1,783 nulls (1.79%). |
| `order_delivered_customer_date` | datetime | 2,965 nulls (2.98%) — matches non-delivered share. |
| `order_estimated_delivery_date` | datetime | 0 nulls. |

## `olist_order_items_dataset.csv` — 112,650 rows

| Column | Type | Notes |
|---|---|---|
| `order_id` | str | FK → orders. 1:N (multiple items per order). 0 orphans. |
| `order_item_id` | int | line index within order. |
| `product_id` | str | FK → products. |
| `seller_id` | str | FK → sellers. |
| `shipping_limit_date` | datetime | seller ship deadline. |
| `price` | float | item price (BRL). |
| `freight_value` | float | per-item freight (BRL). |

775 orders (0.78%) have **no** item row — mostly non-delivered; exclude from line-item metrics.

## `olist_order_payments_dataset.csv` — 103,886 rows

| Column | Type | Notes |
|---|---|---|
| `order_id` | str | FK → orders. N:1 (multi-payment orders exist). 0 orphans. |
| `payment_sequential` | int | payment index within order. |
| `payment_type` | str | credit_card / boleto / voucher / debit_card. |
| `payment_installments` | int | installment count. |
| `payment_value` | float | **AOV = SUM(payment_value) GROUP BY order_id.** mean 160.99, median 105.29, std 221.95, max 13,664.08, min 0.00 BRL. |

1 order has no payment row.

## `olist_customers_dataset.csv` — 99,441 rows

| Column | Type | Notes |
|---|---|---|
| `customer_id` | str | PK, **per-order** key. |
| `customer_unique_id` | str | **person identity** — use for repeat-purchase + variant assignment. 96,096 distinct. |
| `customer_zip_code_prefix` | int | geo join key. |
| `customer_city` | str | covariate. |
| `customer_state` | str | covariate (balance check). |

## Key relationships

```
customers (customer_unique_id = person)
   └─ customer_id (per order)
        └─< orders (order_id)
              ├─< order_items   (1:N)
              └─< order_payments (N:1; sum for AOV)
```

## Metric-defining gotchas (lock in `docs/METRICS.md`)

- **AOV** must aggregate `payment_value` to one row per `order_id` (multi-payment orders).
- **Conversion** = `order_status == 'delivered'`; explicitly exclude in-flight vs failed when
  framing — 97% ceiling means it behaves as fulfillment success.
- **Repeat / cohort** keys on `customer_unique_id`, never `customer_id`.
- **Cohort window** excludes sparse/right-censored boundary months (see `reports/eda_gate.md`).
