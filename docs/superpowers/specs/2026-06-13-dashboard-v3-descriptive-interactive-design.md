# Dashboard v3 — Descriptive & Interactive (design spec)

**Date:** 2026-06-13
**Status:** approved (brainstorming + clickable-mockup sign-off), pre-plan
**Builds on:** Plan 5 dashboard v2 (`feat/plan5-dashboard`, commit `db453b6`) — read-only
Streamlit + Plotly over committed `reports/*.json`.
**Reference mockup:** `docs/mockups/dashboard-v3/index.html` (clickable HTML, real report
numbers; the implementation should match its structure, copy, color logic, and chart choices).
**Related:** v2 spec `docs/superpowers/specs/2026-06-12-plan5-dashboard-design.md`;
ADRs 0002/0004/0005/0006/0007/0008/0009; CLAUDE.md rules (#1 no invented metrics, #2 simulated
labeled, #3 fixtures only).

## Problem

The v2 dashboard is statistically correct but terse: a reader **new to the org** — a PM who did
not build the analysis — cannot reconstruct what each chart says, why a verdict holds, why we
chose the methods/metrics we did, or whether a number is good or bad. It also under-represents
the work: three outcome metrics, covariate adjustment, power analysis, and a full DiD gate exist
in the reports but only AOV was surfaced.

## Goal

A dashboard a non-technical decision-maker can read top-to-bottom and *act on*: every tab states
its real question in plain words and gives a verdict; every metric and method explains itself on
hover; numbers and charts are color-coded good/average/poor; and the design reflects the actual
depth of analysis — all while preserving the read-only, no-invented-metrics architecture.

## Non-goals

- No live recompute against Olist in the app (rejected: breaks read-only, loads full data, OOM
  risk on Community Cloud).
- No new statistics. Reuse `src/experiment/*` (`run_scenarios`, `power.py`) verbatim.
- No change to existing committed reports. The What-if grid is an *additional* report.

## Honesty constraints (locked)

The whole project is a labeled **simulated** experiment (hashed `customer_unique_id`, seed 42;
synthetic injected effect). The three committed scenarios (adverse −5% / null 0% / large +5%)
are three points of that same method.

1. **No invented metrics.** Every number traces to a committed `reports/*.json` (existing +
   new `experiment_grid.json`) OR is a transparent analytical formula labeled as a calculator.
2. **What-if** reads precomputed grid points (same injection method, more points) — never
   generates numbers in the browser. Persistent "SIMULATED — synthetic injection" banner.
3. **Power calculator** is analytical (`mde_mean`/`mde_proportion`). Persistent "CALCULATOR —
   analytical, not experiment output" label.
4. **Color thresholds** (good/average/poor) are interpretation, not new metrics, but must be
   defensible and defined in one place (see §Color logic) and documented.

## Visual system

- **Theme (de-AI'd, user-chosen):** white background; **Space Grotesk** display/headings;
  **Inter** body; **IBM Plex Mono** for numbers/labels; single accent **oxblood `#7a1f2b`**
  (kickers, active tab, links, range-plot adjusted bar). Semantic verdict palette:
  green `#2f7d4f` (SHIP/good), amber `#b7791f` (NEED MORE DATA/average), red `#b3261e`
  (DO NOT SHIP/poor), slate `#5c6b7a` (neutral/guardrail/descriptive).
- **In Streamlit:** custom fonts + headline styling via `st.markdown` CSS injection (Google
  Fonts import); Plotly figures themed to match. (Note: keep CSS injection contained and
  documented; v2's pure/render split still applies.)
- **Responsive:** no horizontal scroll at any width (phone / half-screen / full). Use Streamlit
  `st.columns` that collapse on narrow screens; Plotly figures use autosize/`width="stretch"`
  (the Streamlit equivalent of the mockup's `min-width:0` + responsive-resize fix). The tab
  strip scrolls horizontally on phone rather than forcing page width.

## Structure — persistent header + 5 tabs

**Header (persistent, above tabs):** eyebrow "Product Experimentation · Olist E-Commerce";
title "Should we raise the installment cap from 6× to 10×?"; one-paragraph plain-language
subtitle; context **chips** — Dataset · Method · SIMULATED · Metrics · Plans-shipped — each
with an **ⓘ hover cloud stating what it is + why chosen + what was rejected** (sourced from
ADRs; see §Chip rationale).

Each tab opens with a one-line *"what this answers"* and a **bottom-line tile** (plain-language
question + verdict chip + concrete interpretation in the "$X invested → Y% probability" style).

1. **Overview** — verdict hero; motivation KPIs (color-coded) + bucket bar; headline AOV forest
   (adjusted dot colored by verdict).
2. **Experiment results** — all 3 outcomes: AOV forest (unadj vs adj, verdict-colored) +
   variance-reduction range-plot; conversion guardrail (lift-vs-zero forest); D7 guardrail
   (dumbbell); sample sizes (split balance bar); baseline balance (diverging diamond + band).
3. **Scenario explorer** — radio over the 3 committed scenarios → live verdict chip + colored
   metric values + AOV/conversion/D7 small-multiples + live bottom-line tile; then **What-if**
   slider (−10%…+10%, snaps to grid) → verdict + colored forest.
4. **Power & design** — calculator (n / α / SD / power → MDE, CI half-width, power@observed,
   color-coded) + MDE-vs-n curve + power-vs-effect curve.
5. **Natural experiment (DiD)** — bottom-line tile (honest rejection); 4-condition gate
   checklist with detail; pre-trends coef plot + band (out-of-band leads red); sample adequacy
   (dumbbell); state geography (split bar).

## Explanatory layers (all tabs)

- **Chip rationale tooltips** (header) — see §Chip rationale.
- **Bottom-line tile** per tab — plain question + verdict + concrete interpretation; the
  Scenario tile updates live with the radio.
- **Chart ⓘ tooltips** — every chart has an info icon: "what this shows + how to read it"
  (incl. how color maps to verdict).
- **Glossary hovers** — every metric term/label (AOV, CI, MDE, raw/adjusted lift, θ,
  conversion, D7, power, α, pre-trends, guardrail) has a one-line definition; single source
  `dashboard/glossary.py`.
- **Color-coded values** — KPIs and metric numbers carry a value-color class + optional word
  tag (e.g. "strong"). See §Color logic.

## Chip rationale (from ADRs — accurate, not invented)

- **Dataset = Olist** (ADR-0002): ~99k real relational orders; chosen over DataCo (weak
  semantics, sibling-repo reuse) and synthetic (not credible).
- **Method = ANCOVA on `freight_value`** (ADR-0007): r=0.484 → ~23% variance reduction;
  CUPED rejected (97% one-time buyers → no pre-period signal); item-count covariate deferred.
- **SIMULATED** (ADR-0004): no native A/B column → hashed assignment seed 42 + labeled +5%
  injection; null version kept as A/A check.
- **Metrics = AOV primary / Conversion guardrail / D7 exploratory** (ADR-0005): AOV continuous
  & sensitive (~2.45% MDE); conversion near 97% ceiling → guardrail only; rejected
  conversion-primary and co-primary.
- **Inference** (ADR-0006, optional chip): bootstrap CI (10k, seed 42) + Welch + two-prop z.

## What-if grid

- **Offline script** `scripts/build_experiment_grid.py`: calls `run_scenarios(df, grid)` with
  effects −10%…+10% @ 1% (21 points) → `reports/experiment_grid.json`.
- **Schema** (list; per element): `{ effect, lift, ci, p, aov_adjusted:{lift, ci,
  ci_width_ratio}, verdict, guardrail:{delta, ci} }` — mirrors `experiment_scenarios.json`
  element shape so chart/types reuse.
- **Loader** `load_grid()` in `data.py` — typed, fail-loud (`ReportSchemaError`).
- Slider snaps to nearest grid point; persistent SIMULATED banner.

## Color logic (single source, documented)

- **Verdict** (CI vs zero): all-above → SHIP/green; all-below → DO NOT SHIP/red; straddles →
  NEED MORE DATA/amber. Applied to verdict chips and primary AOV forest dots.
- **Value coloring:** lift values take the verdict color; power ≥0.80 green / 0.50–0.80 amber /
  <0.50 red; MDE green when effect is detectable (|adjusted lift| ≥ MDE) else amber; motivation
  KPIs favorable→green (high installment share / cc share / large cohort). Guardrails &
  descriptive context stay slate.
- Thresholds live in one module (e.g. `dashboard/verdict.py` or constants) and are unit-tested.

## Chart inventory (~16, all report-backed)

forest (AOV unadj/adj, conversion lift) · range-plot (CI shrink) · dumbbell (D7, sample
adequacy) · split bar (sample sizes, geography) · diverging diamond (balance) · bucket bar
(motivation) · line (MDE-vs-n, power-vs-effect) · coef plot + band (pre-trends). New Plotly
builders added to `dashboard/charts.py`.

## Architecture & testing

- **Pure layer = source of truth, keeps 90% gate:** new builders → `charts.py`; loaders/types
  → `data.py`; glossary → `glossary.py`; color/verdict thresholds → `verdict.py` (or constants).
- **Render-only glue (coverage-omitted):** `app.py`, `sections/*`. New: `sections/whatif.py`,
  `sections/calculator.py`; rework `overview/results/scenarios/power/did` sections + header.
- **Per-section error isolation** preserved (try/except incl. `ValueError`).
- **Tests — fixtures only, never full Olist:** tiny `experiment_grid.json` fixture;
  `build_experiment_grid.py` fixture test (shape + monotonic-ish lift); calculator builders vs
  hand-computed `mde_mean`; verdict/color thresholds unit-tested; loaders incl. root-shape +
  missing-field guards.
- **Schema-drift guard:** extend `scripts/dashboard_smoke.py` to validate `experiment_grid.json`;
  CI `dashboard-smoke` already runs it.

## Data flow

```
src/experiment/run_scenarios ─(offline, effect grid)─► reports/experiment_grid.json
src/experiment/* (existing)  ─(offline)──────────────► reports/{experiment_scenarios,installment_motivation,did_feasibility,...}.json
src/experiment/power.py      ─(pure formulas)─────────► dashboard/charts.py (calculator)
                                  │
                       dashboard/data.py (typed, fail-loud) + glossary.py + verdict.py
                                  │
                       dashboard/charts.py (Plotly builders)
                                  │
            dashboard/sections/* (render-only) ──► dashboard/app.py (header + 5 tabs)
```

## Error handling

- Missing/malformed field → `ReportSchemaError` (never a default).
- Per-section try/except keeps one broken section from blanking the app.
- Calculator inputs bounded by widget ranges (n>0, α∈(0,1), power∈(0,1)).

## Risks / open items

- Grid step 1% (21 pts) chosen for "feels continuous" vs file size — adjustable.
- Calculator default SD must come from a committed report (rule #1), not hard-coded.
- CSS injection for fonts/theme is a larger surface than v2 — keep it in one place, documented;
  verify it degrades gracefully if a font fails to load.
- Branch: extend `feat/plan5-dashboard` (one PR for the dashboard) vs new branch off it — confirm
  at plan time. Current lean: extend, since v2 is not yet PR'd.
