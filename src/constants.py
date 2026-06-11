"""Single source of truth for experiment parameters. Pinned for reproducibility."""

SEED: int = 42
SIMULATED_EFFECT: float = 0.05
COHORT_START: str = "2017-01-01"
COHORT_END_EXCLUSIVE: str = "2018-09-01"
BOOTSTRAP_RESAMPLES: int = 10_000
ALPHA: float = 0.05
POWER: float = 0.80
IMBALANCE_TOLERANCE: float = 0.05
BASELINE_BALANCE_TOLERANCE: float = (
    0.05  # max relative arm-mean gap on pre-injection metric
)
DELIVERED_STATUS: str = "delivered"
QUANTILES: tuple[float, ...] = (0.25, 0.50, 0.75, 0.90)

# (name, multiplicative effect) — swept so the decision rule shows all three verdicts.
#   adverse: a harmful change (treatment worse) -> DO NOT SHIP
#   null:    no real effect; still exposes the ~2 BRL baseline arm imbalance -> NEED MORE DATA
#   large:   a clear win above the MDE -> SHIP
SCENARIOS: tuple[tuple[str, float], ...] = (
    ("adverse", -0.05),
    ("null", 0.0),
    ("large", 0.05),
)
