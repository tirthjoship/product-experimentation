# Phase Log — Product Experimentation Analytics

> **Tier 2, history (append-only).** Open only when you need a past detail. Current state lives
> in `STATUS.md`; this file is the record of how we got there. Newest entries on top.

## 2026-06-09 — Session 1

**Onboarding + harness understanding.** Mapped the 5-layer stack (memory → skills → hooks →
subagents → plugins) and this project's place as portfolio slot 4/5 (non-ML, SQL + stats).
Created `docs/SKILL_ROUTING.md` (phase→skill routing).

**Phase 0 — EDA gate → GO.** Created and executed `notebooks/00_eda_gate.ipynb` against the real
Olist CSVs. Findings: 99,441 orders; delivered rate 97.02% (ceiling); join orphans <1%;
D7-within-7d = 0.214%; tail months 2018-09/10 right-censored (0% delivered); DuckDB==pandas
parity. Wrote `reports/eda_gate.md` (GO + caveats) and `docs/DATA_DICTIONARY.md`. Env bootstrapped
with `uv` into `.venv`. Opened PR #1 (`feat/phase0-eda-gate` → `dev`); created `dev` from `main`.

**Phase 1 — design.** Decisions (one AskUserQuestion each): simulated RCT + injected effect;
AOV primary / conversion guardrail / D7 exploratory; bootstrap CI + Welch + two-proportion z.
Wrote and committed the design spec (scrubbed for AI-writing patterns) and the 14-task TDD plan.
All plan reference values verified against the venv before writing.

**Phase 2 implementation (subagent-driven).** Branch `feat/metrics-experiment`.
- Phase A (Tasks 1–3): scaffold, constants, `assign_variant`, fixtures, conftest. Sonnet
  implementer → Opus verification PASS. 14 tests.
- Phase B (Tasks 4–7): conversion/AOV/D7 metric SQL + wrappers (pandas-parity tests), cohort
  frame builder. Sonnet → Opus verification PASS. 24 tests. Two sound deviations: import ordering
  for ruff E402; empty-cohort test uses a fresh empty connection (DuckDB can't DELETE a view).

**Documentation system.** Added ADRs 0001–0006 capturing the decisions above, `docs/STATUS.md`
(Tier 0), this log, and project memory. Enriched `reports/eda_gate.md` with the investigation
narrative (drill-down reasoning behind each decision).
