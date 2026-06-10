# STATUS — Product Experimentation Analytics

> **Tier 0, authoritative.** Current state only. Read first. Overwrite at session end;
> finished history → `PHASE_LOG.md`. ~40 lines. Last updated: 2026-06-10.

## Where we are

- **Shipped to `main`:** Phase 1 (metrics + simulated A/B) + Phase F (result JSON, data sample, determinism fix). CI green.
- **This session (depth series, from methodology review):** two unmerged branches, both local/unpushed.

## Branches (unpushed)

- `fix/portfolio-hygiene-sync` — README test-count/coverage fix (54 tests, 91% cov). 1 commit `5572d77`. Doc-only, PR-ready.
- `feat/experiment-inference-depth` — **Plan 1 DONE** (8 commits, tip `55ff013`). Off `main`.

## Plan 1 done (feat/experiment-inference-depth)

- **BCa bootstrap** replaces percentile (skew-correct; seeded+`batch=100` → deterministic, memory-safe at n≈50k).
- **`quantile_lift`** — distributional AOV view.
- **Scenario sweep** — `SCENARIOS = adverse(-0.05)/null(0.0)/large(0.05)` → `make scenarios` emits `reports/experiment_scenarios.{md,json}` showing all 3 verdicts: **DO NOT SHIP / NEED MORE DATA / SHIP**. Kills the tautology.
- `null` scenario exposes the ~2 BRL baseline arm imbalance (lift 2.06 at zero effect) → motivates Plan 2 (CUPED/covariate adj).
- `experiment_001.{md,json}` (dashboard contract) + `sample_results.json` regenerated with BCa. 64 tests, mypy strict clean, determinism byte-stable.

## Next action

1. Optional: push + PR `fix/portfolio-hygiene-sync` → dev; PR `feat/experiment-inference-depth` → dev (confirm before main).
2. **Plan 2** — spec #2 covariate-adjustment/ANCOVA (classic CUPED infeasible: ~97% one-time customers; surface a pre-treatment covariate e.g. `freight_value` into the frame).
3. **Plan 3** — narrative: free-shipping reframe (default, unconfirmed) + PM decision memo.
4. **Plan 4** — P4 natural experiment (own pre-registration spec).

Plans: `docs/superpowers/plans/2026-06-10-experiment-inference-depth.md` (+ roadmap spec in `docs/superpowers/specs/`).

## Caveats / environment

- Env `.venv` (uv, py3.12); tools as `.venv/bin/pytest`, `.venv/bin/mypy`. `make scenarios` uses bare `python` → run `.venv/bin/python -m src.experiment.run_experiment --scenarios`.
- Disk ~100% → commit with `SKIP=gitleaks` (never `--no-verify`); CI runs gitleaks server-side.
- Hub README (parent, not a git repo) synced to "Phase 1 + F shipped" via file save.
