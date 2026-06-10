# Phase 1 Design — Metrics & Simulated Experiment

**Date:** 2026-06-09 · **Status:** approved, pre-implementation
**Gate:** Phase 0 EDA passed GO (`reports/eda_gate.md`). This spec defines the metric layer
and the simulated experiment. It becomes `docs/METRICS.md` + `docs/EXPERIMENT_DESIGN.md`
once implemented.

## Goal

Define three metrics in SQL and run one simulated A/B test on Olist that produces a
ship/no-ship recommendation with a 95% confidence interval. The experiment is simulated on
historical data — Olist has no native A/B column. Every number traces to a reproducible
command.

## Locked decisions (this spec)

| Decision | Choice |
|---|---|
| Experiment design | Simulated RCT with an injected, labeled treatment effect |
| Primary metric | AOV |
| Guardrail metric | Conversion (delivered rate) |
| Exploratory metric | D7 repeat purchase |
| AOV inference | Bootstrap 95% CI on the difference in means + Welch t-test |
| Conversion inference | Two-proportion z-test |
| Seed | 42 (assignment and bootstrap) |

## Metrics

Person identity is `customer_unique_id`. `customer_id` is per-order and must not key any
cohort or repeat logic. Each metric is defined in SQL first; Python wraps the SQL; a pytest
asserts the Python result equals the SQL result on the same fixture.

### AOV (primary)

Average order value. Sum `payment_value` to one row per `order_id` (multi-payment orders
exist), then take the mean across orders in a variant. Right-skewed: mean 160.99 BRL, median
105.29, max 13,664.08 (EDA). Defined over orders that have at least one payment row.

- SQL: `sql/metrics/aov.sql`

### Conversion (guardrail)

Share of cohort orders with `order_status == 'delivered'`. Cohort baseline is ~97% (a
fulfillment-success ceiling, not checkout conversion, labeled as such in the report). Used
as a guardrail: confirm treatment does not reduce delivery.

- SQL: `sql/metrics/conversion.sql`

### D7 repeat (exploratory)

Share of cohort persons whose second order falls within 7 days of their first. EDA measured
0.214% — too sparse for inference. Reported by variant with no statistical test.

- SQL: `sql/metrics/d7_repeat.sql`

## Experiment design

### Cohort

Orders with `order_purchase_timestamp` in `2017-01-01` to `2018-08-31`. This window drops the
sparse opening months and the right-censored tail (2018-09 and 2018-10 show 0% delivered
because those orders were still in flight at extract time; see `reports/eda_gate.md`).

- SQL: `sql/experiment/cohort.sql`

### Assignment

`variant = int(md5(f"{customer_unique_id}-{SEED}").hexdigest(), 16) % 2`, mapping to
`control` and `treatment`. Assignment is at the person level so a customer's orders never
split across variants. Assignment depends only on `customer_unique_id` and `SEED = 42`. It
never reads any outcome column.

- SQL: `sql/experiment/variant_assignment.sql` (mirrors the Python hash for parity tests)

### Injected effect

`SIMULATED_EFFECT = 0.05`: a multiplicative +5% applied to treatment orders' value, after
assignment. The constant is named `SIMULATED_EFFECT` so the leakage auditor and any reader
can see the effect is synthetic. 5% sits above the AOV minimum detectable effect (2.45% at
α=0.05, power=0.80, n/arm ≈ 49,575), so the experiment yields a detectable, significant
result and a clean ship decision. The value is a single constant and can be changed in one
place.

### A/A sanity check

Before injection, compute the AOV difference between the two raw variants and assert its 95%
bootstrap CI contains 0. This validates that the assignment itself introduces no effect (it
matches the near-null balance found in EDA: 96.924% vs 97.117% delivered). A failure here
means the assignment is broken, not that a treatment worked.

## Analysis

| Metric | Test | Output |
|---|---|---|
| AOV | bootstrap 95% CI on Δmean (10,000 resamples, seed 42) + Welch t-test | lift, CI, p-value |
| Conversion | two-proportion z-test | lift, 95% CI, guardrail flag |
| D7 repeat | none | rate per variant |

Power: document the MDE per metric at α=0.05, power=0.80, using the sample sizes realized in
the cohort. Reuse the formulas already run in the EDA notebook.

## Report

`reports/experiment_001.md`, generated (no hand-typed numbers):

- Simulation disclaimer at the top.
- Sample sizes per variant.
- Metric table: control, treatment, lift, 95% CI, p-value where applicable.
- Power / MDE section.
- Plain-English recommendation: ship, do not ship, or need more data, with the reason.

## Build architecture

Clean `src/` layout. Not hexagonal (locked in CONTEXT §2 as YAGNI for this project).

```
src/io/         duckdb loader, parquet cache
src/metrics/    conversion.py, aov.py, d7_repeat.py  (wrap sql/metrics/)
src/experiment/ assignment.py, effect.py, analysis.py, power.py
src/report/     experiment_report.py  (writes reports/experiment_001.md)
sql/metrics/    conversion.sql, aov.sql, d7_repeat.sql
sql/experiment/ cohort.sql, variant_assignment.sql
tests/          fixtures/ (<=100 rows), conftest.py (duckdb in-memory), test_*.py
```

Data flow: load → filter cohort → assign variant → inject `SIMULATED_EFFECT` →
compute metrics per variant → analysis → power → write report.

## Integrity and errors

The `leakage-auditor` agent runs before commit and checks: assignment reads only
`customer_unique_id` and the seed; the injected effect is labeled `SIMULATED_EFFECT`; the
seed is 42 in assignment and bootstrap; tests load fixtures only.

Raise an error, do not silently continue, when:

- the cohort filter returns zero rows
- a required column is missing from an input table
- variant sizes differ by more than a set tolerance (signals a hash or filter bug)

## Testing

Fixtures only, 100 rows maximum, DuckDB in-memory. No full Olist load in any test.

- Metric tests: Python output equals SQL output on the same fixture.
- Assignment tests: same `customer_unique_id` always gets the same variant; assignment ignores
  outcome columns; split-order check (all of a person's orders share a variant).
- Analysis tests: bootstrap CI is reproducible under seed 42; a known injected effect is
  recovered within its CI.
- Error tests: empty cohort, missing column, imbalance over tolerance each raise.

## Out of scope (this phase)

Streamlit dashboard (Phase 4), real-time pipeline, causal inference beyond the simulated RCT,
dbt or a cloud warehouse. Listed in README as possible later work only.

## Open parameters (changeable in one place)

| Parameter | Default | Where |
|---|---|---|
| `SEED` | 42 | constants |
| `SIMULATED_EFFECT` | 0.05 | constants |
| cohort window | 2017-01-01 .. 2018-08-31 | constants |
| bootstrap resamples | 10,000 | constants |
| significance level | 0.05 | constants |
