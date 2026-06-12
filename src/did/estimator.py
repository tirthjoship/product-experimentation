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


BAND_SD_MULTIPLE = 0.25  # pre-registered: leads must stay within ±0.25 pre-period SD
LEAD_BIN_DAYS = 28  # 4-week lead buckets relative to the boundary


@dataclass(frozen=True)
class PreTrendsResult:
    wald_p: float
    max_lead_abs: float
    band: float
    leads: dict[int, float]
    n_leads: int
    min_detectable_lead: float  # ~2·max lead SE: what this n could have detected


def pretrends_check(
    panel: pd.DataFrame, outcome: str, boundary_date: str
) -> PreTrendsResult:
    pre = panel[~panel["post"]].copy()
    days = (pre["week"] - pd.Timestamp(boundary_date)).dt.days
    pre["rel_bin"] = (days // LEAD_BIN_DAYS).astype(int)  # -1 = 4 weeks before boundary
    lead_bins = sorted(int(b) for b in pre["rel_bin"].unique() if b <= -2)
    cols: list[str] = []
    for b in lead_bins:
        col = f"lead_m{abs(b)}"
        pre[col] = ((pre["rel_bin"] == b) & pre["treated"]).astype(int)
        cols.append(col)
    pre["week_id"] = pre["week"].astype(str)
    res = smf.ols(
        f"Q('{outcome}') ~ {' + '.join(cols)} + C(customer_state) + C(week_id)",
        data=pre,
    ).fit(cov_type="cluster", cov_kwds={"groups": pre["customer_state"]})
    wald = res.wald_test(", ".join(f"{c} = 0" for c in cols), use_f=True, scalar=True)
    leads = {b: float(res.params[f"lead_m{abs(b)}"]) for b in lead_bins}
    max_se = max(float(res.bse[c]) for c in cols)
    return PreTrendsResult(
        wald_p=float(wald.pvalue),
        max_lead_abs=max(abs(v) for v in leads.values()),
        band=BAND_SD_MULTIPLE * float(pre[outcome].std()),
        leads=leads,
        n_leads=len(lead_bins),
        min_detectable_lead=2.0 * max_se,
    )
