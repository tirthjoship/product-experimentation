# Phase Log — Product Experimentation Analytics

> **Tier 2, history (append-only).** Open only when you need a past detail. Current state lives
> in `STATUS.md`; this file is the record of how we got there. Newest entries on top.

## 2026-06-11 — Session: Plan 3 ship + Plan 4 (gated DiD) build → honest rejection

**Plan 3 shipped (was claimed done, wasn't merged).** STATUS said Plan 3 complete but git showed
6 implementation commits local-only. Pushed `feat/plan3-installment-narrative`; merged PR #20 → dev,
PR #21 dev → main (both CI green). Installment-expansion narrative + PM memo + integrity tests now
on main.

**Plan 4 brainstorm + spec.** Chose: EDA-discovery event selection firewalled by catalog +
outcome-blind feasibility; per-event outcome pre-registration; TWFE + cluster SE + event-study.
Wrote design spec on `spec/plan4-did-natural-experiment`.

**Grill-me sweep (Plans 1–4).** Walked the decision tree as teaching quiz (recommendation +
consequence per option). Surfaced and fixed real issues: (1) **ADR 0007 unit error** — the ≤0.85
ci_width_ratio target conflated variance with width; measured 0.868 actually beats the √(1−r²)≈0.875
optimum for r=0.484; amended ADR + STATUS. (2) **README drift** — results table showed only the raw
CI (ADR 0007 made the adjusted CI the decision object) and a stale upper bound 13.00 vs committed
13.11; fixed. Hardened the spec from the grill: donut assignment design, two-sided pre-trends gate
(Wald + magnitude band so noisy cells can't pass vacuously). Added narrative README (problem→triage→
decision mermaid + ADR-linked triage table + statistical-flow + EDA-findings table) per user request.
Merged PR #22 → dev.

**Plan 4 implementation (subagent-driven, Sonnet per task, 12 tasks TDD).** `src/did/`: frozen
event catalog (committed before any data query — pre-registration provenance), blinded panel
builder, TWFE estimator, event-study pre-trends, 4-condition gate, report writers, stage CLI +
make targets. Two real fixes mid-stream: factory bumped 6+6→8+8 clusters (Wald power); dropped
NaN-outcome rows before clustered OLS (real-data crash: statsmodels group-length mismatch when a
state×week cell has zero delivered orders).

**Opus verification (verification-before-completion).** Two Opus reviewers (integrity + drift).
Caught: forgeable GO verdict (`require_go` accepted a 2-key blob) → hardened to require all gate
conditions passed + forgery regression tests; STATUS cited wrong module `event_catalog.py` →
`catalog.py`; stale 128 badge → 132; unnamed NaN-drop selection bias → added to report threats;
redundant in-function imports cleaned. C2 (the real verdict is FAIL) is not a bug — it's the
deliverable.

**Phase B feasibility on real Olist → FAIL (the finding).** truckers'-strike-2018 candidate failed
the pre-registered gate: adequate_n (45.0% of treated×week cells ≥20 orders, threshold 80% —
North/NE too sparse: 3,604 treated vs 27,884 control pre-period orders, 16 vs 7 states) and
parallel_pretrends (wald_p=0.018, max lead 3.40 > band 1.93). Per protocol no estimate computed;
the documented rejection is the portfolio artifact. **ADR 0009.** Stopped before Phase C/D
(pre-registration lock / estimate) per checkpoint.

**Documentation trail.** ADR 0009 + index; README findings sweep; STATUS overwrite; CONTEXT
natural-experiment outcome note; memory `plan4-did-honest-rejection.md`. Merged PR #23 → dev,
PR #24 dev → main (CI green). End state: 132 tests, 93% coverage, mypy strict clean; Plans 1–4 on
main. Pending roadmap: P2 dashboard, P3 reproducibility CI gate.

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

---

## 2026-06-13 — Plan 5 v3 dashboard (subagent-driven) + ship to main

**Implementation.** Executed the 19-task v3 plan via subagent-driven-development (Sonnet
implementers per task, Opus reviews at phase boundaries + a final verification). Built the
read-only Streamlit + Plotly dashboard: pure layer (`data.load_grid`, `glossary`, `valuecolor`,
v3 `theme`, 7 diversified `charts` builders) + render-only `sections/*` (5 tabs, takeaway tiles,
layered hovers, value colors) + `app.py` 5-tab shell. Offline `scripts/build_experiment_grid.py`
generated `reports/experiment_grid.json` (21 points, real `run_scenarios`+`results_to_json`);
smoke-guarded. Verdict READ from `recommend()`, no invented metrics. ADR 0010 records the
read-only-over-committed-reports architecture.

**Bugs caught only by launching the live app (smoke can't):** deprecated `use_container_width`
→ `width="stretch"`; `st.tabs` runs all bodies → `DuplicateElementId` fixed with a unique `key=`
per chart; forest/coef inline annotations overlapped the tight v3 plots (moved to captions);
`overflow:hidden` clipped the `.ci`/`.term` hover tooltips (→ `overflow:visible`); dumbbell/
diverging point labels clipped at the plot edge (padded x-range + `cliponaxis=False`, + regression
tests). Card borders + chart `lay()` config ported to match the locked mockup pixel-for-pixel
(IBM Plex Mono, tight margins, `#eaecef` borders, `.simbar`/`.box`/`.kpi` CSS).

**Ship.** Pre-validated CI locally (coverage 95.59% ≥90, mypy strict, pre-commit, smoke), then
PR #27 (feat→dev) and PR #28 (dev→main), both all-green (incl. gitleaks). Fast-forwarded `dev`
to `main` — both at the same commit. 208 tests · pure-layer 100%. Remaining manual: deploy to
Streamlit Community Cloud + set `<APP_URL>`.
