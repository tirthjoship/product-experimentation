# Plan 2 — Covariate-Adjusted Variance Reduction (Design Spec)

**Date:** 2026-06-10
**Status:** Spec (approved direction; turn into a TDD plan via writing-plans before building)
**Predecessor:** Plan 1 (inference depth) — `docs/superpowers/plans/2026-06-10-experiment-inference-depth.md`, branch `feat/experiment-inference-depth` (PR #12).
**Series:** Plan 2 of 4. Next: Plan 3 (narrative reframe + PM memo), Plan 4 (P4 natural experiment).

---

## Problem (what Plan 1 surfaced)

Plan 1's scenario sweep made a latent flaw visible: the **`null` scenario** (zero injected effect)
still reports an AOV **lift of +2.06, CI (-0.67, 4.93)**. With no treatment effect the lift should
be ~0. The +2.06 is a **baseline arm imbalance** — random hash assignment happened to put slightly
higher-value customers in `treatment` (pre-effect ~161.9 vs control ~159.9). Two costs:

1. **Bias into the headline.** ~2 of the `large` scenario's +10.15 lift is pre-existing imbalance,
   not injected effect (~20% of the reported number).
2. **Wide CIs.** AOV is heavy-tailed (mean 161, median 105, max 13,664); the difference-in-means
   estimator has large variance, so the experiment needs a big effect to clear significance.

The current balance guard (`src/experiment/balance.py`) only checks **arm sizes**, not the **primary
metric's baseline** — so this imbalance passes unguarded.

## Why classic CUPED does not work here

CUPED (Controlled-experiment Using Pre-Experiment Data; Deng et al., 2013, Microsoft) reduces variance
by conditioning each unit's outcome on **that same unit's pre-experiment value of the metric**. On Olist
that input does not exist:

- **~97% one-time customers** — `customer_unique_id` mostly appears once (same fact that demoted D7 to
  exploratory: 0.214% repeat-within-7d, 3.12% ever-repeat; `reports/eda_gate.md`).
- **Near-empty pre-cohort window** — Olist starts 2016-09 with 1–4 orders/month; the cohort is
  2017-01 → 2018-08. For almost every customer the experiment order is their only order, so there is no
  prior AOV to condition on.

A pre-period-AOV covariate would be missing/constant for ~97% of rows → CUPED cannot bite.

## Chosen approach — ANCOVA / regression adjustment on a pre-treatment covariate

CUPED is a special case of **regression adjustment (ANCOVA)**: instead of the unit's pre-period outcome,
use **any covariate `X` that is (a) known at/before assignment, (b) correlated with the outcome `Y`,
(c) independent of treatment.** Olist has order-level covariates that qualify. Adjust:

```
Y_adj = Y − θ·(X − X̄)        θ = cov(Y, X) / var(X)   (estimated treatment-independently)
```

`Y_adj` has the **same expected arm difference** as `Y` (θ·(X−X̄) has mean ~0 within each arm because X is
balanced under randomization) but **lower variance** to the extent X predicts Y — typically a 20–50% CI
shrink. Because X is balanced across arms, the adjustment also **removes the share of the baseline gap
that X explains**, shrinking the `null`-scenario lift toward 0.

### Covariate choice (locked default: `freight_value`)

| Candidate | In data | Pre-treatment? | Corr. with order_value | Verdict |
|---|---|---|---|---|
| **`freight_value`** (sum per order) | `order_items` | yes — shipping cost set at order time | moderate–high (bigger/heavier carts cost more) | **Default.** Simple, one column, untouched by the injected effect. |
| item count per order | `order_items` | yes | high | Strong alternative; slightly more SQL. |
| product-category mean price | `order_items`+`products` | yes | high | Most predictive but needs target-encoding care (leakage risk) — defer. |

**Default = `freight_value`.** The injected effect multiplies `order_value` only, so `freight_value` is
untouched → strictly treatment-independent. (Open to swap to item-count if EDA shows higher correlation.)

### θ estimation (avoid contaminating θ with the effect)

Estimate θ on data **independent of the injected effect**: compute `cov(Y, X)`/`var(X)` on the
**pre-injection frame** (raw `order_value`, pooled across both arms) — i.e. before
`apply_simulated_effect`. A single pooled θ is applied to both arms. This keeps θ honest: it reflects the
natural freight↔value relationship, not the synthetic lift.

## Honesty constraints (carried)

- `X = freight_value` is pre-treatment and untouched by `SIMULATED_EFFECT` — state this in the report.
- θ estimated pre-injection, pooled — documented in `docs/EXPERIMENT_DESIGN.md`.
- `seed=42` unchanged; adjustment is deterministic.
- Report BOTH unadjusted and adjusted CIs side by side so the variance reduction is visible and auditable
  (no hiding the raw number).

---

## Build outline (turn into TDD tasks via writing-plans)

**A. Surface the covariate into the experiment frame**
- `sql/experiment/cohort.sql` — add per-order `freight_value` (sum of `order_items.freight_value` grouped
  by `order_id`; LEFT JOIN so item-less orders → 0/NULL handled). Keep `ORDER BY order_id` (determinism).
- `src/io/loader.py` / `load_olist` — already loads `order_items`; ensure the join is wired.
- `docs/METRICS.md` SQL contract table — add `freight_value` column to the `experiment_frame` schema.
- Fixtures: add a `freight_value` column to `tests/fixtures/*` order/item fixtures + conftest frame.

**B. CUPED/ANCOVA function**
- `src/experiment/cuped.py` (new) — `cuped_theta(y, x) -> float` and
  `cuped_adjust(y, x, theta, x_mean) -> np.ndarray`. Pure numpy, unit-tested (constant-shift,
  zero-correlation → θ≈0 → no change, known-correlation variance drop).

**C. Wire into `run()`**
- Compute θ on the pre-injection pooled `(order_value, freight_value)`; compute `x_mean`.
- After injection, form `Y_adj` per arm; run the existing BCa `bootstrap_ci_diff_means` on `Y_adj`.
- Extend the results dict with an `aov_adjusted` block (control/treatment adj means, lift, CI, and the
  variance-reduction ratio vs unadjusted). Keep the unadjusted `aov` block as-is.

**D. Report + balance guard**
- `src/report/experiment_report.py` — add an "AOV (covariate-adjusted)" row + a one-line variance-reduction
  note; scenarios report likewise.
- `src/experiment/balance.py` — add a **pre-period AOV (or freight) balance check** alongside the size
  check, so the imbalance the `null` scenario exposed is guarded going forward.
- Regenerate committed artifacts (`experiment_001.*`, `experiment_scenarios.*`, `sample_results.json`)
  with the adjusted block; keep determinism (run twice, diff).

## Success criteria

- Adjusted AOV CI is **narrower** than unadjusted on full data (target ≥15% width reduction).
- `null`-scenario adjusted lift is **closer to 0** than the unadjusted +2.06.
- Both unadjusted and adjusted numbers reported (auditable).
- 64+ tests pass, mypy --strict clean, artifacts byte-stable.

## Open decisions (resolve at writing-plans time)

1. Covariate = `freight_value` (default) vs item-count — confirm with a quick correlation check in EDA.
2. Adjust the **scenario sweep** rows too, or only the headline `experiment_001`? (Lean: both, for
   consistency.)
3. Whether to also add an ADR (`docs/adr/0007-covariate-adjustment-not-cuped.md`) recording why classic
   CUPED was rejected — recommended (it's a non-obvious decision).

## Out of scope

- Classic pre-period CUPED (infeasible — see above).
- Target/category encoding (leakage-prone; defer).
- Changing the assignment, seed, cohort window, or the injected-effect mechanism.

## Reference

Deng, Xu, Kohavi, Walker (2013), *Improving the Sensitivity of Online Controlled Experiments by Utilizing
Pre-Experiment Data* (CUPED), WSDM. ANCOVA generalization: any pre-treatment covariate, not just the
pre-period outcome.
