# Plan 3 — Installment-Expansion Narrative + PM Decision Memo (Design Spec)

**Date:** 2026-06-11
**Status:** Spec (approved direction; turn into a TDD plan via writing-plans before building)
**Predecessor:** Plan 2 (covariate adjustment) — merged to main; ANCOVA on `freight_value`,
adjusted-CI verdicts, 82 tests / 95% cov.
**Series:** Plan 3 of 4. Next: Plan 4 (DiD natural experiment, own spec).

---

## Problem

The pipeline is statistically credible (BCa CIs, ANCOVA, 3-verdict sweep, honest misses) but has
**no product story**. A reader sees JSON and CIs with a generic "simulated AOV lift" label — no
hypothesis a PM would recognize, no decision memo, no "so what". Plan 3 supplies the narrative
layer and the single artifact recruiters actually read: a PM decision readout.

## Locked framing — installment-expansion test

**Fictional product change:** checkout today caps interest-free installments at **6x**; treatment
raises the cap to **10x interest-free**. Hypothesis: in Brazilian e-commerce the binding
constraint is the *monthly* payment, not the sticker price — lower per-month cost → customers
build bigger baskets / buy higher-ticket items → **AOV ↑ (primary)**. Risk: more credit stretched
over a longer horizon → more payment failures and cancellations → **delivered-rate ↓ (guardrail,
now load-bearing)**.

### Why this framing (decision record)

1. **Dataset-native.** Olist `order_payments` has `payment_installments` for real. Measured on
   full data (2026-06-11): **49.4%** of payment rows use >1 installment; **73.9%** are credit
   card; median 1, p75 = 4, max 24 installments. The affordability mechanism is observable in
   THIS dataset, not imported from a blog post.
2. **Portfolio separation.** Earlier default (free-shipping threshold) echoed
   `supply-chain-optimization-ml`'s freight/logistics domain. Installments framing leaves
   freight 100% to the supply-chain project; this project owns customer/payments/product levers
   and causal methods. See the supply-chain `docs/FUTURE_ENHANCEMENTS.md` for the matching
   non-overlap commitment on that side.
3. **Machinery fits unchanged.** Customer-level hash assignment is exactly how an installment
   offer would roll out (same customer always sees the same cap). The injected multiplicative
   effect on `order_value` reads as "bigger baskets among treated customers." `freight_value`
   stays a valid ANCOVA covariate (pre-treatment basket-size proxy) — a statistical detail, not
   the story. The delivered-rate guardrail acquires real meaning: credit denials / cancellations
   are exactly non-delivered orders.
4. **Memo has genuine tension.** AOV lift vs credit-risk guardrail = a real PM trade-off, not a
   rubber-stamp SHIP.

Alternatives considered: cross-sell bundle module (recsys-adjacent, collides with
stock-recommender's "recommendation" identity); tiered minimum-spend coupon (discount confounds
revenue vs AOV; weakens guardrail logic). Both rejected.

## Deliverables

### A. Motivation stats — real numbers, committed artifact (no invented metrics)

- `sql/eda/installments.sql` — over `order_payments` (joined to the cohort window via `orders`):
  share of orders with any installment payment (>1), AOV by installment bucket
  (1 / 2–3 / 4–6 / 7+), credit-card share of payment value. Deterministic `ORDER BY`.
- Small runner (`src/report/installment_motivation.py` or extension of an existing module —
  writing-plans decides) emitting `reports/installment_motivation.{md,json}`. Seed-free,
  deterministic, byte-stable.
- Fixtures: add `payment_installments` column to `tests/fixtures/order_payments.csv`; tests use
  fixtures only.

### B. PM decision memo — `reports/experiment_001_readout.md`

Hand-written judgment artifact (not generated), but **every number quoted must exist in a
committed artifact** (`experiment_001.json`, `experiment_scenarios.json`,
`installment_motivation.json`). Structure:

