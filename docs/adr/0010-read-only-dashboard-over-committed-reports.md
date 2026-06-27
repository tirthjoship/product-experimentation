# 0010 — Read-only dashboard over committed reports (no live compute)

**Status:** accepted (2026-06-13)
**Deciders:** Tirth Joshi

## Context

Plans 1–4 produce deterministic artifacts (`reports/*.json` + `.md`) whose every number traces
to a seeded run. A dashboard is the portfolio's public face, so its central risk is **drift**:
a UI that recomputes statistics can silently diverge from the committed results, or worse,
invent numbers the reports never produced. The non-negotiable project rule (ADR
[0004]) is *no invented metrics* — every figure shown must already exist in a committed report
or be a clearly-labeled analytical formula. The dashboard must also stay cheap to test (the 90%
coverage gate) without forcing UI glue through unit tests.

## Decision

Build a **read-only** Streamlit + Plotly dashboard (`dashboard/`) that loads committed
`reports/*.json` and never runs the experiment. Verdicts are READ from each report's
`recommend()` output — the dashboard maps verdict→color, it never re-derives the ship rule.
Split the code into a **pure layer** (`data.py` typed loaders, `charts.py` figure builders,
`theme.py`, `glossary.py`, `valuecolor.py`) that carries all logic and keeps the 90% gate, and a
**render-only layer** (`sections/*`, `app.py`) that is coverage-omitted glue.

Interactivity is honest, not live: the **What-if** tab reads a precomputed
`reports/experiment_grid.json` (21 points, effect −10..+10%) built offline by
`scripts/build_experiment_grid.py`, which *reuses the real* `run_scenarios` + `results_to_json`
so each grid point has the identical schema and verdict as the committed scenario sweep. The
**power calculator** is analytical (closed-form `src.experiment.power.mde_mean` + a two-sample
normal power formula), loudly banner-labeled CALCULATOR. A `dashboard_smoke.py` job (+ CI
`dashboard-smoke`) loads every report through the typed loaders to catch schema drift.

## Options considered

- **Chosen — read-only over committed reports + offline-precomputed grid:** every number traces
  to a committed artifact or a labeled formula; fail-loud `ReportSchemaError` on missing fields;
  no Olist needed to run the app; honesty rule mechanically preserved.
- **Live recompute in the app (load Olist, run scenarios on demand):** rejected — slow (10k
  bootstrap × N), needs the raw dataset deployed, and invites drift between UI math and the
  committed reports.
- **Hard-code the numbers into the UI:** rejected — fastest to break silently; no schema guard;
  violates *no invented metrics* in spirit.

## Consequences

- **Easy:** deploy anywhere (Streamlit Community Cloud, no data), trust the figures, test the
  logic layer to 90%+, swap a report and the UI follows.
- **Harder:** new interactivity that needs new numbers requires an offline build step + a fresh
  committed artifact (by design — that is the honesty tax). The What-if grid must be regenerated
  (`make experiment-grid`, needs full Olist) whenever the experiment method changes.
- **Revisit if:** the dashboard needs genuinely live parameters that can't be precomputed into a
  bounded grid, or the report schema churns often enough that the loader/smoke maintenance
  outweighs the drift protection.

## Links

Locked mockup
`docs/mockups/dashboard-v3/index.html` · ADR [0004] (simulated RCT / no invented metrics) ·
ADR [0009] (DiD honest rejection — the Natural-experiment tab) · PRs #27, #28.
