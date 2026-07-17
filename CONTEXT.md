# CONTEXT.md — Product Experimentation & Growth Metrics Platform

**Repo:** `product-experimentation-analytics`  
**Owner:** Tirth Joshi  
**Created:** 2026-05-30  
**Phase:** v1 complete — EDA → simulated RCT → installment narrative → DiD honest rejection → live dashboard on [Streamlit Cloud](https://experimentation-analytics.streamlit.app/).

**Future enhancements:** [`docs/FUTURE_ENHANCEMENTS.md`](docs/FUTURE_ENHANCEMENTS.md)

---

## 1. Mission

Build an **end-to-end product experimentation analytics system** that answers:

> *We shipped a change to the checkout experience. Did conversion improve beyond random noise—and should we roll out?*

This project demonstrates **SQL + statistics + product judgment** for experimentation analytics:
metric definitions, inference, power reasoning, and ship/no-ship decision writing.

It complements ML-heavy repos (supply chain, stock, healthcare) without duplicating them.

---

## 2. Locked decisions (do not revisit without user approval)

| Decision | Choice |
|----------|--------|
| **Dataset** | [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) |
| **Experiment type** | **Simulated RCT** — random assignment via hashed `customer_id` + fixed seed |
| **Primary metrics** | Conversion (order delivered), AOV, D7 repeat purchase rate |
| **Analysis** | Lift + 95% CI; power analysis documented |
| **SQL engine** | DuckDB (local); SQL files versioned in `sql/` |
| **Dashboard** | **Streamlit + Plotly, read-only over committed `reports/*.json`** (shipped; ADR 0010) |
| **Architecture** | Clean `src/` layout with thin domain layer — **not full hexagonal v1** (YAGNI) |
| **Honesty banner** | README must state experiment is simulated on historical data |

- **Business framing:** installment-expansion test (6x→10x interest-free cap).
  Free-shipping framing rejected for portfolio separation from supply-chain ML (ADR 0008).

---

## 3. Why Olist (and why not DataCo)

**Olist strengths:**
- ~100k real orders with timestamps, payments, customers, sellers
- Multi-table relational model → credible SQL joins, funnels, cohorts
- Stable enough for metric definitions and simulated A/B

**DataCo lesson (sibling repo [late-delivery-risk-prediction](https://github.com/tirthjoship/late-delivery-risk-prediction)):**
- Single categorical feature dominated outcome after leakage removal
- Demo dataset → weak business story
- **Gate:** Do not proceed to modeling/reporting until `reports/eda_gate.md` passes its GO checks

---

## 4. Dataset inventory

Download from Kaggle into `data/raw/olist/` (gitignore raw CSVs; commit schema docs only).

| File | Purpose | Key columns |
|------|---------|-------------|
| `olist_orders_dataset.csv` | Funnel spine | `order_id`, `customer_id`, `order_status`, `order_purchase_timestamp` |
| `olist_order_items_dataset.csv` | Line items | `order_id`, `product_id`, `price`, `freight_value` |
| `olist_order_payments_dataset.csv` | Payments | `order_id`, `payment_type`, `payment_value` |
| `olist_customers_dataset.csv` | Customer geo | `customer_id`, `customer_state`, `customer_city` |
| `olist_products_dataset.csv` | Product attrs | `product_id`, `product_category_name` |
| `olist_sellers_dataset.csv` | Seller geo | `seller_id`, `seller_state` |
| `product_category_name_translation.csv` | EN labels | category mapping |
| Optional: reviews, geolocation | v2 | defer unless time |

**Primary key graph:**
```
customers ──< orders ──< order_items
              │
              ├──< order_payments
              └── (order_status, timestamps)
```

---

## 5. Metric definitions (investigate in EDA, lock in `docs/METRICS.md`)

| Metric | Draft definition | Notes |
|--------|------------------|-------|
| **Conversion** | % orders with `order_status == 'delivered'` | Exclude canceled/unavailable explicitly |
| **AOV** | `sum(payment_value) / count(distinct order_id)` | Handle multi-payment rows |
| **D7 repeat** | Customer with ≥2 orders where 2nd within 7 days of 1st | Cohort logic — validate in EDA |
| **Funnel drop-off** | Created → paid → delivered | By month |
| **Time to deliver** | `delivered_timestamp - purchase_timestamp` | If columns reliable |

All metrics must have **SQL in `sql/metrics/`** + pytest that runs against a tiny fixture DB.

---

## 6. Experiment design (simulated RCT)

Olist has **no native A/B column**. v1 approach:

1. Filter cohort: e.g. orders in date range `[T0, T1]` with valid customer_id
2. Assign variant: `variant = hash(customer_id, seed=42) % 2` → `control` / `treatment`
3. **Proxy outcome:** For simulation, treatment effect can be:
   - **Option A (recommended):** Compare pre-defined segments as pseudo-treatment (document clearly), OR
   - **Option B:** Apply synthetic lift to treatment group for **methodology demo only** — must be labeled `SIMULATED_EFFECT` in code constants

**Natural experiment path (executed):** A gated DiD on the 2018 truckers'-strike shock was
pursued with pre-registered feasibility. The candidate failed on Olist sparsity (45.0% week-cell
density vs 80% threshold) and diverging pre-trends (Wald p=0.018). No estimate was computed;
rejection is the deliverable. See [ADR 0009](docs/adr/0009-gated-did-natural-experiment.md).

If pure hash assignment with no treatment effect: experiment shows **null result** — still valuable if power analysis and CIs are correct.

**Deliverable:** `reports/experiment_001.md` auto-generated with:
- Sample sizes per variant
- Metric table + lift + 95% CI
- p-value / bootstrap CI
- Plain-English recommendation: ship / don't ship / need more data

---

## 7. Phase 0 — EDA gate

```
notebooks/00_eda_gate.ipynb   → exploratory
reports/eda_gate.md           → GO/NO-GO verdict
docs/DATA_DICTIONARY.md       → column notes from EDA
```

### EDA checklist

- Row counts per table; date ranges
- Join integrity orders↔payments↔items (% orphans)
- Conversion rate overall and by month
- D7 repeat feasibility
- Covariate balance under hash assignment
- Draft DuckDB query for conversion — matches pandas?

### Go criteria

- ≥50k valid orders
- Conversion computable without >5% ambiguous status
- Metric SQL reproducible

---

## 8. Target architecture (post-EDA)

```
product-experimentation-analytics/
├── src/
│   ├── metrics/          # Python wrappers calling sql/
│   ├── experiment/       # assignment, analysis, power
│   ├── report/           # markdown report generator
│   └── io/               # duckdb loader, parquet cache
├── sql/
│   ├── metrics/          # conversion.sql, aov.sql, d7_repeat.sql
│   └── experiment/       # cohort.sql, variant_assignment.sql
├── tests/                # pytest on fixtures (tiny CSV/duckdb)
├── notebooks/            # EDA only; not production path
├── reports/              # generated outputs (commit md + json, not raw data)
├── dashboard/            # Streamlit app (reads committed reports/*.json)
├── docs/
│   ├── METRICS.md
│   └── EXPERIMENT_DESIGN.md
├── data/raw/             # gitignored
├── Makefile
├── pyproject.toml
└── README.md
```

**Dependencies (initial):** pandas, duckdb, scipy, matplotlib, pytest, streamlit

---

## 9. Testing & quality

- pytest on **small fixtures** in `tests/fixtures/` (100 rows max)
- Pin random seed `42` everywhere
- No full Olist load in unit tests — use DuckDB in-memory from fixtures
- Pre-commit: ruff, black (match sibling repos)

---

## 10. Success criteria (v1 complete)

| Criterion | Evidence |
|-----------|----------|
| EDA gate passed | `reports/eda_gate.md` says GO |
| ≥3 metrics defined in SQL | Files in `sql/metrics/` + tests pass |
| One experiment report | `reports/experiment_001.md` with CI |
| Power analysis | Section in report + calculator tab |
| Streamlit dashboard | Live on Streamlit Cloud |
| README | Problem, dataset, honest simulation disclaimer, how to reproduce |
| No invented metrics | All numbers from reproducible command |

---

## 11. Out of scope (v1)

- Real-time pipeline / Airflow (mention as v2 in README only)
- Causal inference beyond documented diff-in-diff or simulated RCT
- dbt / cloud warehouse (DuckDB local is enough)
- Replacing or merging with supply chain / stock repos

---

## 12. Sibling repos (patterns to copy)

| Pattern | Source repo |
|---------|-------------|
| Makefile + pytest rigor | [late-delivery-risk-prediction](https://github.com/tirthjoship/late-delivery-risk-prediction) |
| Report generation | [multi-modal-stock-recommender](https://github.com/tirthjoship/multi-modal-stock-recommender) |
| Locked decisions doc | `CONTEXT.md` §2 |

Do **not** claim Olist or simulated experiments as employer work.
