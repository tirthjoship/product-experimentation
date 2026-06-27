# Architecture Decision Records

One file per decision that was non-obvious or expensive to reverse. Each records the context,
the options weighed, and the consequences — so a future reader understands *why*, not just
*what*. Append-only: supersede with a new ADR rather than rewriting.

This is **Tier 2** documentation (read on demand). For the stable "why + locked decisions" read `CONTEXT.md`.

| ADR | Title | Status |
|-----|-------|--------|
| [0001](0001-clean-src-not-hexagonal.md) | Clean `src/` layout, not full hexagonal | accepted |
| [0002](0002-olist-dataset-over-dataco.md) | Olist dataset over DataCo | accepted |
| [0003](0003-eda-gate-before-pipeline.md) | EDA gate before building the pipeline | accepted |
| [0004](0004-simulated-rct-with-injected-effect.md) | Simulated RCT with a labeled injected effect | accepted |
| [0005](0005-aov-primary-conversion-guardrail.md) | AOV primary, conversion guardrail, D7 exploratory | accepted |
| [0006](0006-bootstrap-welch-ztest-inference.md) | Bootstrap CI + Welch t-test + two-proportion z | accepted |
| [0007](0007-covariate-adjustment-not-cuped.md) | ANCOVA on `freight_value`, classic CUPED rejected | accepted |
| [0008](0008-installment-framing-over-free-shipping.md) | Installment-expansion framing over free-shipping | accepted |
| [0009](0009-gated-did-natural-experiment.md) | Gated DiD natural experiment — rejected on Olist (honest FAIL) | accepted |

New ADR: copy `0000-template.md`, bump the number, add a row above.
