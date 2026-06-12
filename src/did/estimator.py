"""TWFE DiD estimator: y_st = β·(treated×post) + α_s + γ_t + ε, cluster-robust by state.
Spec §8. Nothing stochastic — OLS is deterministic."""

from dataclasses import dataclass

import pandas as pd
import statsmodels.formula.api as smf


@dataclass(frozen=True)
class DidResult:
    beta: float
    se: float
    ci: tuple[float, float]
    p: float
    n_obs: int
    n_clusters: int
    outcome: str


def fit_twfe(panel: pd.DataFrame, outcome: str) -> DidResult:
    d = panel.copy()
    d["treated_post"] = (d["treated"] & d["post"]).astype(int)
    d["week_id"] = d["week"].astype(str)
    res = smf.ols(
        f"Q('{outcome}') ~ treated_post + C(customer_state) + C(week_id)", data=d
    ).fit(cov_type="cluster", cov_kwds={"groups": d["customer_state"]})
    ci_lo, ci_hi = res.conf_int().loc["treated_post"]
    return DidResult(
        beta=float(res.params["treated_post"]),
        se=float(res.bse["treated_post"]),
        ci=(float(ci_lo), float(ci_hi)),
        p=float(res.pvalues["treated_post"]),
        n_obs=int(res.nobs),
        n_clusters=int(d["customer_state"].nunique()),
        outcome=outcome,
    )
