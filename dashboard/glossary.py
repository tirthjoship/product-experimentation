"""Single source of plain-language definitions for metrics/terms.

Wording is reconciled with docs/mockups/dashboard-v3/index.html tooltips so the
dashboard and the approved mockup stay in sync.
"""

_MDE = (
    "Smallest detectable effect (MDE): the smallest true lift this design would "
    "reliably catch at the chosen significance level and 80% power."
)
_RAW = (
    "Treatment average minus control average order value, with no covariate correction."
)
_ADJ = (
    "Treatment minus control difference after ANCOVA covariate correction. It removes "
    "pre-experiment imbalance between the groups and usually tightens the interval."
)

_TERMS: dict[str, str] = {
    "AOV": "Average order value (AOV): the mean amount spent per order, in Brazilian reais (R$). It is the primary metric the cap change targets.",
    "CI": "Confidence interval (CI): the plausible range for the true effect at 95% confidence.",
    "MDE": _MDE,
    "mde": _MDE,
    "raw lift": _RAW,
    "raw_lift": _RAW,
    "adjusted lift": _ADJ,
    "adjusted_lift": _ADJ,
    "theta": "ANCOVA coefficient on freight_value, estimated before the effect was injected. It is used to remove variance explained by freight cost.",
    "conversion": "Share of sessions or customers that place an order. It is a guardrail: the cap change must not hurt it.",
    "D7": "D7 repeat purchase: share of customers who buy again within 7 days. A guardrail for retention.",
    "power": "Probability of detecting a true effect of the target size (0.80 means an 80% chance).",
    "alpha": "Significance level: the false-positive rate we are willing to accept (0.05 means 5%).",
    "pre-trends": "Treated-minus-control gap in each week before an event. For a valid difference-in-differences (DiD) test, these gaps must sit inside the band near zero.",
    "guardrail": "A metric that must not move. It is watched to make sure the change does no harm.",
}


def define(term: str) -> str:
    """Return the plain-language definition for a term, or raise KeyError if unknown."""
    return _TERMS[term]
