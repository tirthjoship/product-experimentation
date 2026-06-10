"""Inject the labeled synthetic treatment effect. SIMULATED — not a real lift."""

import pandas as pd

from src.constants import SIMULATED_EFFECT


def apply_simulated_effect(
    frame: pd.DataFrame, effect: float = SIMULATED_EFFECT
) -> pd.DataFrame:
    out = frame.copy()
    is_treatment = out["variant"] == "treatment"
    out.loc[is_treatment, "order_value"] = out.loc[is_treatment, "order_value"] * (
        1 + effect
    )
    return out
