# STATUS — Product Experimentation Analytics

> **Tier 0, authoritative.** Current state only. Read first. Overwrite at session end;
> finished history → `PHASE_LOG.md`. ~40 lines. Last updated: 2026-06-11.

## Where we are

- **Plans 1–3 on main** (inference depth + covariate adjustment + installment narrative + PM memo).
- **Plan 4 DiD INFRASTRUCTURE complete on branch `feat/plan4-did-natural-experiment`.**
  132 tests · 93% coverage · mypy strict clean.
  Shipped: event catalog · blinded panel builder · TWFE estimator · pre-trends check ·
  DiD gate · report writers · `make did-feasibility` / `make did-gate` / `make did` stage CLI.
- **Event catalog committed BEFORE any Phase B query** — pre-registration timestamp is
  git-verifiable (`git log --follow src/did/catalog.py`).

## Plan 4 — phase status

| Phase | Status |
|-------|--------|
| A — event catalog + blinded panel | complete |
| B — feasibility (pre-period counts, outcome-blind) | **PENDING — next action** |
| C — pre-registration lock | blocked on B |
| D — TWFE estimation + gate | blocked on C |

## Next action

Run `make did-feasibility` on full data (outcome-blind; pre-period counts only — safe to run
before pre-registration). Then **STOP for user review** before Phase C pre-registration lock.
Do NOT run `make did-gate` or `make did` without explicit user sign-off.

## Real motivation numbers (cohort window, full data — Plan 3)

- 51.4% of orders paid in >1 installment · credit cards = 78.4% of payment value · n=99,092.
- AOV by bucket: 1→120.98, 2-3→136.11, 4-6→182.69, 7+→337.03 (affordability gradient is real).

## Caveats / environment

- `.venv` (uv, py3.12); use `.venv/bin/pytest`, `.venv/bin/mypy`. `make scenarios`/`motivation`
  call bare `python` — run via `.venv/bin/python -m ...`.
- Disk ~100% → commit `SKIP=gitleaks` (never `--no-verify`); CI runs gitleaks server-side.
- ci_width_ratio = 0.868 (Plan 2) ≈ theoretical optimum √(1−r²)=0.875 for r=0.484; the old
  ≤0.85 target was a variance-vs-width unit error — corrected in ADR 0007 amendment.
- `caffeinate` running (keeps Mac awake) — `pkill caffeinate` to stop.

## Pointers

`CONTEXT.md` · `docs/adr/` (0007 covariate, 0008 framing) · `docs/superpowers/specs/` ·
`docs/superpowers/plans/` (Plans 1–4).
