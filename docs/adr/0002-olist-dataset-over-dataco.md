# ADR-0002: Olist dataset over DataCo

- **Status:** accepted
- **Date:** 2026-06-09
- **Deciders:** Tirth Joshi

## Context

This project needs a dataset that supports credible funnel metrics, cohort logic, and a
simulated A/B test. The sibling supply-chain repo used DataCo and hit a wall: after leakage
removal, a single categorical feature dominated the outcome, producing a weak business story.
We did not want to repeat that.

## Decision

Use the Olist Brazilian E-Commerce dataset (~99k real orders across orders, items, payments,
customers, sellers, products).

## Options considered

- **Chosen — Olist:** real multi-table relational model → credible joins, funnels, cohorts;
  large enough to power a simulated A/B; timestamps support cohort windows.
- **DataCo:** rejected — weak semantics, single-feature dominance, already used in a sibling
  repo. Reusing it would duplicate the weakness, not add a new skill.
- **Fully synthetic data:** rejected — not credible for a portfolio piece; defeats the point
  of demonstrating work on real, messy data.

## Consequences

Real relational data with genuine quirks (multi-payment orders, right-censored tail months) —
which the EDA surfaced and turned into design decisions. Olist has no native A/B column, so the
experiment must be simulated (see ADR-0004). Raw CSVs are gitignored; only schema docs commit.

## Links

`CONTEXT.md` §3 (Why Olist), `reports/eda_gate.md`, `../../PORTFOLIO_LOCKED_DECISIONS.md`.
