"""Single source of plain-language definitions for metrics/terms.

Wording is reconciled with docs/mockups/dashboard-v3/index.html tooltips so the
dashboard and the approved mockup stay in sync.
"""

_TERMS: dict[str, str] = {
    "AOV": "Average order value — mean BRL spent per order; the primary metric the cap change targets.",
    "CI": "Confidence interval — the plausible range for the true effect at 95% confidence.",
    "MDE": "Minimum Detectable Effect — the smallest true lift this design reliably catches at the chosen alpha and 80% power.",
    "mde": "Minimum Detectable Effect — the smallest true lift this design reliably catches at the chosen alpha and 80% power.",
    "raw lift": "Treatment minus control AOV with no covariate correction.",
    "raw_lift": "Treatment minus control AOV with no covariate correction.",
    "adjusted lift": "Treatment-control difference after ANCOVA covariate correction, which removes pre-experiment imbalance and usually tightens the interval.",
    "adjusted_lift": "Treatment-control difference after ANCOVA covariate correction, which removes pre-experiment imbalance and usually tightens the interval.",
    "theta": "ANCOVA coefficient on freight_value, estimated pre-injection; used to remove covariate-driven variance.",
    "conversion": "Share of sessions/customers that place an order. A guardrail — the cap change must not hurt it.",
    "D7": "Share of customers returning to purchase within 7 days. A guardrail for retention.",
    "power": "Probability of detecting a true effect of the target size (0.80 = 80% chance).",
    "alpha": "Significance level — the tolerated false-positive rate (0.05 = 5%).",
    "pre-trends": "Treated-minus-control gap in each week before an event; for a valid DiD these must sit inside the band (near zero).",
    "guardrail": "A metric that must NOT move — watched to ensure the change does no harm.",
}


def define(term: str) -> str:
    """Return the plain-language definition for a term, or raise KeyError if unknown."""
    return _TERMS[term]