1. **TL;DR** — verdict + one-line rationale (from the `large` headline scenario, adjusted CI).
2. **Context & motivation** — installment economics with the real Olist numbers (artifact A).
3. **Hypothesis & change** — 6x→10x cap; mechanism; expected effect direction on each metric.
4. **Design** — unit of randomization + why customer-level; seed 42; cohort window; metric tiers
   (AOV primary / delivered-rate guardrail / D7 exploratory + why D7 is exploratory: ~3%
   ever-repeat); MDE & power; ANCOVA adjustment (one paragraph, plain language).
5. **Results** — unadjusted AND adjusted side by side; scenario sweep table reframed as
   "what if the offer backfires / does nothing / works" (adverse / null / large).
6. **Guardrail readout** — delivered-rate deltas + what a real credit-risk signal would look like.
7. **Honesty & caveats** — simulation label (prominent, top and bottom); ci_width_ratio 0.868 vs
   ≤0.85 target disclosed; baseline imbalance story (+2.06 → +0.54 after adjustment); one-time
   customer base limits repeat-purchase claims.
8. **Recommendation** — verdict + post-launch monitoring plan (delivered-rate by installment
   bucket, payment-failure proxy, basket-mix shift) + rollback trigger.

### C. Memo↔artifact integrity test

`tests/test_readout_integrity.py` — parses the memo for its quoted headline numbers (lift,
adjusted CI bounds, verdict word, motivation shares) and asserts each matches the committed JSON
artifacts. Enforces rule 1 ("no invented metrics") in CI forever, not just at review time.
Implementation detail (marker syntax vs regex on the table) → writing-plans.

### D. Framing sweep across existing docs

- `README.md` — experiment section reframed to installment-expansion test; link the memo as the
  headline artifact; simulation disclaimer unchanged.
- `docs/EXPERIMENT_DESIGN.md` — add framing section (fictional change, mechanism, why
  customer-level assignment fits an offer test).
- `CONTEXT.md` glossary/decision list — framing recorded as locked.
- ADR `0008-installment-framing-over-free-shipping.md` — context, options (free-shipping,
  cross-sell, coupon), decision, consequences (incl. portfolio-separation rationale).
- `src/report/experiment_report.py` DISCLAIMER + report titles: writing-plans decides whether a
  one-line framing mention is added; the simulation label itself must not weaken.

## Honesty constraints (carried, non-negotiable)

- Simulated experiment labeled in memo, README, and reports — unchanged rule.
- Memo numbers only from committed artifacts (enforced by deliverable C).
- No code changes to assignment, effect injection, seed, cohort window, or metric definitions.
- Motivation stats are **descriptive** (mechanism exists); memo must not imply they estimate the
  treatment effect.

## Success criteria

- `reports/experiment_001_readout.md` exists; a non-statistician can read TL;DR → recommendation
  in <5 minutes and every number traces to a committed artifact.
- `reports/installment_motivation.{md,json}` committed, deterministic (two-run byte-identical).
- Integrity test red if any quoted number drifts from artifacts.
- All existing gates stay green: tests (82+ → more), 90% coverage gate, mypy strict, byte-stable
  artifacts. CI green on dev and main.

## Out of scope

- Plan 4 (DiD natural experiment) — own spec.
- P2 dashboard, P3 reproducibility CI gate — earlier roadmap, unscheduled.
- Any new inference machinery (no new estimators, no new metrics in the pipeline).
- Modeling actual credit default (no such labels in Olist; guardrail stays delivered-rate).

## Open decisions (resolve at writing-plans time)

1. Motivation runner location: new `src/report/installment_motivation.py` vs extending
   `run_experiment.py` with a `--motivation` flag (lean: new module, single responsibility).
2. Integrity-test mechanism: HTML-comment markers in the memo (e.g. `<!-- metric:aov_lift -->`)
   vs regex on table cells (lean: markers — robust to prose edits).
3. Whether the scenario report intro also gets the installment wording or stays generic
   (lean: one-line framing reference, keep report code-generated text minimal).
