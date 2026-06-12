# Experiment 001 Readout — Installment-Expansion Test

> **Simulated experiment.** Olist has no native A/B test. Variants are assigned by hashed
> `customer_unique_id` (seed 42) on historical data; the treatment effect is a labeled synthetic
> injection. This memo demonstrates experiment methodology and decision writing — not a real lift.

## TL;DR

**SHIP** (in the headline scenario). Raising the interest-free installment cap from 6x to 10x
lifted AOV by **8.63 BRL** (covariate-adjusted 95% CI **(6.15, 11.15)**, excludes zero) with no
detectable damage to the delivered-rate guardrail. Recommendation: roll out, with the
post-launch monitoring plan below — the guardrail, not the lift, carries the real risk.

## Context & motivation (real Olist numbers)

Brazilian e-commerce is installment-driven. In our cohort window:

- **51.4%** of orders are paid in more than one installment.
- Credit cards carry **78.4%** of payment value.
- AOV rises steeply with installment count (see `reports/installment_motivation.md` — orders
  paid in 7+ installments average several times the basket of single-payment orders).

These are **descriptive** numbers: they show the affordability mechanism exists, not what the
cap change causes. Estimating the causal effect is the experiment's job.

## Hypothesis & change

Checkout today caps interest-free installments at **6x**. Treatment raises the cap to **10x**.
The binding constraint on basket size is the *monthly* payment, not the sticker price; lowering
per-month cost lets customers build bigger baskets.

- **Primary:** AOV ↑ (order_value per order).
- **Guardrail:** delivered-rate — more credit stretched over a longer horizon means more payment
  failures and cancellations, which surface as non-delivered orders.
- **Exploratory:** D7 repeat purchase (Olist is ~97% one-time buyers, so this can only be
  directional).

## Design

- **Randomization:** by `customer_unique_id` hash (seed 42) — a customer must always see the
  same cap, so customer-level assignment is the only correct unit. n = **49,694** control /
  **49,398** treatment.
- **Cohort:** orders 2017-01 → 2018-08 (stable-volume window; pre-registered in
  `docs/EXPERIMENT_DESIGN.md`).
- **Inference:** BCa bootstrap CI on the AOV difference, plus ANCOVA adjustment on pre-treatment
  `freight_value` (a basket-size proxy, estimated pooled pre-injection). Adjustment removes
  baseline arm imbalance and shrinks the CI to **87%** of its unadjusted width.
- **Power:** MDE on AOV ≈ **4.32** BRL at α=0.05 — the observed lift clears it.

## Results

| Metric | Control | Treatment | Lift | 95% CI | Read |
|---|---|---|---|---|---|
| AOV (unadjusted) | — | — | 10.15 | (7.36, 13.11) | biased up by baseline imbalance |
| **AOV (covariate-adjusted)** | — | — | **8.63** | **(6.15, 11.15)** | **decision basis** |
| Delivered-rate (guardrail) | 0.9700 | 0.9718 | +0.0018 | (-0.0003, 0.0039) | no detectable harm |

Why two AOV rows: random assignment happened to put slightly higher-value customers in
treatment. The null scenario (zero injected effect) still shows a **2.06** raw "lift"; after
adjustment it shrinks to **0.54**. Reporting both rows keeps the bias visible and auditable.

### Decision-rule stress test (scenario sweep)

The same pipeline was run with a harmful, zero, and large injected effect — the decision rule
must produce all three verdicts, not just SHIP:

| Scenario | Meaning | Verdict |
|---|---|---|
| adverse | the offer backfires (cancellations, remorse) | DO NOT SHIP |
| null | the cap change does nothing | NEED MORE DATA |
| large | affordability mechanism works | SHIP |

## Caveats (read before acting)

1. **This is a simulated experiment** — the lift is injected; the methodology is the product.
2. CI-width reduction from adjustment was 13% (87% ratio) vs a ≥15% target — disclosed, not
   tuned (ADR 0007).
3. ~97% one-time buyers: repeat-purchase effects are out of reach for this dataset.
4. Delivered-rate is a proxy guardrail; a real rollout would track payment-failure and
   chargeback rates directly.

## Recommendation & monitoring plan

Roll out to 100% **with a kill switch**, monitoring weekly:

- Delivered-rate by installment bucket (1 / 2-3 / 4-6 / 7+): a drop concentrated in 7+ is the
  credit-risk signature; **rollback trigger: guardrail CI excludes zero on the downside.**
- Basket-mix shift: AOV lift should come from bigger baskets, not from fewer small orders.
- Payment-failure proxy (orders canceled before shipment) by arm during any holdback period.
