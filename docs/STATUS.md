# STATUS — Product Experimentation Analytics

> **Tier 0, authoritative.** Current state only. Read this first. Overwrite at end of session;
> move finished history to `PHASE_LOG.md`. Keep ~40 lines. Last updated: 2026-06-09.

## Where we are

- **Phase:** 1–2 implementation **COMPLETE + verified**. All 14 plan tasks committed.
- **Branch:** all work **merged to `main`**. PRs #1 (phase0→dev), #2 (metrics→dev),
  #3 (dev→main) all merged. `main` tip `2bfc664`.
- **Open PR:** none.

## Done

- Phase 0 EDA gate (GO), docs system (ADRs 0001–0006, PHASE_LOG, doc map).
- Phase A (Tasks 1–3 scaffold/constants/assignment/fixtures) — verified PASS.
- Phase B (Tasks 4–7 conversion/AOV/D7 + cohort frame) — verified PASS.
- Phase C (Tasks 8–11 effect injection, analysis, power, balance) — verified PASS.
- Phase D (Tasks 12–14 report gen, end-to-end runner, METRICS/EXPERIMENT_DESIGN/README/FUTURE)
  — **verified PASS this session** (Opus verification-before-completion).
- `make experiment` ran on real Olist → `reports/experiment_001.md` (SHIP, AOV CI (7.35, 13.00)).
- Verification evidence: 43/43 pytest, mypy --strict clean (19 files), coverage 92% (>90% gate).
- Cleanups: real `conv_z` captured (was hardcoded 0.0); `.coverage` gitignored.

## Next action

Phase 1 shipped to `main`. **Phase 2 = Streamlit dashboard** (control vs treatment with CIs) —
the one remaining ⏳ in the README deliverables table. Start there next session.

## Caveats / environment

- Env is `.venv` (uv, py3.12). Run tools as `.venv/bin/pytest`, `.venv/bin/mypy`.
- **Local disk ~100%** → `gitleaks` pre-commit hook can't build. Commit with `SKIP=gitleaks`
  (never `--no-verify`). CI runs gitleaks server-side. Free disk when able.
- CI Security job (gitleaks-action@v2) needs `permissions: pull-requests: read` to list PR
  commits on `pull_request` events — without it, PR runs 403. Fixed in `security.yml`.
- Uncovered lines are expected (loader real-CSV, `main()` entry, balance raise) — not fixture-testable.

## Pointers

`CONTEXT.md` (why + locked decisions) · `docs/adr/` · `docs/SKILL_ROUTING.md` ·
plan `docs/superpowers/plans/2026-06-09-metrics-and-experiment.md`.
