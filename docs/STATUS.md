# STATUS — Product Experimentation Analytics

> **Tier 0, authoritative.** Current state only. Read first. Overwrite at session end;
> finished history → `PHASE_LOG.md`. ~40 lines. Last updated: 2026-06-13.

## Where we are

- **Plans 1–4 on `main`** (inference + covariate adjustment + installment narrative +
  PM memo + Plan 4 DiD honest rejection). Shipped via PR #26.
- **Plan 5 dashboard v3 IMPLEMENTED + VERIFIED on `feat/plan5-dashboard`.**
  Read-only Streamlit + Plotly over committed `reports/*.json` + `reports/experiment_grid.json`.
  Screenshots committed. PR to dev → main is the remaining manual step.

## Gate numbers (all verified this session)

- `.venv/bin/pytest -q` → **206 passed**
- Pure-layer coverage → **100%** (charts / data / glossary / theme / valuecolor)
- `mypy dashboard src --strict` → **clean (50 files)**
- `scripts/dashboard_smoke.py` → **green** (experiment + 3 scenarios + 4 buckets + DiD + 21 grid points)
- Live app headless check → **0 render exceptions, 0 horizontal overflow** across all 5 tabs at 390 / 720 / 1280 px

## Dashboard v3 — what's built

- **5 tabs:** Overview · Experiment results · Scenario explorer · Power & design · Natural experiment
- **New features:** persistent header + chip rationale tooltips; plain-language bottom-line takeaway
  tiles per tab; layered hovers (chip rationale + chart ⓘ + glossary term spans); semantic value
  color-coding (good / average / poor); diversified responsive charts (dumbbell, range/variance,
  split bar, diverging marker, lift forest, MDE-vs-n, power-vs-effect); What-if effect grid
  (`scripts/build_experiment_grid.py` → `reports/experiment_grid.json`, 21 points, reuses
  `run_scenarios` + `results_to_json`); analytical power calculator (`src.experiment.power`)
- **De-AI theme:** white · Space Grotesk · Inter · IBM Plex Mono · oxblood accent
- **Honesty preserved:** verdict read from `recommend()` in committed report, never recomputed;
  SIMULATED + CALCULATOR banners on every synthetic figure; no invented metrics
- **New make target:** `make experiment-grid` (builds the grid; requires full Olist)
- **Screenshots committed:** `docs/img/v3-0-overview.png` through `v3-4-natural-experiment.png`
  + `v3-phone-overview.png`

## Remaining manual steps (not done — needs user)

1. Deploy to Streamlit Community Cloud (entrypoint `dashboard/app.py`, py3.12), replace `<APP_URL>`
   in README.md.
2. Open PR `feat/plan5-dashboard` → dev → main.

## Caveats / environment

- `.venv` (uv, py3.12); use `.venv/bin/pytest`, `.venv/bin/mypy`. `make dashboard` uses
  `.venv/bin/python -m streamlit`. Editable install: `pip install -e ".[dev,dashboard]"`.
- Disk ~100% → commit with `SKIP=gitleaks` (never `--no-verify`); CI runs gitleaks server-side.
- `caffeinate` may be running — `pkill caffeinate` to stop.

## Pointers

`CONTEXT.md` · `docs/adr/` (0007 covariate, 0008 framing, 0009 DiD rejection) ·
`docs/superpowers/specs/2026-06-13-dashboard-v3-descriptive-interactive-design.md` ·
`docs/superpowers/plans/2026-06-13-dashboard-v3.md` (19 tasks, TDD, fixtures-only)
