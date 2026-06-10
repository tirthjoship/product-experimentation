# Experiment 001 — Simulated AOV Lift

> **Simulated experiment.** Olist has no native A/B test. Variants are assigned by hashed `customer_unique_id` (seed 42) on historical data, and the treatment effect is a synthetic `SIMULATED_EFFECT` injected for methodology demonstration. Not a real lift.

Injected `SIMULATED_EFFECT` = 0.05

## Sample sizes
- control: 49694
- treatment: 49398

## Metrics

| Metric | Control | Treatment | Lift | 95% CI | p |
|---|---|---|---|---|---|
| AOV (primary) | 159.88 | 170.03 | 10.15 | (7.30, 13.03) | 0.0000 |
| Conversion (guardrail) | 0.9700 | 0.9718 | 0.0018 | (-0.0003, 0.0039) | 0.0874 |
| D7 repeat (exploratory) | 0.0088 | 0.0084 | — | — | — |

## Power
- AOV MDE: 4.32
- Conversion MDE: 0.0030

## Recommendation
**SHIP** — based on the AOV 95% bootstrap CI (7.30, 13.03).
