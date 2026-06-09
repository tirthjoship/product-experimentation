# Metric Definitions

**Source of truth:** SQL files in `sql/metrics/`. Python wrappers in `src/metrics/` run each
SQL against a registered DuckDB relation named `experiment_frame`. A pytest for each metric
asserts that the Python result equals a pandas computation on the same fixture (≤100 rows,
in-memory DuckDB — no full Olist in tests).

Numbers below come from `reports/eda_gate.md` (executed `notebooks/00_eda_gate.ipynb`).

---

## Person identity

`customer_unique_id` is the person key. `customer_id` is issued per order — one person may
have many `customer_id` values. Any cohort or repeat-purchase logic must key on
`customer_unique_id`. Using `customer_id` as a person key inflates unique-user counts and
breaks D7 logic (source: EDA gate, table inventory).

---

## AOV — average order value (primary metric)

**Definition:** Mean of per-order payment totals across orders in a variant.

**Why per-order total, not raw row sum:** The `order_payments` table has one row per payment
instrument on an order (e.g. credit card + voucher split). Summing `payment_value` at the
row level would count multi-payment orders multiple times. The SQL aggregates to one row per
`order_id` first, then takes the mean. This is the AOV multi-payment rule.

**SQL:** `sql/metrics/aov.sql`

**Python wrapper:** `src/metrics/aov.py` — `aov_by_variant(con) -> dict[str, float]`

**EDA numbers (full cohort, no effect injected):**
- Mean: 160.99 BRL, median: 105.29, std: 221.95, max: 13,664.08
- Right-skewed. Bootstrap CI is preferred over a bare t-test (see ADR-0006).

**Role in experiment:** Primary metric. The ship/no-ship recommendation is based on the AOV
bootstrap 95% CI on the treatment–control difference. A CI entirely above 0 → SHIP.

---

## Conversion — delivered rate (guardrail metric)

**Definition:** Share of cohort orders where `order_status == 'delivered'`.

**What this measures:** Fulfillment success, not checkout conversion. The Olist baseline is
97.02% (EDA gate, status distribution). That is a ceiling — the metric behaves like an
operations health signal, not a purchase-intent funnel step. Honest labeling is required
wherever this is reported.

**Why it is a guardrail, not primary:** The 97% baseline is statistically powerable (MDE =
0.30 pp at n ≈ 49.6k/arm, α=0.05, power=0.80), but the semantic is wrong. A 1 pp drop is
operationally significant. Conversion is watched to confirm treatment does not degrade
fulfillment, not to claim treatment improved checkout. See ADR-0005.

**SQL:** `sql/metrics/conversion.sql`

**Python wrapper:** `src/metrics/conversion.py` — `conversion_by_variant(con) -> dict[str, float]`

---

## D7 repeat purchase — 7-day repeat rate (exploratory metric)

**Definition:** Share of cohort persons whose second order falls within 7 days of their first.

**EDA finding:** 96,096 unique persons. "≥2 orders ever" = 3.12% (2,997 persons). "2nd order
within 7 days" = 0.214% (206 persons). Too sparse to power a statistical test. Reported by
variant with no test. See EDA gate, D7 repeat section.

**Why it is exploratory, not a test metric:** A 0.214% baseline would need tens of millions
of observations to detect a meaningful relative effect at standard power. The value of
reporting it is directional — if D7 is dramatically different between variants, that is a flag
worth investigating, not a basis for a ship decision.

**SQL:** `sql/metrics/d7_repeat.sql`

**Python wrapper:** `src/metrics/d7_repeat.py` — `d7_repeat_by_variant(con) -> dict[str, float]`

---

## SQL contract

All metric SQL runs against a relation registered as `experiment_frame` with these columns:

| Column | Type | Notes |
|---|---|---|
| `order_id` | str | unique per row |
| `customer_unique_id` | str | person key |
| `order_status` | str | e.g. `delivered`, `canceled` |
| `order_value` | float | sum of `payment_value` for this order |
| `order_purchase_timestamp` | datetime | cohort filter applied upstream |
| `variant` | str | `control` or `treatment` |

`build_experiment_frame` in `src/io/loader.py` produces this relation from the raw Olist
tables, filters the cohort window, and assigns variants.
