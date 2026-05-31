# CLAUDE.md — Product Experimentation Analytics

Read **`CONTEXT.md`** first — it is the source of truth for locked decisions, dataset, and phase gates.

## Quick reference

| Item | Value |
|------|-------|
| Dataset | Olist Brazilian E-Commerce (Kaggle) |
| Phase | **0 = EDA gate** — do not build full pipeline until `reports/eda_gate.md` says GO |
| Portfolio docs | `../PORTFOLIO_LOCKED_DECISIONS.md`, `../PORTFOLIO_EDA_SPRINT.md` |

## Commands (after scaffold exists)

```bash
make test          # pytest
make lint          # ruff + black
jupyter lab notebooks/00_eda_gate.ipynb
```

## Rules

1. **No invented metrics** — every number from notebook output or saved report.
2. **Simulated experiment** must be labeled in README and reports.
3. Tests use **fixtures only** — never load full Olist in pytest.
4. Pin `random_seed=42` for assignment and bootstrap.
5. Do not copy DataCo / supply-chain dataset into this repo.

## First session default

Execute **Phase 0 EDA only** per `CONTEXT.md` §14 Session 1 unless user explicitly says to scaffold `src/`.
