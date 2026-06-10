# ADR-0006: Bootstrap CI + Welch t-test + two-proportion z

- **Status:** accepted
- **Date:** 2026-06-09
- **Deciders:** Tirth Joshi

## Context

AOV is right-skewed with a long tail (mean 160.99, median 105.29, max 13,664 BRL). A plain
t-test leans on a normality assumption the data violates, but a classic p-value is still what
many reviewers expect to see. Conversion is a proportion, a different inference problem.

## Decision

- **AOV (primary):** bootstrap 95% CI on the difference in means (10,000 resamples, seed 42) as
  the headline result, with a Welch t-test p-value as a cross-check.
- **Conversion (guardrail):** two-proportion z-test with lift and 95% CI.
- **D7 (exploratory):** no test.

## Options considered

- **Chosen — bootstrap + Welch:** bootstrap is robust to AOV's skew and makes the CI the primary
  object; Welch supplies the familiar p-value without being load-bearing.
- **Welch t-test only:** rejected — skew/outliers weaken it with no robustness check.
- **Bootstrap only:** rejected — omits the classic p-value some reviewers expect.
- **Add log-transform variant:** deferred — extra interpretation overhead beyond this phase.

## Consequences

Seed 42 makes the bootstrap reproducible (asserted in tests). The CI is the decision object:
lift CI above 0 → SHIP, below 0 → DO NOT SHIP, spanning 0 → NEED MORE DATA. All reference values
in the implementation plan were computed against the real scipy/numpy implementations.

## Links

`docs/superpowers/specs/2026-06-09-metrics-and-experiment-design.md`,
`docs/superpowers/plans/2026-06-09-metrics-and-experiment.md` (Task 9), ADR-0005.
