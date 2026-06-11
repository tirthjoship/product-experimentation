# CLAUDE.md — Product Experimentation Analytics

**Fresh-session startup (token budget):** read **`docs/STATUS.md`** ONLY (Tier 0 — current
phase, next action, branch, caveats, ~40 lines). That is enough to start work. Do NOT read
`CONTEXT.md`, ADRs, `PHASE_LOG.md`, or code history up front — open a Tier-2 file only when
the named task points at it, max ~3 such files before starting. `CONTEXT.md` is the stable
source of truth (locked decisions, dataset, phase gates) — on demand, never by default.

## Documentation map (what lives where — don't duplicate)

| Channel | Holds | Tier |
|---------|-------|------|
| `docs/STATUS.md` | current state: phase, next action, branch, PR, caveats (~40 lines, overwrite) | 0 — read first |
| `MEMORY.md` (auto-loaded) | evergreen cross-session prefs + pointers | 1 — scan |
| `CONTEXT.md` | why + locked decisions + dataset + glossary (stable) | 2 — on demand |
| `docs/adr/` | one record per non-obvious decision (context/options/consequences) | 2 — on demand |
| `docs/PHASE_LOG.md` | append-only history of each session/phase | 2 — history only |
| `docs/SKILL_ROUTING.md` | phase→skill/agent routing + gate rules | 2 — on demand |
| `AGENTS.md` | coding standards | 2 — on demand |
| `docs/superpowers/specs/` · `plans/` | design specs + implementation plans | 2 — on demand |

Route by this table: current state never goes in an ADR; decisions never go in STATUS.

## Quick reference

| Item | Value |
|------|-------|
| Dataset | Olist Brazilian E-Commerce (Kaggle) |
| Phase | **0 = EDA gate** — do not build full pipeline until `reports/eda_gate.md` says GO |
| Skill routing | `docs/SKILL_ROUTING.md` — which skill/agent to invoke per phase + gate rules |
| Portfolio docs | `../PORTFOLIO_LOCKED_DECISIONS.md`, `../PORTFOLIO_EDA_SPRINT.md` |

## Commands (after scaffold exists)

```bash
make test        # pytest -v --tb=short
make test-cov    # pytest with 90% coverage gate
make lint        # pre-commit run --all-files
make typecheck   # mypy src/ --strict
make check       # lint + typecheck + test-cov
make setup       # pip install -e ".[dev]" + pre-commit install
```

Note: `make test-cov` and `make typecheck` require `src/` directory (created after EDA gate).

## Rules

1. **No invented metrics** — every number from notebook output or saved report.
2. **Simulated experiment** must be labeled in README and reports.
3. Tests use **fixtures only** — never load full Olist in pytest.
4. Pin `random_seed=42` for assignment and bootstrap.
5. Do not copy DataCo / supply-chain dataset into this repo.

## First session default

Execute **Phase 0 EDA only** per `CONTEXT.md` §14 Session 1 unless user explicitly says to scaffold `src/`.
