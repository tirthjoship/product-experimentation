# Skill Routing — Product Experimentation Analytics

> **Purpose:** Which skill/agent to invoke at each phase of *this* repo, and what gate must
> pass before the next phase opens. Repo-specific projection of
> [`../../SKILLS_AND_SCAFFOLDING_GUIDE.md`](../../SKILLS_AND_SCAFFOLDING_GUIDE.md) onto the
> phase gates in [`../CONTEXT.md`](../CONTEXT.md).
>
> **Read order:** `CONTEXT.md` (source of truth) → this file (routing) → the guide (full table).

---

## Where this project sits

Portfolio slot **4 of 5**. Deliberately **non-ML** — proves SQL + statistics + product
judgment, not modeling. No archetype from the guide fits cleanly, so:

- Architecture: **clean `src/`, NOT full hexagonal** (YAGNI — locked in `CONTEXT.md` §2).
- Guard type: **experiment integrity** (no post-assignment peeking), not column-blocklist
  leakage. Enforced by [`.claude/agents/leakage-auditor.md`](../.claude/agents/leakage-auditor.md).
- Honesty constraint: every report states "simulated RCT on historical Olist data".

---

## The gate rule (non-negotiable)

**Do not scaffold `src/` or build the pipeline until `reports/eda_gate.md` says GO.**
Phase 0 is the only open phase until then. This exists because of the DataCo scar
(`CONTEXT.md` §3): a weak dataset produced a single-feature model and a weak story.

Go criteria (`CONTEXT.md` §7): ≥50k valid orders · conversion computable with <5% ambiguous
status · metric SQL reproducible (DuckDB row counts match pandas).

---

## Phase → skill routing

| Phase | Gate to enter | Invoke | Over | Model |
|-------|---------------|--------|------|-------|
| **0 · EDA** *(current)* | data on disk | run EDA notebook; `ds-methodology-review` if approach is questioned; `grill-me` after, to prove understanding | jumping to `src/` | Sonnet (EDA) / Opus (grill) |
| **1 · Lock metrics** | EDA = GO | `brainstorming` → `writing-plans` to lock `docs/METRICS.md` + `docs/EXPERIMENT_DESIGN.md` | ad-hoc coding | Opus |
| **2 · Build metric SQL** | plan written | `test-driven-development` — SQL in `sql/metrics/` first, Python wraps it, test asserts SQL output == pandas on the same fixture | ad-hoc pytest | Sonnet |
| **3 · Experiment** | metrics pass | `subagent-driven-development` for assignment + analysis + report generator; run `leakage-auditor` agent before commit | `executing-plans` (no shared-file risk here) | Sonnet |
| **4 · Dashboard** | report generates | `frontend-design` only if building real UI; else plain Streamlit | generic code | Sonnet |
| **Review** | branch ready | `requesting-code-review` (standards pass) or `code-review` (multi-agent audit) | self-review | Opus |
| **Ship** | review clean | `finishing-a-development-branch` → `caveman-commit` | guessing | Sonnet |

`security-guidance` fires automatically on every commit — no manual invocation.

---

## Always-on triggers (any phase)

| Situation | Invoke |
|-----------|--------|
| Need library/framework docs (duckdb, scipy, streamlit) | `context7` |
| Explore code structure without reading whole files | `smart-explore` |
| A test fails unexpectedly | `systematic-debugging` before any fix |
| About to claim "done / passing / fixed" | `verification-before-completion` — show command output |
| "Did we solve this before?" | `mem-search` |
| Touching experiment assignment or test fixtures | run `leakage-auditor` agent |

---

## Hard constraints these rules must never break

From `AGENTS.md` + `CLAUDE.md` (all NON-NEGOTIABLE):

1. No invented metrics — every number traces to notebook output or a reproducible command.
2. Simulated effect labeled `SIMULATED_EFFECT`; `RANDOM_SEED = 42` everywhere.
3. Fixture-only tests (≤100 rows, DuckDB in-memory) — never load full Olist in pytest.
4. Every metric defined in SQL first; Python wraps SQL; no logic duplicated.
5. Feature branches only — never commit to `main`/`dev`. Never `--no-verify`.
