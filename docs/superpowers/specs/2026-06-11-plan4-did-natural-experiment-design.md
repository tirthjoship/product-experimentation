# Plan 4 — Gated DiD Natural Experiment — Design Spec

**Date:** 2026-06-11
**Series:** Plan 4 of 4 (final analytical plan). Predecessors: Plan 1 (inference depth),
Plan 2 (covariate adjustment), Plan 3 (installment narrative + PM memo).
**Parent roadmap:** `2026-06-09-phase2-roadmap-design.md` §P4 (calendar-shock × region DiD,
pre-registered gate, rejection-is-valid).

## 1. Goal

Produce a natural-experiment artifact on Olist: a difference-in-differences estimate of a
calendar shock's effect, identified by differential regional exposure — **or** a documented,
pre-registered rejection explaining which identification assumption failed. Either exit ships.
This demonstrates observational-causal judgment, the skill the simulated A/B test (Plans 1–3)
cannot show.

## 2. Honesty frame (why gated)

Olist has no documented product intervention. Classic DiD needs a dated treatment. The danger
is manufacturing a causal claim by scanning the data for a break and back-fitting a story.
The defense is a **pre-registered gate decided before post-period outcomes are seen**, with
the discovery process firewalled (§4–§5). A FAIL verdict is an explicitly valued deliverable:
`reports/natural_experiment_feasibility.md` = REJECTED + which condition broke.

## 3. Locked decisions (brainstorm 2026-06-11)

| Decision | Choice | Rejected alternatives |
|---|---|---|
| Event selection | EDA discovery, firewalled by event catalog + outcome-blind feasibility | Fixing truckers' strike a priori; free EDA with honest documentation |
| Outcome registration | Per-event in catalog, declared before any data access | Single event-agnostic outcome; multiple corrected co-primaries |
| Estimator | TWFE OLS + cluster-robust SE (state) + event-study leads/lags | 2×2 means + house BCa bootstrap; wild cluster bootstrap |

## 4. Phase A — Event catalog (no data access)

Written from public record only, before any query runs. 3–5 externally dated candidate
events within the usable data window (§10). Each entry declares:

- **Event + date boundary** (citable public source).
- **Mechanism** — why it should move behavior.
- **Hypothesis**: primary outcome + expected sign (e.g. truckers' strike May 21–30 2018 →
  `delivery_days` ↑; Black Friday Nov 24 2017 → weekly order volume ↑).
- **Assignment rule**: treated vs control states defined by geography/timing only (e.g.
  freight distance from Southeast hubs), never by the outcome.
- **Known confounds** (seasonality collisions, concurrent events).

Candidate starting set: truckers' strike (May 2018), Black Friday (Nov 2017), Carnival
(Feb 2018), Brazilian postal tariff/strike events if a dated source exists. The catalog may
score a candidate as non-viable on paper (e.g. national exposure → no control group) without
touching data.

Artifact: `docs/superpowers/specs/2026-06-11-plan4-event-catalog.md` (committed before
Phase B code runs; git history is the timestamp).

## 5. Phase B — Feasibility EDA (outcome-blind)

SQL/DuckDB on state×week cells. **May look at:** pre-period order counts, data coverage by
state and week, missingness of fields the catalog entries need, delivery-field availability.
**Must not look at:** any outcome × event-window cross-tabulation, outcome trends around
candidate boundaries, or anything that ranks candidates by apparent effect.

**Volume-outcome caveat:** when a candidate's primary outcome is order volume, post-period
cell counts ARE the outcome. Feasibility therefore evaluates counts on the **pre-period
only** for all candidates; post-period adequacy is checked after unblinding (§6 condition
4a) and a shortfall there is documented as a FAIL-at-unblinding, not silently patched.

Output: `reports/did_feasibility.{md,json}` — per-candidate cell-count tables and a selection
(or rejection of all candidates) justified only by feasibility criteria.

**Blinding mechanics (code-enforced):** `src/did/panel.py:build_panel()` takes the chosen
event definition and by default excludes all rows with `order_purchase_timestamp` on/after
the event boundary. The unblinded panel is only constructible when a committed gate-verdict
artifact (`reports/did_gate_verdict.json`) exists with `verdict == "GO"` (§7). Tests assert
this raises otherwise.

## 6. Phase C — Pre-registration lock

One commit containing: chosen event, primary outcome, assignment rule (explicit state lists),
estimation window, and the gate thresholds below. After this commit, no parameter changes.

**Gate — ALL four conditions, operationalized:**

1. **Dated boundary** — event date from public record, cited in catalog.
2. **Exogenous assignment** — treated/control state lists derive from a geographic rule
   written in Phase A, mechanically applied (no outcome input).
3. **Parallel pre-trends** — event-study on the pre-period (§8): joint Wald test that all
   lead coefficients (≥3 leads) are zero; gate passes iff p > 0.10.
