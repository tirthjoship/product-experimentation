# STATUS — Product Experimentation Analytics

> **Tier 0, authoritative.** Current state only. Read first. Overwrite at session end;
> finished history → `PHASE_LOG.md`. ~40 lines. Last updated: 2026-06-13.

## Where we are

- **Plans 1–5 all shipped to `main`.** `dev` and `main` are in sync at the same commit
  (merged via PR #27 feat→dev, PR #28 dev→main, then dev fast-forwarded to main).
- Plan 5 = **read-only Streamlit + Plotly dashboard v3** over committed `reports/*.json`.
  All CI green (test, lint, mypy strict, dashboard-smoke, gitleaks). Branch
  `feat/plan5-dashboard` is merged (kept on origin, can be deleted).
- **Gate at ship:** 208 tests · pure-layer 100% · combined src+dashboard coverage 95.59%
  (≥90 gate) · mypy --strict clean · `dashboard_smoke.py` green (21 grid points).

## Plan 5 dashboard — what's live

- 5 tabs: Overview · Experiment results · Scenario explorer (+ What-if grid slider) ·
  Power & design (analytical calculator) · Natural experiment (DiD honest rejection).
- Pure layer (`dashboard/data.py`,`charts.py`,`theme.py`,`glossary.py`,`valuecolor.py`)
  carries logic + 90% gate; `sections/*`+`app.py` render-only (coverage-omitted).
- Honest interactivity: What-if reads precomputed `reports/experiment_grid.json` (21 pts,
  built offline by `scripts/build_experiment_grid.py`); power calc is analytical. Verdict
  READ from `recommend()`, never recomputed. No invented metrics. See **ADR 0010**.
- Mockup-faithful: matches `docs/mockups/dashboard-v3/index.html` (charts, `.box`/`.simbar`/
  `.kpi` CSS, layered hovers). Verified live headless: 0 exceptions · 0 clipped labels ·
  0 horizontal overflow @ 390/720/1280px. Screenshots in `docs/img/v3-*.png`.

## Next actions

1. **Deploy (needs user):** Streamlit Community Cloud — entrypoint `dashboard/app.py`, py3.12,
   editable install with `[dashboard]` extra. Then replace `<APP_URL>` in `README.md`.
2. Optional: delete merged `feat/plan5-dashboard` on origin; prune stale `docs/*` / `spec/*`
   branches.
3. **Backlog:** Plan 3 reproducibility CI gate; optional Plan 4 Phase E GO path (needs denser
   geography or log_orders outcome + pre-registration lock — explicit sign-off required).

## Caveats / environment

- `.venv` (uv, py3.12); use `.venv/bin/pytest`, `.venv/bin/mypy`. Editable install must include
  the `[dashboard]` extra or the finder won't map `dashboard/` (`pip install -e ".[dev,dashboard]"`).
- Disk ~100% → commit `SKIP=gitleaks` locally (never `--no-verify`); CI runs gitleaks server-side.
- Charts use `width="stretch"` (not deprecated `use_container_width`); every `st.plotly_chart`
  needs a unique `key=` (st.tabs renders all bodies → DuplicateElementId otherwise).
- Run the app: `make dashboard`. Smoke: `.venv/bin/python scripts/dashboard_smoke.py`.

## Pointers

`CONTEXT.md` · `docs/adr/` (0007 covariate · 0008 framing · 0009 DiD rejection · 0010 dashboard) ·
specs+plans under `docs/superpowers/`. History → `docs/PHASE_LOG.md`.
