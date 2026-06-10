# CLAUDE.md — Product Experimentation Analytics

Read **`CONTEXT.md`** first — it is the source of truth for locked decisions, dataset, and phase gates.

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
