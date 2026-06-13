# STATUS — Product Experimentation Analytics

> **Tier 0, authoritative.** Current state only. Read first. Overwrite at session end;
> finished history → `PHASE_LOG.md`. ~40 lines. Last updated: 2026-06-13.

## Where we are

- **Plans 1–4 on `main`** (inference depth + covariate adjustment + installment narrative +
  PM memo + Plan 4 DiD honest rejection). Shipped via PR #26.
- **Plan 5 dashboard on branch `feat/plan5-dashboard` — PR-ready (commit `db453b6`).**
  Read-only Streamlit + Plotly over committed `reports/*.json`. Opus pre-PR review DONE,
  all fixes landed. 152 tests · 95.11% coverage · mypy strict clean (46 files) ·
  `make dashboard-smoke` green. NOT yet PR'd (3 manual steps below).

## Plan 5 — what's built

- `dashboard/`: pure layer (`data.py` typed loaders, `charts.py` plotly builders, `theme.py`)
  carries logic + 90% gate; `sections/*` + `app.py` are render-only glue (coverage-omitted).
- Story tab: hero verdict (read from `large` scenario) · motivation bar · how-to-read ·
  results forest plot (unadj vs adj CI + variance-reduction + MDE annotations) · DiD
  honest-rejection (pre-trends coef plot, 2 leads break band → red · gate checklist).
- Interactive tab: scenario radio → verdict flip + CI plot · guardrail panel.
- Fail-loud: missing/malformed field → `ReportSchemaError`, never a default. Per-section
  error isolation. `scripts/dashboard_smoke.py` + CI `dashboard-smoke` job guard schema drift.

## Dashboard v3 — designed + planned (NEXT: implement in fresh session)

Dashboard v2 is PR-ready (`db453b6`) but we're expanding it to **v3** before PR. v3 design is
locked via a clickable mockup; spec + full TDD plan committed. **Implement v3 next.**
- Spec: `docs/superpowers/specs/2026-06-13-dashboard-v3-descriptive-interactive-design.md`
- Plan: `docs/superpowers/plans/2026-06-13-dashboard-v3.md` (19 tasks, TDD, fixtures-only)
- Reference mockup (open it): `docs/mockups/dashboard-v3/index.html`
- v3 = persistent header + 5 tabs · plain-language bottom-line tiles · chip rationale + chart ⓘ
  + glossary hovers · value color-coding · diversified responsive charts · What-if effect grid
  (`reports/experiment_grid.json` via `scripts/build_experiment_grid.py`) · power calculator.
  De-AI theme: white · Space Grotesk · Inter · oxblood. Read-only/no-invented-metrics preserved.

## Next actions

1. **Implement v3** in a fresh session via `superpowers:subagent-driven-development` (or
   executing-plans) against the plan above. Start at Phase 0 (baseline gate green on
   `feat/plan5-dashboard`).
2. **Manual (needs user):** capture screenshots → `docs/img/`; deploy to Streamlit Community
   Cloud (entrypoint `dashboard/app.py`, py3.12), replace `<APP_URL>`.
3. Open PR `feat/plan5-dashboard` → dev → main once v3 done.
4. Backlog: Plan 3 reproducibility CI gate; optional Plan 4 Phase E GO path (needs denser
   geography or log_orders outcome + pre-registration lock — explicit sign-off required).

## Caveats / environment

- `.venv` (uv, py3.12); use `.venv/bin/pytest`, `.venv/bin/mypy`. `make dashboard` uses
  `.venv/bin/python -m streamlit`. Editable install must include `[dashboard]` extra or the
  finder won't map `dashboard/` (regenerate with `pip install -e ".[dev,dashboard]"`).
- Disk ~100% → commit `SKIP=gitleaks` (never `--no-verify`); CI runs gitleaks server-side.
- `use_container_width=True` swapped to `width="stretch"` across all 5 sections; streamlit
  pin bumped to `>=1.52.0` (pyproject + pre-commit synced). Resolved in `db453b6`.
- `caffeinate` may be running — `pkill caffeinate` to stop.

## Pointers

`CONTEXT.md` · `docs/adr/` (0007 covariate, 0008 framing, 0009 DiD rejection) ·
`docs/superpowers/specs/2026-06-12-plan5-dashboard-design.md` ·
`docs/superpowers/plans/2026-06-12-plan5-dashboard.md`.
