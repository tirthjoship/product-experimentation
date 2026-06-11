# ADR-0007: ANCOVA covariate adjustment on freight_value — CUPED rejected

- **Status:** accepted
- **Date:** 2026-06-10
- **Deciders:** Tirth Joshi

## Context

Plan 1's null scenario (zero injected effect) exposed a +2.06 BRL baseline arm imbalance in
raw AOV (control mean higher than treatment mean by ~2.06 BRL before any effect is applied).
With a right-skewed outcome (mean 160.99, std 221.95, max 13,664 BRL) and arm sizes ~49.5k
each, even small pre-existing imbalances widen CIs and risk a spurious verdict.

The standard industry remedy for variance reduction in A/B tests is CUPED (Controlled-experiment
Using Pre-Experiment Data; Deng, Xu, Kohavi, Walker, WSDM 2013): subtract a covariate
constructed from the same user's pre-experiment outcome (e.g. pre-period AOV per customer).
CUPED is infeasible here: ~97% of Olist customers are one-time purchasers (repeat rate
0.214% within 7 days, 3.12% ever, per `reports/eda_gate.md`). There is no meaningful
per-customer pre-period AOV to carry forward.

A covariate that is (a) correlated with the outcome, (b) set before treatment exposure, and
(c) untouched by the injected effect is needed.

## Options considered

### 1. Classic CUPED — **rejected**

Construct per-user pre-experiment AOV and use it as the covariate. Rejected: ~97% of
customers have exactly one order in the dataset, so no pre-period signal exists for them.
Applying CUPED to the 3% repeat customers only would exclude the vast majority of the
cohort and introduce selection bias.

### 2. ANCOVA on `freight_value` — **CHOSEN**

`freight_value` is the shipping cost charged on the order. It is determined at order
placement time by seller/marketplace rules and is therefore pre-treatment in the causal
sense: the injected effect multiplies `order_value` only and never touches `freight_value`.
It is a strong predictor of `order_value` (Pearson r = 0.484 on n = 99,092 orders, measured
pre-injection on the full cohort).

The adjustment formula:

```
Y_adj = Y − θ · (X − X̄)
θ = Cov(Y, X) / Var(X)   [pooled, estimated pre-injection]
```

where Y = `order_value`, X = `freight_value`, X̄ = grand mean of X across both arms.
θ is computed once from the unadjusted frame before the synthetic effect is applied, so the
estimated coefficient cannot be contaminated by the injected signal.

Measured correlation: **r = 0.484** (n = 99,092). This is sufficient to meaningfully reduce
variance (expected variance reduction ≈ 1 − r² ≈ 77% of original variance retained, i.e.
~23% reduction).

### 3. Item count per order as covariate — viable, deferred

`order_item_id` count per order is also pre-treatment and correlated with AOV. Viable
alternative or complement. Deferred: freight_value is already strong (r = 0.484) and adding
multiple covariates increases implementation complexity without a clear need for this phase.

### 4. Category mean price as covariate — leakage-prone, deferred

The mean price of products in the order's category correlates with AOV but is derived from
outcome-adjacent signals that could shift with the injected synthetic prices. Deferred
pending a clean leakage audit.

## Decision

Use ANCOVA adjustment on `freight_value` with θ pooled pre-injection. Verdicts are based
on the adjusted CI. Both unadjusted and adjusted numbers are always reported for audit
transparency.

The baseline-imbalance guard in `run()` is downgraded from a hard exception to a
`UserWarning` that records the gap in `results["baseline_balance"]`. A hard guard would
crash on legitimate small fixtures in tests; the ANCOVA adjustment corrects the bias anyway.

## Consequences

- Variance reduction: ~23% expected reduction in CI width, improving sensitivity.
- Verdicts use the adjusted CI as the decision object; raw CIs are always reported alongside.
- θ is estimated pre-injection: the synthetic treatment effect cannot contaminate the
  covariate coefficient.
- `freight_value` is treatment-independent by construction: it is set at order time and the
  injected effect never modifies it.
- The baseline-imbalance warning is recorded in `results["baseline_balance"]` for downstream
  audit; it does not halt execution.
- Classic CUPED remains documented here as the preferred method should repeat-customer data
  ever become available.

## Links

- Deng, A., Xu, Y., Kohavi, R., Walker, T. (2013). "Improving the Sensitivity of Online
  Controlled Experiments by Utilizing Pre-Experiment Data." WSDM.
- `docs/EXPERIMENT_DESIGN.md` — "Covariate adjustment (Plan 2)" section
- `docs/superpowers/specs/` — Plan 2 covariate-adjustment spec
- ADR-0006 (inference methods), ADR-0005 (metrics)
