# STATUS — Product Experimentation Analytics

> **Tier 0, authoritative.** Current state only. Read first. Overwrite at session end;
> finished history → `PHASE_LOG.md`. ~40 lines. Last updated: 2026-06-11.

## Where we are

- **Plans 1 + 2 on main** (inference depth + covariate adjustment). CI green on main.
- **Plan 3 DONE on branch `feat/plan3-installment-narrative`** — not yet pushed/PR'd. 95 tests,
  96% coverage, mypy strict clean.

## Plan 3 — what shipped (installment-expansion narrative)

- Framing locked: installment-expansion test (6x→10x interest-free cap). Free-shipping rejected
  for portfolio separation from supply-chain-ml. **ADR 0008**.
- `src/report/installment_motivation.py` + `sql/eda/installments*.sql` → committed descriptive
  artifacts `reports/installment_motivation.{md,json}` (deterministic; aov rounded 6dp because
  DuckDB AVG parallel-sum is float-nondeterministic). `make motivation`.
- **PM decision memo** `reports/experiment_001_readout.md` (hand-written, judgment artifact).
- **Memo↔artifact integrity test** `tests/test_readout_integrity.py` — every headline number in
  the memo must match committed JSON (CI enforces "no invented metrics" forever).
- Framing sweep: report intro lines, README, EXPERIMENT_DESIGN, CONTEXT §2, ADR 0008 index.
- Experiment .json numbers UNCHANGED (only report .md framing lines + new artifacts).

## Real motivation numbers (cohort window, full data)

- 51.4% of orders paid in >1 installment · credit cards = 78.4% of payment value · n=99,092.
- AOV by bucket: 1→120.98, 2-3→136.11, 4-6→182.69, 7+→337.03 (affordability gradient is real).

## Next action

1. **Push + PR** `feat/plan3-installment-narrative` → dev, merge, promote dev → main.
2. **Plan 4** — DiD natural experiment (calendar-shock × region), own spec, pre-registered gate.
3. Earlier roadmap still pending: P2 dashboard + P3 reproducibility CI gate.

## Caveats / environment

- `.venv` (uv, py3.12); use `.venv/bin/pytest`, `.venv/bin/mypy`. `make scenarios`/`motivation`
  call bare `python` — run via `.venv/bin/python -m ...`.
- Disk ~100% → commit `SKIP=gitleaks` (never `--no-verify`); CI runs gitleaks server-side.
- ci_width_ratio = 0.868 (Plan 2) ≈ theoretical optimum √(1−r²)=0.875 for r=0.484; the old
  ≤0.85 target was a variance-vs-width unit error — corrected in ADR 0007 amendment.
- `caffeinate` running (keeps Mac awake) — `pkill caffeinate` to stop.

## Pointers

`CONTEXT.md` · `docs/adr/` (0007 covariate, 0008 framing) · `docs/superpowers/specs/` ·
`docs/superpowers/plans/` (Plans 1–3).
