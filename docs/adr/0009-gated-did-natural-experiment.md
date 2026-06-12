# 0009 — Gated DiD natural experiment, and its honest rejection on Olist

**Status:** accepted (2026-06-11)
**Deciders:** Tirth Joshi

## Context

Plans 1–3 deliver a *simulated* RCT: assignment is hashed, the effect is injected, the truth
is known. That demonstrates inference mechanics but never observational-causal judgment — the
harder, more credible skill. Plan 4 (P4 in the Phase-2 roadmap) attempts a real
difference-in-differences (DiD) estimate from a natural experiment in Olist.

Olist has no documented product intervention, so a DiD must lean on an external calendar shock
with differential regional exposure. The central risk is **manufacturing** a causal claim by
scanning the data for a break and back-fitting a story. The defense is a pre-registered gate
decided before post-period outcomes are seen, with the discovery process firewalled.

## Options considered

1. **Free observational EDA, pick the cleanest break, document honestly** — rejected: loses the
   pre-registration showcase; the result reads exploratory, not confirmatory.
2. **Fix one event a priori (e.g. truckers' strike)** — rejected: the outcome and arms depend
   on the shock type; a blind a-priori lock risks mis-specifying the outcome.
3. **Gated discovery with a firewalled catalog (CHOSEN)** — enumerate externally dated
   candidate events from public record (no data touched), pre-register hypothesis + outcome +
   donut assignment per candidate, run outcome-blind feasibility (pre-period counts only), then
   a 4-condition gate. **A documented rejection is a valid, valued deliverable.**

## Decision

Build the gated pipeline (`src/did/`): frozen event catalog committed before any query;
code-enforced post-period blinding (post-boundary rows are unobtainable without a *genuine*
committed GO verdict — `require_go` checks every gate condition actually passed, not merely the
`"GO"` string); TWFE estimator with state-clustered SEs; event-study pre-trends (joint Wald +
magnitude band); deterministic verdict JSON (no timestamp — git is the timestamp).

**Pre-registered gate — all four must hold:** (1) dated boundary from public record;
(2) treated/control states defined by geography only (donut design: high-exposure bloc /
low-exposure bloc / excluded middle); (3) parallel pre-trends — joint Wald p > 0.10 **and**
every lead within ±0.25 pre-period SD (two-sided so noisy cells can't pass vacuously);
(4) adequate n — ≥1,000 pre orders/arm, ≥80% of week-cells ≥20 orders, ≥5 states/arm.

## Outcome on Olist: REJECTED (and that is the result)

Phase B feasibility (outcome-blind) on the truckers'-strike-2018 candidate
(treated = North+Northeast, control = Southeast+South, excluded = Center-West) returned
**FAIL** on two of the four conditions — exact committed numbers in
`reports/did_feasibility.json`:

- **adequate_n: FAIL.** Only **45.0%** of treated×week cells reach ≥20 orders (threshold 80%).
  The North/Northeast is too thin in Olist: 3,604 treated pre-period orders vs 27,884 control,
  16 vs 7 states. (The ≥1,000/arm and ≥5-states/arm sub-criteria pass; the week-cell density
  is what breaks.)
- **parallel_pretrends: FAIL.** Joint Wald **p = 0.018** (< 0.10) and max lead **3.40 > band
  1.93** — pre-trends visibly diverge before the event, so the parallel-trends assumption is
  not credible.

Per protocol, **no estimate is computed.** The deliverable is the documented rejection. This
is the intended showcase: the discipline to walk away from an under-identified causal claim
rather than ship a number.

## Consequences

- The natural-experiment artifact for the portfolio is a *rejection* memo, not a DiD estimate
  — explicitly a valid exit (and arguably the stronger judgment signal).
- Infrastructure is reusable: a future GO requires either a denser geography (the sparsity is
  fundamental to Olist's North/Northeast), or a `log_orders` volume outcome (avoids the
  delivery-cell NaN selection channel named in the report threats section), plus genuinely
  parallel pre-trends. Both are noted as extensions, not built.
- Blinding is enforced by code + tests (forged-verdict regression tests), not by convention —
  hardened after an integrity audit found `require_go` originally accepted a 2-key blob.
- `min_detectable_lead` is reported for transparency (it can exceed the band, i.e. the test can
  be underpowered) but is not itself a gate criterion; the gate is Wald + magnitude band.

## Links

- `docs/superpowers/specs/2026-06-11-plan4-did-natural-experiment-design.md` — design
- `docs/superpowers/specs/2026-06-11-plan4-event-catalog.md` — Phase A pre-registration
- `reports/did_feasibility.{md,json}` — the committed FAIL artifact
- ADR-0004 (simulated RCT — the contrast this plan completes)
