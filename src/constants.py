"""Single source of truth for experiment parameters. Pinned for reproducibility."""

SEED: int = 42
SIMULATED_EFFECT: float = 0.05
COHORT_START: str = "2017-01-01"
COHORT_END_EXCLUSIVE: str = "2018-09-01"
BOOTSTRAP_RESAMPLES: int = 10_000
ALPHA: float = 0.05
POWER: float = 0.80
IMBALANCE_TOLERANCE: float = 0.05
DELIVERED_STATUS: str = "delivered"
QUANTILES: tuple[float, ...] = (0.25, 0.50, 0.75, 0.90)

# (name, multiplicative effect) — swept to show the decision rule yields all verdicts.
SCENARIOS: tuple[tuple[str, float], ...] = (
    ("null", 0.0),
    ("borderline", 0.025),
    ("large", 0.05),
)
