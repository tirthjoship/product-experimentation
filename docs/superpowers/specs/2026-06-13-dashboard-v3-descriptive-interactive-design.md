# Dashboard v3 — Descriptive & Interactive (design spec)

**Date:** 2026-06-13
**Status:** approved (brainstorming), pre-plan
**Builds on:** Plan 5 dashboard v2 (`feat/plan5-dashboard`, commit `db453b6`) — read-only
Streamlit + Plotly over committed `reports/*.json`.
**Related:** `docs/superpowers/specs/2026-06-12-plan5-dashboard-design.md` (v2),
CLAUDE.md rules (#1 no invented metrics, #2 simulated must be labeled, #3 fixtures only).

## Problem

The v2 dashboard is correct but terse. A reader **new to the org** — a PM who did not
build the analysis — cannot reconstruct *what* each chart says or *why* the verdict is
what it is. The asks: (1) more descriptive / plain-language, (2) more interactive —
hover detail and adjustable inputs that show the project's reasoning live.

## Goal

Turn the dashboard into something a new-to-org PM can read top-to-bottom and *understand*
the experiment, the decision rule, and the sensitivity of both — without prior context and
without reading code. Add genuine interactivity (hover + adjustable inputs) **without
breaking the read-only, no-invented-metrics architecture**.

## Non-goals

- No live recompute against Olist inside the app (rejected approach B — would break the
  read-only lock, load full data in the app, and risk Community Cloud OOM).
- No new statistical methods. Reuse the existing `src/experiment/*` engine verbatim.
- No change to the committed `reports/*.json` produced by the existing pipeline (the grid
  is an *additional* report, not a rewrite).

## Honesty constraints (locked)

The whole project is a **labeled simulated experiment** — variants assigned by hashed
`customer_unique_id` (seed 42); the treatment effect is a synthetic injection. The three
committed scenarios (adverse −5% / null 0% / large +5%) are three points of that same
injection method.

1. **No invented metrics.** Every number shown traces to a committed `reports/*.json`
   (existing reports + the new `experiment_grid.json`) OR is a transparent analytical
   formula clearly labeled as a calculator (not an experiment result).
2. The **What-if** simulated slider reads precomputed grid points (same injection method,
   more points) — it does NOT generate numbers in the browser. Carries a persistent
   "SIMULATED — synthetic injection" banner.
3. The **Power calculator** is analytical (closed-form `mde_mean`/`mde_proportion`).
   Carries a persistent "CALCULATOR — analytical, not experiment output" label.

## Structure — 4 tabs (read → play escalation)

```
Story            narrative; the SHIP decision, motivation, DiD honest-rejection. + richer hover + plain-English captions.
Explore scenarios  the 3 committed scenarios (adverse/null/large), now with deep hover + "what this means" panels.
What-if          simulated-outcome slider over reports/experiment_grid.json (snaps to nearest grid point).
Power calculator analytical: slide n / α / SD / power → MDE, CI half-width, power. Pure formulas.
```

Each tab opens with a one-line **"what this answers"** header for a new PM. Glossary
tooltips (AOV, CI, MDE, ANCOVA, guardrail, pre-trends) appear where each term first shows.

## Section detail

### 1. Explanatory layer (applies to all tabs)

- **Rich hover** via Plotly `hovertemplate` on every chart:
  - bucket bar: AOV value + bucket label + share of orders.
  - forest rows: point estimate, CI low/high, adjusted-vs-unadjusted, variance-reduction.
  - guardrail: delta + "indistinguishable from zero" framing.
  - pre-trends coef plot: per-lead coefficient + whether it breaches the band.
- **Plain-English caption** under each chart — one jargon-free sentence. Example:
  "Treatment customers spent about R$6 *less* on average; we're 95% confident the true
  drop is between R$3 and R$9."
- **Glossary** — single source `dashboard/glossary.py` (dict: term → one-line definition),
  rendered through Streamlit `help=`/`?` affordances. No term defined in two places.
- **"What this answers" header** per tab (one line).

### 2. What-if tab (simulated grid)

- **Offline script** `scripts/build_experiment_grid.py`: calls existing
  `run_scenarios(df, grid)` with effects from −10% to +10% in 1% steps (21 points),
  writes `reports/experiment_grid.json`.
- **Report schema** (`experiment_grid.json`) — a list; each element:
  `{ effect, lift, ci, p, aov_adjusted: {lift, ci, ci_width_ratio}, verdict,
  guardrail: {delta, ci} }`. (Mirror the per-scenario shape already in
  `experiment_scenarios.json` so charts/types are reused.)
- **Dashboard**: a slider (−10…+10%, step 1) **snaps to the nearest grid point**; the
  forest plot, verdict chip, and guardrail update from that point.
- **Loader** `load_grid()` in `data.py` — typed, fail-loud (`ReportSchemaError` on
  missing/malformed field), same pattern as existing loaders.
- **Label**: persistent "SIMULATED — synthetic injection, same method as the committed
  scenarios" banner (reuse v2 simulated-banner style).

### 3. Power calculator tab

- **Inputs**: n per arm, α, baseline SD (default seeded from a committed report), power
  target — Streamlit number inputs / sliders.
- **Outputs (live)**: MDE (via `mde_mean`), CI half-width, power at the observed effect.
  Plus a small **MDE-vs-n** sensitivity curve (Plotly).
- **Pure**: no data load; calls `src/experiment/power.py` functions only.
- **Label**: persistent "CALCULATOR — analytical, not experiment output."

### 4. Architecture & testing

- **Pure layer is the source of truth, keeps the 90% gate:**
  - new chart builders → `dashboard/charts.py`
  - new loaders + types → `dashboard/data.py`
  - glossary → `dashboard/glossary.py`
- **Render-only glue (coverage-omitted):** `dashboard/app.py`, `dashboard/sections/*`.
  - new: `sections/whatif.py`, `sections/calculator.py`
  - enriched: `sections/scenarios.py` (→ Explore), `results.py`, `motivation.py`,
    `guardrail.py`, `did.py`, `hero.py` (hover + captions).
- **Per-section error isolation** preserved (existing `_render` try/except, incl.
  `ValueError`).
- **Tests — fixtures only, never full Olist:**
  - tiny `experiment_grid.json` fixture (a few effect points).
  - `build_experiment_grid.py` gets a fixture-based test (small injected df → expected
    grid shape + monotonic-ish lift sanity).
  - calculator builders tested against hand-computed `mde_mean` values.
  - new loaders tested incl. root-shape + missing-field guards (match existing rigor).
- **Schema-drift guard:** extend `scripts/dashboard_smoke.py` to load and validate
  `experiment_grid.json`; CI `dashboard-smoke` job already runs it.

## Data flow

```
src/experiment/run_scenarios ──(offline, grid of effects)──► reports/experiment_grid.json
src/experiment/* (existing) ───(offline, as today)─────────► reports/{experiment_scenarios,installment_motivation,did_feasibility,...}.json
                                                                      │
                                                          dashboard/data.py (typed, fail-loud loaders)
                                                                      │
                                          dashboard/charts.py (Plotly builders) + glossary.py
                                                                      │
                              dashboard/sections/* (render-only) ──► dashboard/app.py (4 tabs)

src/experiment/power.py ──(pure formulas, no data)──► dashboard/charts.py (calculator) ──► sections/calculator.py
```

## Error handling

- Missing/malformed report field → `ReportSchemaError` (fail loud, never a default).
- Per-section try/except keeps one broken section from blanking the app.
- Calculator inputs are bounded (slider/number-input ranges) so formulas can't receive
  invalid (e.g. n≤0, α∉(0,1)).

## Risks / open items

- Grid step granularity: 1% (21 points) chosen for "feels continuous" vs report size.
  Adjustable if the file gets large.
- Default baseline SD for the calculator must come from a committed report, not be
  hard-coded, to honor rule #1.
- Branch decision (extend `feat/plan5-dashboard` vs new branch off it) — to confirm at
  plan time.
