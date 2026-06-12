"""Synthetic state×week panel with KNOWN injected DiD effect — the estimator must
recover it (same known-truth philosophy as the simulated RCT, ADR 0004)."""

import numpy as np
import pandas as pd

BOUNDARY = pd.Timestamp("2018-05-21")


def make_synthetic_panel(
    n_treated: int = 8,
    n_control: int = 8,
    n_weeks: int = 24,
    boundary_week: int = 16,
    effect: float = 0.0,
    pre_trend: float = 0.0,  # extra per-week slope on treated states (breaks parallelism)
    noise: float = 0.25,
    base: float = 12.0,
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    weeks = [BOUNDARY + pd.Timedelta(weeks=w - boundary_week) for w in range(n_weeks)]
    states = [f"T{i:02d}" for i in range(n_treated)] + [
        f"C{i:02d}" for i in range(n_control)
    ]
    rows = []
    for s in states:
        treated = s.startswith("T")
        alpha = float(rng.normal(0.0, 2.0))  # state fixed effect
        for w, week in enumerate(weeks):
            gamma = 0.3 * w  # common week trend
            post = w >= boundary_week
            y = base + alpha + gamma + float(rng.normal(0.0, noise))
            if treated:
                y += pre_trend * w
                if post:
                    y += effect
            n_orders = int(rng.integers(30, 80))
            rows.append(
                {
                    "customer_state": s,
                    "week": week,
                    "n_orders": n_orders,
                    "delivery_days": y,
                    "treated": treated,
                    "post": post,
                    "log_orders": float(np.log1p(n_orders)),
                }
            )
    return pd.DataFrame(rows)
