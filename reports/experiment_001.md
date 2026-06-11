# Experiment 001 — Simulated AOV Lift

> **Simulated experiment.** Olist has no native A/B test. Variants are assigned by hashed `customer_unique_id` (seed 42) on historical data, and the treatment effect is a synthetic `SIMULATED_EFFECT` injected for methodology demonstration. Not a real lift.

Injected `SIMULATED_EFFECT` = 0.05

## Sample sizes
- control: 49694
- treatment: 49398

## Metrics

| Metric | Control | Treatment | Lift | 95% CI | p |
|---|---|---|---|---|---|
| AOV (primary) | 159.88 | 170.03 | 10.15 | (7.36, 13.11) | 0.0000 |
| AOV (covariate-adjusted) | 160.64 | 169.27 | 8.63 | (6.15, 11.15) | — |
| Conversion (guardrail) | 0.9700 | 0.9718 | 0.0018 | (-0.0003, 0.0039) | 0.0874 |
| D7 repeat (exploratory) | 0.0088 | 0.0084 | — | — | — |

Covariate adjustment (ANCOVA on pre-treatment `freight_value`, θ=4.9570, estimated pooled pre-injection): CI width is 87% of the unadjusted width. Both rows shown for auditability. The adjusted row uses lower variance by removing freight_value correlation, yielding narrower confidence intervals.

## Power
- AOV MDE: 4.32
- Conversion MDE: 0.0030

## Recommendation
**SHIP** — based on the **covariate-adjusted** AOV 95% bootstrap CI (6.15, 11.15).
