# ADR-0001: Clean `src/` layout, not full hexagonal

- **Status:** accepted
- **Date:** 2026-06-09
- **Deciders:** Tirth Joshi

## Context

The portfolio standard is hexagonal architecture (ports & adapters) for ML projects, and the
sibling repos (supply-chain, stock, healthcare) follow it. This project is different in kind:
it is a SQL + statistics analytics deliverable, not a model-serving system. It has one input
source (Olist CSVs via DuckDB) and one output (a markdown report, later a Streamlit view).
Full hexagonal ceremony — domain/application/adapters, port interfaces, dependency inversion —
would add structure with no consumer.

## Decision

Use a clean `src/` layout: `src/metrics/`, `src/experiment/`, `src/report/`, `src/io/`, with
SQL living in `sql/`. No ports/adapters layer.

## Options considered

- **Chosen — clean `src/`:** matches the project's actual shape (one source, one sink); keeps
  files focused; SQL stays the single definition of each metric.
- **Full hexagonal:** rejected as YAGNI — no second adapter or domain-invariant complexity to
  justify the indirection.
- **Flat scripts / notebook-only:** rejected — no test seams, no reuse, fails the repo's
  testing and typing standards.

## Consequences

Lower ceremony and faster iteration. The boundary that matters here is SQL-vs-Python (enforced
by parity tests), not domain-vs-adapter. Revisit if the project grows a real-time path or a
second data source — that would justify ports.

## Links

`CONTEXT.md` §2 (locked decisions).
