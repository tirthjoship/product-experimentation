# STATUS — Product Experimentation Analytics

> **Tier 0, authoritative.** Current state only. Read this first. Overwrite at end of session;
> move finished history to `PHASE_LOG.md`. Keep ~40 lines. Last updated: 2026-06-09.

## Where we are

- **Phase:** 1–2 implementation **COMPLETE + verified**. All 14 plan tasks committed.
- **Branch:** `feat/metrics-experiment` (off `feat/phase0-eda-gate`). Clean; uncommitted: STATUS +
  `.gitignore` + `z`-field fix (this session).
- **Open PR:** #1 `feat/phase0-eda-gate` → `dev` (Phase 0 + routing docs). Not yet merged.

## Done

- Phase 0 EDA gate (GO), docs system (ADRs 0001–0006, PHASE_LOG, doc map).
- Phase A (Tasks 1–3 scaffold/constants/assignment/fixtures) — verified PASS.
- Phase B (Tasks 4–7 conversion/AOV/D7 + cohort frame) — verified PASS.
- Phase C (Tasks 8–11 effect injection, analysis, power, balance) — verified PASS.
- Phase D (Tasks 12–14 report gen, end-to-end runner, METRICS/EXPERIMENT_DESIGN/README/FUTURE)
  — **verified PASS this session** (Opus verification-before-completion).
- `make experiment` ran on real Olist → `reports/experiment_001.md` (SHIP, AOV CI (7.39, 13.01)).
- Verification evidence: 43/43 pytest, mypy --strict clean (19 files), coverage 92% (>90% gate).
- Cleanups: real `conv_z` captured (was hardcoded 0.0); `.coverage` gitignored.

## Next action

1. Commit this session (STATUS + `.gitignore` + `run_experiment.py` z-fix). Use `SKIP=gitleaks`.
2. Open PR for `feat/metrics-experiment` (Phase 1–2 metrics + simulated experiment).
3. Decide merge order vs open PR #1 (`feat/phase0-eda-gate` → `dev`).

## Caveats / environment

- Env is `.venv` (uv, py3.12). Run tools as `.venv/bin/pytest`, `.venv/bin/mypy`.
- **Local disk ~100%** → `gitleaks` pre-commit hook can't build. Commit with `SKIP=gitleaks`
  (never `--no-verify`). CI runs gitleaks server-side. Free disk when able.
- Uncovered lines are expected (loader real-CSV, `main()` entry, balance raise) — not fixture-testable.

## Pointers

`CONTEXT.md` (why + locked decisions) · `docs/adr/` · `docs/SKILL_ROUTING.md` ·
plan `docs/superpowers/plans/2026-06-09-metrics-and-experiment.md`.
