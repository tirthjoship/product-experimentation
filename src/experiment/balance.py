"""Guard against a broken hash or filter producing lopsided variants."""

import pandas as pd

from src.constants import IMBALANCE_TOLERANCE
from src.exceptions import ImbalanceError


def check_balance(frame: pd.DataFrame, tolerance: float = IMBALANCE_TOLERANCE) -> None:
    counts = frame["variant"].value_counts()
    control = int(counts.get("control", 0))
    treatment = int(counts.get("treatment", 0))
    larger = max(control, treatment)
    if larger == 0:
        raise ImbalanceError("no rows in either variant")
    gap = abs(control - treatment) / larger
    if gap > tolerance:
        raise ImbalanceError(
            f"variant imbalance {gap:.3f} exceeds tolerance {tolerance} "
            f"(control={control}, treatment={treatment})"
        )
