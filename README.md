# Product Experimentation & Growth Metrics Platform

**Status:** Phase 1 complete (metrics + simulated experiment) · Phase F foundation complete
(committed result JSON + join-consistent data sample) · Phase 2 (dashboard) next
**Portfolio:** Project 4 of 5 · Balanced DA/DS strategy

> **Simulated RCT on historical Olist cohorts.** Variants are assigned by hashed
> `customer_unique_id` (seed 42) on historical data — Olist has no native A/B column.
> The treatment effect is a synthetic constant (`SIMULATED_EFFECT = 0.05`, defined once in
> `src/constants.py`) injected after assignment to demonstrate the inference pipeline.
> This is not a real product lift. Seed 42 is documented and pinned.

End-to-end **product analytics** for a classic hiring question: *Did a product change actually improve conversion, or was it noise?* Built on the [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) dataset — SQL metric definitions, simulated experiment analysis, confidence intervals, and a ship/no-ship recommendation.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Phase](https://img.shields.io/badge/phase-1%20complete-brightgreen)](./reports/experiment_001.md)
[![Tests](https://img.shields.io/badge/tests-82%20passing-brightgreen)](./tests/)
[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)](./tests/)
[![Portfolio](https://img.shields.io/badge/portfolio-4%20of%205-purple)](../README.md)

> **Disclaimer:** Experiments in this repo are **simulated** on historical Olist data (hashed customer assignment or documented natural experiment). This is not employer A/B test data and does not claim causal lift from a real product rollout.

---

## The business problem

A product team ships a checkout or onboarding change. Leadership asks:

1. Did **conversion** move beyond random noise?
2. Are **AOV** and **repeat purchase** consistent with the story?
3. Was the test **powered** enough to detect a meaningful effect?
4. Should we **ship**, **hold**, or **collect more data**?

Most ML portfolio projects prove modeling depth. This one proves **metric definitions + statistics + product judgment** — the skill cluster that rose fastest in 2026 DS postings (experimentation, causal framing, SQL case studies).

---

## Results — Experiment 001 (simulated)

**Framing:** installment-expansion test — would raising the interest-free installment cap
(6x → 10x) grow basket sizes? Motivated by real Olist payment behavior
([motivation stats](reports/installment_motivation.md)); effect itself is simulated and labeled.
**→ Read the [PM decision memo](reports/experiment_001_readout.md)** — the headline artifact:
verdict, guardrail readout, caveats, rollout + monitoring plan.

> Full report: [`reports/experiment_001.md`](./reports/experiment_001.md). Numbers below are
> emitted by `make experiment` on the real Olist cohort (99,092 delivered-eligible orders);
> nothing here is hand-entered. The lift is a **labeled synthetic effect** (`SIMULATED_EFFECT = 0.05`),
> not a real product rollout.

| Metric | Control | Treatment | Lift | 95% CI | p | Verdict |
|--------|---------|-----------|------|--------|---|---------|
| **AOV** (primary) | 159.88 | 170.03 | **+10.15** | (7.35, 13.00) | <0.0001 | CI excludes 0 → **SHIP** |
| **Conversion** (guardrail) | 0.9700 | 0.9718 | +0.0018 | (−0.0003, 0.0039) | 0.087 | CI spans 0 → no harm |
| **D7 repeat** (exploratory) | 0.0088 | 0.0084 | — | — | — | descriptive only |

**Recommendation: SHIP** — the AOV 95% bootstrap CI lies entirely above zero, while the
conversion guardrail shows no significant movement (the synthetic effect was injected on
`order_value` only, so the guardrail *should* stay flat — and it does, validating no leakage).

**Reading the numbers (the narrative that matters in interviews):**

1. **Why is observed lift +6.35% when the injected effect is 5%?** Random hash assignment left
   the treatment arm with a slightly higher pre-effect baseline (~161.9 vs 159.9). The ×1.05
   multiplier adds ~8.1; the ~2.0 baseline gap is sampling noise. Decompose before you trust a lift.
2. **The guardrail is the integrity check.** Effect touches only `order_value`; `order_status`
   is untouched, so conversion staying flat (p=0.087) is *expected* and confirms the pipeline
   doesn't leak the treatment signal into other metrics.
3. **Powered enough?** AOV MDE ≈ 4.32 at n≈49k/arm — the detected +10.15 is well above the
   minimum detectable effect, so the SHIP call isn't an underpowered fluke.
4. **Assignment balance:** 49,694 control / 49,398 treatment (0.6% gap, within the 5% tolerance
   guard). A near-50/50 split confirms hash assignment introduces no structural bias.
5. **Reproducibility finding (Phase F).** The bootstrap CI was initially *non-deterministic* —
   the cohort SQL had no `ORDER BY`, so DuckDB returned rows in arbitrary order and the
   positional bootstrap resampled differently each run (CI wandered at the 2nd decimal). Fixed by
   pinning frame order (`ORDER BY order_id`); the CI `(7.35, 13.00)` is now byte-stable across
   runs and guarded by a determinism test. A committed `reports/experiment_001.json` snapshot
   makes the result a regression-testable contract — not a number you have to trust.

---

## Who this is for (hiring signal)

| Market | Why this repo matters |
|--------|----------------------|
| **Seattle / San Francisco** | Product DS interviews center on A/B design, SQL, and judgment under uncertainty |
| **Vancouver** | Retail funnel analytics (Walmart background) + full-spectrum DA roles |
| **Remote Canada / US** | Demonstrates you can own metrics, not just train models |

**Complements** (does not duplicate): supply chain ML, stock falsification rigor, healthcare interpretability, medallion BI pipeline.

---

## What's delivered (Phase 1, v1)

| Component | Deliverable | Evidence | Status |
|-----------|-------------|----------|--------|
| **Metric layer** | Versioned SQL in `sql/metrics/` | Conversion, AOV, D7 repeat — each with pandas-parity pytest on fixtures | ✅ |
| **Experiment** | Simulated RCT, labeled synthetic effect | Hashed `customer_unique_id` assignment (seed 42) | ✅ |
| **Analysis** | Lift + 95% bootstrap CI, Welch t, two-proportion z | `reports/experiment_001.md` auto-generated | ✅ |
| **Power** | MDE + sample-size reasoning | AOV MDE 4.32, conversion MDE 0.0030 in report | ✅ |
| **Integrity** | Balance guard + no-leakage design | 0.6% arm gap (within 5% tol); guardrail flat | ✅ |
| **Honesty** | README + report banners | Simulation labeled; SHIP/HOLD/MORE-DATA all valid | ✅ |
| **Dashboard** | Streamlit variant comparison | Control vs treatment with CIs visible | ⏳ Phase 2 |

---

## Dataset — Olist Brazilian E-Commerce

**Source:** [Kaggle — Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)  
**Local path:** `data/raw/olist/` (9 CSVs onboarded, gitignored)

| File | Role |
|------|------|
| `olist_orders_dataset.csv` | Funnel spine — status, purchase timestamps |
| `olist_order_items_dataset.csv` | Line items, price, freight |
| `olist_order_payments_dataset.csv` | Payment type and value |
| `olist_customers_dataset.csv` | Customer geography |
| `olist_products_dataset.csv` | Product attributes |
| `olist_sellers_dataset.csv` | Seller geography |
| `product_category_name_translation.csv` | English category labels |
| `olist_order_reviews_dataset.csv` | Optional v2 |
| `olist_geolocation_dataset.csv` | Optional v2 |

**Why Olist (not DataCo):** Multi-table relational data supports credible SQL joins, funnels, and cohorts. The supply chain sibling repo taught that single dominant categorical features and tutorial-grade semantics weaken the business story — this project runs an **EDA gate** before any reporting.

### Entity relationship (simplified)

```mermaid
erDiagram
    customers ||--o{ orders : places
    orders ||--o{ order_items : contains
    orders ||--o{ order_payments : paid_by
    orders {
        string order_id PK
        string customer_id FK
        string order_status
        datetime order_purchase_timestamp
    }
    order_items {
        string order_id FK
        string product_id FK
        float price
    }
```

---

## Locked metrics (post-EDA, implemented)

| Metric | Locked definition | Role |
|--------|-------------------|------|
| **Conversion** | % orders with `order_status == 'delivered'` | Guardrail |
| **AOV** | `sum(payment_value)` per order, averaged per variant (multi-payment rows summed first) | Primary |
| **D7 repeat** | Customer with a 2nd order within 7 days of the 1st | Exploratory |

Each metric is **SQL in `sql/metrics/`** wrapped by a thin DuckDB Python adapter, with a pytest
that asserts the SQL matches a pandas reimplementation on a ≤100-row fixture (never the full
100k+ load in CI). Full definitions: [`docs/METRICS.md`](./docs/METRICS.md).

---

## Experiment design (v1 approach)

Olist has **no native A/B column**. The locked v1 approach:

1. Filter a cohort (date range + valid `customer_id`)
2. Assign variant: `hash(customer_id, seed=42) % 2` → control / treatment
3. Compare metrics with lift, 95% CI, and plain-English recommendation

**Locked approach: Labeled synthetic lift.** A `SIMULATED_EFFECT = 0.05` is injected on
`order_value` for the treatment arm *after* assignment — methodology demo only, marked in code
constants and every report banner. Natural-experiment and pure-null variants are documented as
future options in [`docs/FUTURE_ENHANCEMENTS.md`](./docs/FUTURE_ENHANCEMENTS.md).

See [`CONTEXT.md`](./CONTEXT.md) §6 and [`docs/EXPERIMENT_DESIGN.md`](./docs/EXPERIMENT_DESIGN.md).

---

## Target architecture (post-EDA)

```
product-experimentation-analytics/
├── src/
│   ├── metrics/          # Python wrappers → sql/
│   ├── experiment/       # assignment, analysis, power
│   ├── report/           # markdown report generator
│   └── io/               # DuckDB loader
├── sql/
│   ├── metrics/          # conversion.sql, aov.sql, d7_repeat.sql
│   └── experiment/       # cohort.sql, variant_assignment.sql
├── tests/fixtures/       # ≤100 rows — no full Olist in unit tests
├── notebooks/            # EDA only
├── reports/              # eda_gate.md, experiment_001.md
├── app/                  # Streamlit (Phase 2)
└── docs/                 # METRICS.md, EXPERIMENT_DESIGN.md
```

**Stack:** Python 3.12+, DuckDB (local SQL), scipy, pytest, Streamlit (v1 dashboard).

**Explicitly out of scope v1:** Airflow, dbt, Snowflake, cloud warehouse — GitHub Actions covers orchestration narrative.

---

## Phase 0 — EDA gate (PASSED → GO)

Implementation was gated on EDA. The gate returned **GO**; full `src/` then built.

| Deliverable | Status |
|-------------|--------|
| `notebooks/00_eda_gate.ipynb` | ✅ Executed |
| `reports/eda_gate.md` (GO/NO-GO) | ✅ **GO** |
| `docs/DATA_DICTIONARY.md` | ✅ Done |

### EDA gate checks

- Row counts per table; date ranges
- Join integrity: orders ↔ payments ↔ items (% orphans)
- Conversion rate overall and by month
- D7 repeat purchase feasibility
- Covariate balance under hash assignment
- DuckDB conversion query matches pandas

**Pass criteria:** ≥50k valid orders · conversion computable without >5% ambiguous status · metric SQL reproducible.

Full checklist: [`../PORTFOLIO_EDA_SPRINT.md`](../PORTFOLIO_EDA_SPRINT.md)

---

## How this differs from sibling repos

| Repo | Focus |
|------|-------|
| `supply-chain-optimization-ml` | Interpretable ML, leakage control — **not** experimentation |
| `multi-modal-stock-recommender` | Time series, falsification gates — **not** product funnels |
| `healthcare-noshow-predictor` | Regulated health ops, calibration — **not** A/B |
| `medallion-analytics-pipeline` | Lakehouse + Power BI — **not** statistical testing |

---

## Reproduce

```bash
# 1. Install dependencies and pre-commit hooks
make setup

# 2. Place the Olist CSVs in data/raw/olist/
#    Download from https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
#    Files needed: olist_orders_dataset.csv, olist_order_payments_dataset.csv,
#                  olist_customers_dataset.csv, olist_order_items_dataset.csv

# 3. Run the simulated experiment (bootstrap takes ~10-60 s on ~50k/arm)
make experiment     # writes reports/experiment_001.md

# 4. Run the full test suite (fixtures only — no full Olist in tests)
make test
```

Generated outputs:
- `reports/experiment_001.md` — ship/no-ship recommendation with 95% CI, power table,
  simulation disclaimer

Metric and design documentation:
- [`docs/METRICS.md`](./docs/METRICS.md) — three metric definitions, SQL paths, AOV
  multi-payment rule, person-key rule
- [`docs/EXPERIMENT_DESIGN.md`](./docs/EXPERIMENT_DESIGN.md) — cohort window, assignment,
  injected effect, inference, power/MDE

---

## Developer entry points

1. [`CONTEXT.md`](./CONTEXT.md) — mission, locked decisions, session playbook
2. [`docs/METRICS.md`](./docs/METRICS.md) — metric definitions
3. [`docs/EXPERIMENT_DESIGN.md`](./docs/EXPERIMENT_DESIGN.md) — experiment design
4. [`CLAUDE.md`](./CLAUDE.md) — rules and commands
5. [`../PORTFOLIO_LOCKED_DECISIONS.md`](../PORTFOLIO_LOCKED_DECISIONS.md) — anti-hallucination rules

### Quick setup

```bash
cd product-experimentation-analytics
make setup
make test
make experiment
```

**Data:** Place CSVs in `data/raw/olist/`. If missing, download from [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).

---

## Resume bullet

> Defined funnel metrics (conversion, AOV, D7-repeat) in versioned SQL over ~99k Olist
> e-commerce orders; ran a simulated A/B test with hashed person-level assignment, 95% bootstrap
> CIs, Welch/two-proportion tests, and MDE power analysis; auto-generated a ship/no-ship report
> with a guardrail-validated, no-leakage pipeline (82 tests, 95% coverage, mypy strict).

---

## Author

**Tirth Joshi** — UBC Master of Data Science · Former analytics (VGH, BCCNM, Walmart Canada)

Do **not** claim Olist or simulated experiments as employer work.

---

## License

MIT License. See [`LICENSE`](LICENSE) when added.
