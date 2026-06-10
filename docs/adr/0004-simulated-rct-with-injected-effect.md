# ADR-0004: Simulated RCT with a labeled injected effect

- **Status:** accepted
- **Date:** 2026-06-09
- **Deciders:** Tirth Joshi

## Context

Olist has no native experiment column. To demonstrate A/B analysis we must construct the
experiment ourselves, and the construction has to stay honest for a portfolio piece — a reader
must never mistake a synthetic effect for a real one.

## Decision

Run a simulated RCT: assign variants by `md5(customer_unique_id + seed)` with seed 42 at the
person level, then inject a multiplicative `SIMULATED_EFFECT` (+5%) into the treatment group's
primary metric after assignment. The constant is named `SIMULATED_EFFECT` so the synthetic
nature is visible in code, and every report carries a simulation disclaimer.

## Options considered

- **Chosen — simulated RCT + injected effect:** cleanest demonstration of assignment integrity,
  power, CI, and a ship decision; fully honest because the effect is labeled.
- **Simulated RCT, null result (no injection):** honest but the report shows lift ≈ 0; less
  compelling for showing the full decision machinery. (Kept as the A/A sanity check instead.)
- **Natural experiment / difference-in-differences:** more "real" but observational and
  confounded; heavier assumptions to defend, and EDA surfaced no clean quasi-treatment.
- **Both A/A and A/B:** strongest story but more code/report surface than this phase needs.

## Consequences

The pipeline injects the effect only after assignment, so assignment never depends on outcomes
(enforced by the `leakage-auditor`). An A/A sanity check (pre-injection lift CI spans 0)
validates the assignment. +5% sits above the AOV MDE (2.45%), so the result is detectable and
the report reaches a clean SHIP recommendation. Seed 42 is pinned for assignment and bootstrap.

## Links

`docs/superpowers/specs/2026-06-09-metrics-and-experiment-design.md`, `CONTEXT.md` §6, ADR-0005.
