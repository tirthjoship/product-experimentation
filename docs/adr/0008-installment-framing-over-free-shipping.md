# 0008 — Installment-expansion framing over free-shipping threshold

**Status:** accepted (2026-06-11)

## Context

The pipeline was statistically credible but had no product story: a generic "simulated AOV
lift" with no hypothesis a PM would recognize. Plan 3 adds the narrative layer (decision memo).
That requires picking the fictional product change the experiment simulates. The earlier
default — a free-shipping-threshold change — was questioned by the user: it overlaps the
freight/logistics domain owned by the sibling `supply-chain-optimization-ml` project.

## Options

1. **Free-shipping threshold change** — fits AOV mechanics and the freight covariate, but
   collides with the supply-chain project's domain; portfolio reads as two freight projects.
2. **Installment-expansion test (chosen)** — raise the interest-free installment cap 6x→10x.
   Dataset-native: `order_payments.payment_installments` is real; measured in the cohort
   window, ~half of orders use >1 installment and credit cards carry ~3/4 of payment value
   (exact committed numbers: `reports/installment_motivation.json`). The delivered-rate
   guardrail becomes load-bearing (credit risk → cancellations). Customer-level assignment
   matches an offer rollout. Zero overlap with any sibling repo.
3. **Cross-sell bundle module** — recsys-adjacent; collides with the stock-recommender's
   "recommendation" identity.
4. **Tiered minimum-spend coupon** — discount confounds revenue vs AOV; weakens the guardrail
   logic.

## Decision

Option 2. The injected effect, assignment, seed, cohort, metrics, and inference are unchanged —
the framing is narrative + docs + one descriptive artifact. Portfolio separation is recorded on
both sides (supply-chain repo: `docs/FUTURE_ENHANCEMENTS.md` bans causal/uplift work there;
this repo stays out of freight/logistics).

## Consequences

- `freight_value` remains the ANCOVA covariate but is a statistical detail, not the story.
- The memo (`reports/experiment_001_readout.md`) quotes only committed-artifact numbers,
  enforced by `tests/test_readout_integrity.py`.
- Motivation stats are descriptive and must never be presented as effect estimates.
- D7 repeat stays exploratory (~3% ever-repeat).
