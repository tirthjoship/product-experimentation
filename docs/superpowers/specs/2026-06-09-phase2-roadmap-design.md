# Phase 2 → End Roadmap — Design Spec

**Date:** 2026-06-09
**Status:** Approved (brainstorm + grill-me, 2026-06-09)
**Supersedes planning intent in:** `docs/FUTURE_ENHANCEMENTS.md` (this spec is the locked sequencing)
**Predecessor:** Phase 1 (metrics + simulated experiment) shipped to `main`; see
`docs/superpowers/plans/2026-06-09-metrics-and-experiment.md`.

---

## Goal

Take the project from "Phase 1 shipped" to a finished portfolio showcase that maximizes the
product-DS hiring signal — **statistical rigor + SQL depth + product judgment + reproducible
pipeline** — while refusing infra theater (no S3/dbt/Docker/Snowflake, no committed full dataset).

## Finish-line decision

Tiered finish, **all three phases, P4 gated**. Chosen over "minimal E2E" (looks like every other
A/B demo) and "full platform showcase" (diminishing returns for portfolio slot 4/5).

## Locked decisions (from grill-me)

| # | Branch | Decision | Why |
|---|--------|----------|-----|
| Q1 | Data in CI/host | Commit a **~2MB labeled sample** (only the 4 tables the experiment uses: orders, payments, customers, items; ~5–10k orders) under `data/sample/`. Full data stays Kaggle-referenced + gitignored. | 120MB raw bloats git history permanently (immutable); 58MB geolocation is unused dead weight; "reference don't commit" is the senior DS convention. Sample gives ~95% of "clone → it runs" at ~2% of the size. |
| Q2 | Dashboard data source | `run_experiment.py` emits committed `reports/experiment_001.json` (real 99k numbers). Dashboard **renders that JSON** (no recompute). Host on Streamlit Community Cloud → public README link. | A dashboard showing **real** headline numbers beats an interactive one showing toy sample numbers. Zero data dependency → trivial deploy. JSON artifact doubles as P3's snapshot input. |
| Q3 | GHA scope | **Reproducibility regression gate**: CI runs the pipeline on the committed sample and asserts metrics == committed `reports/sample_results.json`; fail the build on drift. Optional sample-report artifact upload. **No** auto-commit bot. | CI cannot regenerate the full-data report (no full data in repo). Reframing "re-run a script" into "my analytics pipeline is numerically stable + regression-guarded" is a stronger, rarer signal. Auto-commit causes commit loops + push-permission pain. |
| Q4 | Natural experiment | **Calendar-shock × region diff-in-diff**, with a **pre-registered gate** (below). Rejection is a valid, still-valuable deliverable. | Olist has no documented intervention; classic DiD needs a dated treatment. Pre-registering the gate prevents manufacturing a fake causal claim. A documented rejection is a strong judgment artifact. |

---

## Phases

### Phase F — Foundation (prerequisite for P2 + P3)

- Add a sampling script (e.g. `scripts/build_sample.py`) that downsamples the 4 used Olist tables
  to ~5–10k orders, deterministic (seed 42), and writes labeled CSVs to `data/sample/`. Commit the
  sample (~2MB). Each file/banner labeled "sample for CI/demo; full data on Kaggle".
- Extend `run_experiment.py` to emit two committed JSON artifacts alongside the markdown:
  - `reports/experiment_001.json` — full-data (99k) results dict (the dashboard reads this).
  - `reports/sample_results.json` — results computed on `data/sample/` (P3's regression snapshot).
- Add a `[dashboard]` optional-dependency group (`streamlit`) to `pyproject.toml`.
- Tests: JSON emit shape matches the `results` contract; sample build is deterministic on fixture.

### Phase P2 — Streamlit dashboard (needs F)

- `app/` Streamlit app that **renders** committed `reports/experiment_001.json` — no recompute.
- Shows control vs treatment for AOV (primary), conversion (guardrail), D7 (exploratory) with
  **95% CI error bars**, the ship/no-ship banner, and the simulation disclaimer.
- Deploy on Streamlit Community Cloud; add the public URL + a screenshot to README.
- Test: a render/smoke test that the app loads the JSON and produces the expected figure/labels
  headlessly (no full data needed).

### Phase P3 — Reproducibility regression gate (needs F)

- New CI job (extend `.github/workflows/`): install deps, run the pipeline on `data/sample/`,
  assert the freshly-computed metrics equal `reports/sample_results.json` within tolerance; **fail
  on drift**. This is a numerical regression test for the stats pipeline.
- Optional: upload the rendered sample report as a build artifact for viewing.
- No auto-commit. The committed full-data report/JSON are produced locally and reviewed in PRs.

### Phase P4 — Natural experiment, gated (independent; do last — highest uncertainty)

- Design: **calendar-shock × region** diff-in-diff. Pick a dated boundary (e.g. the Nov-2017
  Black-Friday spike, or a freight/delivery-time regime change by state); treated = regions
  exposed earlier/more, control = late/less-exposed; outcome = AOV or order volume.
- **Pre-registered GO gate — ALL four must hold, decided before inspecting the post-period:**
  1. An identifiable dated boundary (the "event") exists.
  2. Treated vs control groups defined by geography/timing, **not** by the outcome.
  3. **Parallel pre-trends** — on ≥3 pre-event time buckets, treated & control move together
     (DiD interaction term on the pre-period is non-significant).
  4. Adequate n per cell.
- **GO** → `reports/experiment_002_did.md` (DiD estimate + CI + parallel-trends evidence).
- **FAIL** → `reports/natural_experiment_feasibility.md` = REJECTED, documenting which assumption
  broke. This still ships and is a deliberate judgment signal — no manufactured causal claim.

---

## Dependency order

```
F → (P2 ∥ P3) → P4
```

P2 and P3 may proceed in parallel once F lands. P4 is independent but scheduled last because its
outcome is uncertain and it must not block the rest of the showcase.

## Out of scope (explicitly rejected)

- Committing the full or unused (geolocation) raw dataset.
- S3 PDF archive, dbt-core, Docker, Snowflake/Databricks, Airflow.
- Auto-commit / bot-push of regenerated reports.
- Live-recompute dashboard showing sample numbers that conflict with the headline report.

## Success criteria (project "done")

- Public Streamlit link renders real Phase-1 results with CIs (P2).
- CI fails on any silent change to pipeline numbers (P3).
- A natural-experiment artifact exists — either a valid DiD result or a documented rejection (P4).
- Repo stays lean (~2MB sample, no full data in history); README reproduction steps intact.

## Honesty constraints (carried from project rules)

- Every number traces to a committed artifact or notebook output (no invented metrics).
- Sample data and simulated effect labeled in every report banner + README.
- `seed = 42` pinned for sampling, assignment, and bootstrap.
