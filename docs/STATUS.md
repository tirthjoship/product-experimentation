# STATUS — Product Experimentation Analytics

> **Tier 0, authoritative.** Current state only. Read first. Overwrite at session end;
> finished history → `PHASE_LOG.md`. ~40 lines. Last updated: 2026-06-10.

## Where we are

- **On `main`:** Phase 1 (metrics + simulated A/B) + Phase F (result JSON, sample, determinism). CI green.
- **This session** (methodology review → depth series): three branches, **all pushed, PRs open → `dev`, none merged yet**.

## Open PRs → dev (merge in any order; no conflicts)

- **PR #11** `fix/portfolio-hygiene-sync` — README test-count/coverage sync (54 tests, 91% cov). Doc-only.
- **PR #12** `feat/experiment-inference-depth` — **Plan 1 DONE** (BCa + 3-verdict scenario sweep). 64 tests, mypy strict clean, byte-stable.
- **PR (this branch)** `spec/plan2-covariate-adjustment` — Plan 2 design spec only (no code).

## Plan 1 shipped (PR #12)

- BCa bootstrap replaces percentile (seeded + `batch=100` → deterministic, memory-safe at n≈50k).
- `quantile_lift` distributional view. `make scenarios` → `reports/experiment_scenarios.{md,json}`.
- Sweep `adverse(-0.05)/null(0.0)/large(0.05)` → **DO NOT SHIP / NEED MORE DATA / SHIP** (tautology killed).
- `null` lift = +2.06 at zero effect → exposes baseline arm imbalance → motivates Plan 2.

## Next action (fresh session)

1. **Merge PRs #11, #12, #-spec → dev** (confirm before promoting dev→main).
2. **Plan 2** — build covariate-adjustment from spec `docs/superpowers/specs/2026-06-10-plan2-covariate-adjustment.md`. Run **writing-plans** to turn it into TDD tasks, then subagent-driven (Sonnet impl, Opus verify). Default covariate = `freight_value`; classic CUPED rejected (Olist ~97% one-time customers). Adds an `aov_adjusted` block + pre-period balance guard.
3. **Plan 3** — narrative: free-shipping-threshold reframe (default, **unconfirmed** — user questioned it) + PM decision memo `reports/experiment_001_readout.md`.
4. **Plan 4** — P4 natural experiment (calendar-shock × region DiD, pre-registered gate). Own spec.

Also pending from earlier roadmap: **P2 dashboard** + **P3 reproducibility CI gate** (`docs/superpowers/specs/2026-06-09-phase2-roadmap-design.md`).

## Caveats / environment

- `.venv` (uv, py3.12); use `.venv/bin/pytest`, `.venv/bin/mypy`. `make scenarios` calls bare `python` — run `.venv/bin/python -m src.experiment.run_experiment --scenarios`.
- Disk ~100% → commit `SKIP=gitleaks` (never `--no-verify`); CI runs gitleaks server-side.
- Hub README (parent dir, not a git repo) synced to "Phase 1 + F shipped" via file save.
- `caffeinate` running (keeps Mac awake) — `pkill caffeinate` to stop.

## Pointers

`CONTEXT.md` · `docs/adr/` · `docs/superpowers/specs/` (roadmap + Plan 2) · `docs/superpowers/plans/` (Plan 1).