4. **Adequate n** — all of: (a) each pre-period DiD cell (treated/control) has ≥1,000
   orders per feasibility counts, with post-period cells re-checked against the same
   threshold after unblinding (§5 caveat); (b) ≥80% of pre-period group×week cells have
   ≥20 orders; (c) ≥5 states per arm (cluster-robust SE reliability).

Conditions 1, 2, 4(pre) are decidable from Phases A–B without outcomes. Condition 3 uses
pre-period outcomes only.

## 7. Phase D — Gate evaluation

`src/did/gate.py` evaluates all four conditions and writes
`reports/did_gate_verdict.json` (`{verdict: GO|FAIL, conditions: {...}, computed_at, seed}`)
plus a human-readable section in the final report. The verdict file is committed; it is the
key that unlocks post-period data in `panel.py`.

## 8. Estimator

- **Panel:** state×week, weekly buckets, estimation window per catalog entry.
- **DiD spec:** `y_st = β·(treated_s × post_t) + α_s + γ_t + ε_st`, OLS via statsmodels,
  `cov_type="cluster"` clustered on state. β is the headline estimate, with 95% CI.
- **Event-study spec:** `y_st = Σ_{k≠−1} β_k·(treated_s × 1[t=k]) + α_s + γ_t + ε_st`,
  relative-week indicators. Pre-period leads feed the gate Wald test (computed on pre-period
  data only); full lead/lag plot is a report figure after GO.
- Volume outcomes modeled in logs (`log(orders_st)`); delivery outcomes in natural units.
- Nothing stochastic in OLS; any resampling added later pins `seed=42`.

## 9. Phase E — Exits (both ship)

- **GO** → `reports/experiment_002_did.md` + `.json`: DiD estimate, CI, event-study figure,
  gate evidence, threats-to-validity section (spillovers, composition shifts, SUTVA).
  Memo↔JSON integrity test à la Plan 3 (`tests/test_did_readout_integrity.py`).
- **FAIL** → `reports/natural_experiment_feasibility.md`: REJECTED verdict naming the broken
  condition(s), with the evidence table. No estimate is computed or reported.

## 10. Data window & panel

- Usable window: **Jan 2017 – Aug 2018** (drop sparse Sep–Dec 2016 head and Sep–Oct 2018
  tail, both known-thin in Olist).
- Unit: customer state (27) × ISO week. Aggregates from `orders` + `order_items` +
  `customers` (+ delivery timestamps for logistics outcomes).
- SQL in `sql/did/*.sql`; same DuckDB pattern as `sql/eda/installments*.sql`.

## 11. Architecture

```
src/did/
  catalog.py    # typed event definitions (frozen dataclasses): dates, outcome, assignment rule
  panel.py      # DuckDB → state×week panel; post-period blinding enforced here
  estimator.py  # TWFE DiD + event-study; statsmodels wrapper; typed results
  gate.py       # evaluates 4 conditions → verdict JSON
  report.py     # md/json writers (house style from report/installment_motivation.py)
sql/did/        # panel + feasibility queries
```

- Make targets: `make did-feasibility` (Phase B artifact), `make did-gate` (Phase D),
  `make did` (Phase E, requires GO verdict). All run via `.venv/bin/python -m ...`.
- New dependency: `statsmodels` (pinned in `pyproject.toml`).
- mypy strict; structured logging; no prints.

## 12. Testing strategy (fixtures only — never full Olist)

- **Synthetic panel fixtures**: generator with known state/week FE + injected DiD effect →
  estimator must recover β within tolerance; zero-effect fixture → CI covers 0.
- **Gate fixtures**: parallel-trends panel → condition 3 passes; diverging-trends panel →
  fails; cell-count fixtures around the n thresholds → condition 4 boundary behavior.
- **Blinding tests**: building unblinded panel without GO verdict raises; with FAIL verdict
  raises.
- **Hypothesis property tests**: DiD estimate invariant to adding state-constant or
  week-constant shifts to the outcome.
- **Integrity tests**: every headline number in the shipped report matches committed JSON.
- Coverage gate stays ≥90%; CI unchanged otherwise.

## 13. Out of scope

- Synthetic control, staggered-adoption estimators (Callaway–Sant'Anna), wild cluster
  bootstrap — noted as extensions in the report, not built.
- Dashboard integration of DiD results (belongs to roadmap P2 if it happens).
- Any second event after the first GO/FAIL cycle completes.

## 14. Success criteria

- Event catalog committed before any Phase B query ran (verifiable in git history).
- A gate verdict JSON + exactly one of the two exit reports exists and is committed.
- Post-period blinding is code-enforced and tested.
- All numbers in shipped reports trace to committed JSON (integrity test green).
- `make check` green: mypy strict, ≥90% coverage, all tests on fixtures.
