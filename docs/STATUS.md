# STATUS — Product Experimentation Analytics

> **Tier 0, authoritative.** Current state only. Read first. Overwrite at session end;
> finished history → `PHASE_LOG.md`. ~40 lines. Last updated: 2026-06-11.

## Where we are

- **Plans 1–3 on main** (inference depth + covariate adjustment + installment narrative + PM memo).
- **Plan 4 DiD implemented on branch `feat/plan4-did-natural-experiment`** — PR #23 open to dev
  (CI green). 132 tests · 93% coverage · mypy strict clean.
  Shipped: event catalog · blinded panel builder · TWFE estimator · pre-trends check ·
  DiD gate · report writers · `make did-feasibility` / `make did-gate` / `make did` stage CLI.
- **Event catalog committed BEFORE any Phase B query** — pre-registration timestamp is
  git-verifiable (`git log --follow src/did/catalog.py`).

## Plan 4 — outcome

**Phase B feasibility ran on real Olist data. Truckers'-strike candidate FAILED the gate:**

| Check | Result |
|-------|--------|
| adequate_n | **FAIL** — 45.0% week-cell density (threshold 80%); treated pre-period 3,604 orders / 16 states; control 27,884 / 7 states |
| parallel_pretrends | **FAIL** — Wald p = 0.018 (threshold >0.10); max lead abs = 3.40 > band 1.93 |

Per pre-registered protocol, **no post-period estimate was computed.** Rejection documented in
[ADR 0009](adr/0009-gated-did-natural-experiment.md). The rejection is the deliverable.

## Next actions

1. Merge PR #23 → dev → main (in progress).
2. Optional Phase E only if pursuing a GO — would need denser geography or log_orders volume
   outcome + a pre-registration lock commit before any data query; needs explicit user sign-off.
3. Earlier roadmap still pending: Plan 2 dashboard (Streamlit), Plan 3 reproducibility CI gate.

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

`CONTEXT.md` · `docs/adr/` (0007 covariate, 0008 framing, 0009 DiD rejection) · `docs/superpowers/specs/` ·
`docs/superpowers/plans/` (Plans 1–4).
