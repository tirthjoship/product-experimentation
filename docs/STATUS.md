# STATUS — Product Experimentation Analytics

> **Tier 0, authoritative.** Current state only. Read this first. Overwrite at end of session;
> move finished history to `PHASE_LOG.md`. Keep ~40 lines. Last updated: 2026-06-10.

## Where we are

- **Phase:** Phase 1 (metrics + simulated experiment) and **Phase F (foundation)** both COMPLETE,
  verified, and **merged to `main`** (`main` tip `4cf0805`). CI green on dev + main.
- **Branch:** on `main`. `feat/phase-f-foundation` merged into dev → main and deleted.
- **Open PR:** none. Roadmap spec + per-phase plans live in `docs/superpowers/`.

## Done

- Phase 0 EDA gate (GO); Phases A–D (Phase 1): metrics, simulated A/B, report — verified.
- **Phase F (this session, subagent-driven, all reviewed):**
  - `src/report/results_io.py` — JSON serializer for results dict (tuples→arrays, numpy coerced).
  - `run_experiment.py` emits committed `reports/experiment_001.json` (full) via `write_outputs()`.
  - `scripts/build_sample.py` — deterministic join-consistent Olist sampler w/ loud guards.
  - `data/sample/` (3.6 MB, labeled) + `reports/sample_results.json` committed.
  - `[dashboard]` optional-deps (streamlit); `make typecheck` now covers `scripts/`.
  - **CRITICAL fix:** `cohort.sql` had no `ORDER BY` → bootstrap CI was non-deterministic.
    Added `ORDER BY order_id` → CI `(7.35, 13.00)` byte-stable, guarded by determinism test.
- Evidence: 54/54 pytest, mypy --strict clean (src + scripts, 22 files), CI green main.

## Next action

**Phase 2 = Streamlit dashboard** — renders committed `reports/experiment_001.json` (real numbers),
CI error bars + ship banner, deploy on Streamlit Community Cloud (public README link). Needs its own
plan (writing-plans). Then **P3** (reproducibility regression gate on the sample) and **P4** (gated
calendar-shock × region diff-in-diff). Roadmap: `docs/superpowers/specs/2026-06-09-phase2-roadmap-design.md`.

## Caveats / environment

- Env `.venv` (uv, py3.12). Tools as `.venv/bin/pytest`, `.venv/bin/mypy`.
- **Local disk ~100%** → `gitleaks` pre-commit hook can't build. Commit with `SKIP=gitleaks`
  (never `--no-verify`). CI runs gitleaks server-side.
- CI Security (gitleaks-action@v2) needs `permissions: pull-requests: read` — fixed in `security.yml`.
- Large-file hook holds 500 KB globally, excludes `data/sample/`.

## Pointers

`CONTEXT.md` · `docs/adr/` · `docs/SKILL_ROUTING.md` · roadmap spec + Phase F plan in
`docs/superpowers/`. Caffeinate (PID may be stale) keeps Mac awake — `pkill caffeinate` to stop.
