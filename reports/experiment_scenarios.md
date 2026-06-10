# Experiment Scenarios — Decision Rule Validation

> **Simulated experiment.** Olist has no native A/B test. Variants are assigned by hashed `customer_unique_id` (seed 42) on historical data, and the treatment effect is a synthetic `SIMULATED_EFFECT` injected for methodology demonstration. Not a real lift.

Each row injects a different `SIMULATED_EFFECT` and reports the verdict the AOV 95% bootstrap CI produces. The rule yields SHIP / DO NOT SHIP / NEED MORE DATA — not just SHIP — which is the point: the pipeline handles the hard cases.

| Scenario | Injected effect | Control | Treatment | Lift | 95% CI | Verdict |
|---|---|---|---|---|---|---|
| adverse | -0.05 | 159.88 | 153.84 | -6.04 | (-8.69, -3.24) | DO NOT SHIP |
| null | 0.0 | 159.88 | 161.94 | 2.06 | (-0.67, 4.93) | NEED MORE DATA |
| large | 0.05 | 159.88 | 170.03 | 10.15 | (7.36, 13.11) | SHIP |
