# STATUS — Product Experimentation Analytics

> **Tier 0, authoritative.** Current state only. Read first. Overwrite at session end;
> finished history → `PHASE_LOG.md`. ~40 lines. Last updated: 2026-06-10.

## Where we are

- **Branch:** `feat/plan2-covariate-adjustment` (not yet pushed / no PR open).
- **Plan 2 DONE** — covariate-adjusted block shipped, artifacts regenerated, all gates green.

## Plan 2 — what shipped

- `freight_value` covariate (CUPED-style regression adjustment; classic CUPED rejected — ~97% one-time buyers).
- `src/experiment/cuped.py` — `theta_ols` + `adjusted_means` + `adjusted_ci` (OLS residualization).
- `aov_adjusted` block added to every `run()` result dict (lift, CI, ci_width_ratio, theta).
- Adjusted-CI verdicts in scenario sweep (adverse / null / large).
- Baseline-balance warning guard (`order_value_gap` emitted; warns if gap > 0.05).
- ADR 0007 — freight_value covariate rationale (logged in `docs/adr/`).
- Artifacts regenerated + determinism verified (byte-identical on two consecutive runs).

## Measured numbers (full-data run, seed 42)

- **aov_adjusted.ci_width_ratio = 0.868** (target ≤ 0.85 — see caveat below).
- **null scenario adjusted lift = +0.537** vs unadjusted **+2.057** → adjustment pulls toward zero ✓.
- 77 tests pass · mypy strict clean · pre-commit all-pass (gitleaks skipped, disk-full).

## ci_width_ratio caveat

Target was ≤ 0.85 (≥15% CI width reduction). Achieved 0.868 (~13% reduction). freight_value
is a real predictor but R² is modest at n≈100k. This is honest — do not inflate. Noted in ADR 0007.

## Next action

1. **Push + open PR** `feat/plan2-covariate-adjustment` → `dev`.
2. Merge pending PRs (#11, #12, plan2 PR) into dev, then promote dev → main.
3. **Plan 3** — narrative memo `reports/experiment_001_readout.md`; free-shipping-threshold reframe
   (unconfirmed — user questioned it; treat as default hypothesis, not locked).
4. **Plan 4** — DiD natural experiment (calendar-shock × region), own spec, pre-registered gate.

## Caveats / environment

- `.venv` (uv, py3.12); use `.venv/bin/pytest`, `.venv/bin/mypy`. `make scenarios` calls bare `python` — run `.venv/bin/python -m src.experiment.run_experiment --scenarios`.
- Disk ~100% → commit `SKIP=gitleaks` (never `--no-verify`); CI runs gitleaks server-side.
- Hub README (parent dir, not a git repo) synced to "Phase 1 + F shipped" via file save.
- `caffeinate` running (keeps Mac awake) — `pkill caffeinate` to stop.

## Pointers

`CONTEXT.md` · `docs/adr/` · `docs/superpowers/specs/` (roadmap + Plan 2) · `docs/superpowers/plans/` (Plan 1, Plan 2).
