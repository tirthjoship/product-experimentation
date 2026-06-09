# STATUS — Product Experimentation Analytics

> **Tier 0, authoritative.** Current state only. Read this first. Overwrite at end of session;
> move finished history to `PHASE_LOG.md`. Keep ~40 lines. Last updated: 2026-06-09.

## Where we are

- **Phase:** 1→2 transition. EDA gate **GO** (`reports/eda_gate.md`). Design spec + plan approved.
  Implementation in progress.
- **Branch:** `feat/metrics-experiment` (off `feat/phase0-eda-gate`).
- **Open PR:** #1 `feat/phase0-eda-gate` → `dev` (Phase 0 + routing docs). Not yet merged.

## Done

- Phase 0 EDA gate (notebook executed, `reports/eda_gate.md` = GO, `docs/DATA_DICTIONARY.md`).
- Phase 1 design: spec + 14-task plan, both committed.
- Implementation **Phase A** (Tasks 1–3: scaffold, constants, assignment, fixtures) — done, verified PASS.
- Implementation **Phase B** (Tasks 4–7: conversion/AOV/D7 metrics + cohort frame) — done, verified PASS.
- Docs system: ADRs 0001–0006, this STATUS, PHASE_LOG, ADR index.

## Next action

Resume implementation **Phase C** (Tasks 8–11: effect injection, analysis, power, balance),
then **Phase D** (Tasks 12–14: report generator, end-to-end runner, METRICS/EXPERIMENT_DESIGN/README).
Workflow: Sonnet implementer per phase → Opus `verification-before-completion` after each phase.

## Caveats / environment

- Env is `.venv` (created via `uv`, py3.12). Run tools as `.venv/bin/pytest`, `.venv/bin/mypy`.
  `make` targets assume this venv. mypy installed into venv.
- **Local disk at ~100%** → pre-commit `gitleaks` hook can't build. Commit with `SKIP=gitleaks`
  (skips only gitleaks; never `--no-verify`). CI runs gitleaks server-side. Free disk when able.
- Current test suite: 24 passing. mypy strict clean.

## Pointers

`CONTEXT.md` (why + locked decisions) · `docs/adr/` (decision records) · `docs/SKILL_ROUTING.md`
(phase→skill) · plan `docs/superpowers/plans/2026-06-09-metrics-and-experiment.md`.
