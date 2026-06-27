# ADR-0003: EDA gate before building the pipeline

- **Status:** accepted
- **Date:** 2026-06-09
- **Deciders:** Tirth Joshi

## Context

The DataCo experience (sibling repo) was: build the ML pipeline first, discover the dataset's
signal was weak only afterward. The cost of that ordering is high — code and narrative built on
a foundation that turns out to be shaky.

## Decision

Phase 0 is a hard gate. No `src/` scaffolding or pipeline work until `reports/eda_gate.md`
records a GO against explicit criteria (≥50k valid orders, conversion computable with <5%
ambiguous status, metric SQL reproducible, join orphans <1%).

## Options considered

- **Chosen — gate first:** validate the dataset can carry the intended metrics and experiment
  before investing in the build.
- **Build then validate:** rejected — this is exactly the DataCo failure mode.
- **Skip formal gate, rely on intuition:** rejected — the 97% conversion ceiling and the
  right-censored tail months were not obvious without measuring; intuition would have missed them.

## Consequences

The gate caught three things that reshaped the design *before* any code: conversion is a 97%
ceiling (a fulfillment rate, not checkout), the tail months are right-censored, and D7-within-7d
is too sparse to be primary. Those findings drive ADR-0005. Gate passed GO on 2026-06-09.

## Links

`reports/eda_gate.md`, `CONTEXT.md` §7.
