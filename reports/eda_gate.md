# EDA Gate — Olist Experimentation

**Date:** 2026-06-09 · **Phase:** 0 · **Source:** `notebooks/00_eda_gate.ipynb` (executed)
**Owner:** Tirth Joshi

> All numbers below are reproduced by executing `notebooks/00_eda_gate.ipynb` against
> `data/raw/olist/`. None are hand-entered. Re-run to verify.

---

## Verdict: ✅ **GO — with design caveats**

The dataset passes every structural gate. It is large, well-joined, and reproducible in
SQL. Two metric-design caveats (conversion ceiling, D7 sparsity) are documented below and
must be carried into `docs/METRICS.md` and `docs/EXPERIMENT_DESIGN.md` — they constrain the
design, they do **not** block the project.

---

## Go criteria

| Criterion (CONTEXT §7 / EDA sprint) | Threshold | Measured | Pass |
|---|---|---|---|
| Valid orders | ≥ 50,000 | **99,441** | ✅ |
| Ambiguous status | < 5% | 2.98% non-`delivered` | ✅ |
| Conversion computable | yes | delivered rate = **97.02%** | ✅ |
| Metric SQL reproducible | DuckDB == pandas | 97.0203% == 97.0203% | ✅ |
| FK join orphans | < 1% per group | max 0.78% (orders w/o item) | ✅ |

---

## Table inventory

| Table | Rows | Notes |
|---|---|---|
| orders | 99,441 | funnel spine; `order_purchase_timestamp` 0 nulls |
| order_items | 112,650 | 1:N with orders |
| order_payments | 103,886 | N:1 with orders (multi-payment rows summed for AOV) |
| customers | 99,441 | `customer_unique_id` = person; `customer_id` = per-order |

**Date span:** 2016-09-04 → 2018-10-17 (25 calendar months).

## Join integrity

| Check | Count | % |
|---|---|---|
| items with no parent order | 0 | 0.00% |
| payments with no parent order | 0 | 0.00% |
| orders with no customer | 0 | 0.00% |
| orders with no payment | 1 | 0.00% |
| orders with no item | 775 | 0.78% |

All orphan groups < 1%. The 775 item-less orders are predominantly non-`delivered` (canceled/
unavailable) — exclude from line-item metrics, keep for status funnel.

## Status distribution

`delivered` 97.02% · `shipped` 1.11% · `canceled` 0.63% · `unavailable` 0.61% ·
`invoiced` 0.32% · `processing` 0.30% · `created`/`approved` ~0%.

## Conversion by month — censoring warning

Boundary months are unusable: **2016-09** has 4 orders, **2016-12** has 1; the tail months
**2018-09 (16 orders)** and **2018-10 (4 orders)** show **0% delivered** because those orders
were still in flight at data-extract time — right-censoring, not failure. The stable core
runs roughly **2017-01 → 2018-08** (e.g. 2018-07 = 97.89%, 2018-08 = 97.53%).
➡️ **The experiment cohort must filter to the stable window.**

## AOV

Per-order `payment_value`: mean **160.99 BRL**, median 105.29, std 221.95, max 13,664.08,
min 0.00. Right-skewed — log-transform or trim for parametric tests; bootstrap CI preferred.

## D7 repeat purchase

96,096 unique persons. ≥2 orders **ever**: 2,997 (3.12%). 2nd order **within 7 days**:
**206 (0.214%)**. ➡️ Too sparse to be a primary metric — demote to exploratory.

## Simulated assignment (seed = 42)

Hash `customer_unique_id` → variant 0: 49,866 / variant 1: 49,575. Delivered rate
96.924% vs 97.117% — balanced, near-null as expected with no treatment effect. Confirms a
labeled `SIMULATED_EFFECT` is required to demonstrate detectable lift.

## Power / MDE (α=0.05, power=0.80, n/arm ≈ 49,575)

| Metric | Baseline | MDE (abs) | MDE (rel) |
|---|---|---|---|
| Conversion (delivered) | 97.02% | 0.303 pp | 0.31% |
| AOV | 160.99 BRL | 3.95 BRL | 2.45% |

---

## Decisions carried into design

1. **Primary metric = AOV** (continuous, sensitive). Conversion = secondary, framed as
   *fulfillment success*, not checkout conversion (97% ceiling — honest labeling required).
2. **D7 repeat = exploratory only** (0.214% within-7d).
3. **Cohort window** = stable months only (~2017-01 → 2018-08); exclude boundary months.
4. **Assignment** by hashed `customer_unique_id`, seed 42; treatment effect synthetic and
   labeled `SIMULATED_EFFECT`.
5. Every metric gets SQL in `sql/metrics/` with a pandas-parity test on a ≤100-row fixture.

## Next phase (gate = GO → open Phase 1)

Per `docs/SKILL_ROUTING.md`: `brainstorming` → `writing-plans` to lock `docs/METRICS.md`
and `docs/EXPERIMENT_DESIGN.md`, then scaffold `src/` + `sql/`.
