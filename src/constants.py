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
