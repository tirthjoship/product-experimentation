"""Guard against a broken hash or filter producing lopsided variants."""

import pandas as pd

from src.constants import BASELINE_BALANCE_TOLERANCE, IMBALANCE_TOLERANCE
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


def check_metric_balance(
    frame: pd.DataFrame,
    column: str,
    tolerance: float = BASELINE_BALANCE_TOLERANCE,
) -> float:
    """Guard the PRE-injection metric baseline: relative arm-mean gap must be small.

    Catches the imbalance the null scenario exposed (lift +2.06 at zero effect).
    Returns the gap so run() can report it.
    """
    means = frame.groupby("variant")[column].mean()
    ctrl, treat = float(means["control"]), float(means["treatment"])
    if ctrl == 0.0:
        raise ImbalanceError(f"control mean of {column} is zero")
    gap = abs(treat - ctrl) / abs(ctrl)
    if gap > tolerance:
        raise ImbalanceError(
            f"baseline {column} arm gap {gap:.4f} exceeds tolerance {tolerance} "
            f"(control={ctrl:.2f}, treatment={treat:.2f})"
        )
    return gap
