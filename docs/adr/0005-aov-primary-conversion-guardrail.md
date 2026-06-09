# ADR-0005: AOV primary, conversion guardrail, D7 exploratory

- **Status:** accepted
- **Date:** 2026-06-09
- **Deciders:** Tirth Joshi

## Context

CONTEXT originally listed conversion, AOV, and D7 repeat as co-equal primary metrics. The EDA
measured what each can actually carry:

- **Conversion (delivered rate) = 97.02%.** A ceiling. At n ≈ 49.6k/arm its MDE is a tight
  0.30pp, so it is *powerable* — but semantically it is fulfillment success, not checkout
  conversion, so calling it the headline metric would misrepresent it.
- **AOV** is continuous, right-skewed (mean 160.99 BRL, median 105.29), MDE 3.95 BRL (2.45%
  relative). Sensitive and meaningful.
- **D7-within-7-days = 0.214%** (only 206 of 96,096 persons). Too sparse for inference.

## Decision

AOV is the primary metric and receives the injected effect. Conversion is a guardrail (confirm
treatment does not hurt delivery). D7 repeat is exploratory — reported per variant with no test.

## Options considered

- **Chosen — AOV primary + guardrails:** mirrors real product-experiment structure (one
  primary, conversion as guardrail, D7 watched); avoids a ceiling metric as headline.
- **Conversion primary:** rejected — 97% ceiling, semantically fulfillment, weaker product story.
- **AOV-only:** rejected — drops a cheap, informative guardrail.
- **Conversion + AOV co-primary:** rejected — adds multiple-comparison correction for little
  gain and reintroduces the ceiling metric as headline.

## Consequences

The experiment report has a clear hierarchy: AOV with bootstrap CI + p-value, conversion with a
guardrail flag, D7 as a watched number. The metric definitions are promoted to `docs/METRICS.md`.

## Links

`reports/eda_gate.md` (power/MDE table), ADR-0004, ADR-0006,
`docs/superpowers/specs/2026-06-09-metrics-and-experiment-design.md`.
