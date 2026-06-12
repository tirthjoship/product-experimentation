"""Pre-registered gate (spec §6). Thresholds are constants — locked at the Phase C
commit; changing them after feasibility is a protocol violation, not a refactor."""

from pathlib import Path
from typing import Any

import pandas as pd

from src.did.catalog import ALL_UFS, EventDefinition
from src.did.estimator import pretrends_check
from src.report.results_io import write_results_json

ALPHA_PRETRENDS = 0.10
MIN_CELL_ORDERS = 1_000  # per arm, pre-period (4a, pre side)
MIN_WEEK_CELL_ORDERS = 20  # (4b)
MIN_WEEK_CELL_SHARE = 0.80  # (4b)
MIN_STATES_PER_ARM = 5  # (4c)
MIN_LEADS = 3


def feasibility_counts(panel_pre: pd.DataFrame) -> dict[str, Any]:
    treated = panel_pre[panel_pre["treated"]]
    control = panel_pre[~panel_pre["treated"]]
    return {
        "treated_orders": int(treated["n_orders"].sum()),
        "control_orders": int(control["n_orders"].sum()),
        "week_cell_share_ge_20": float(
            (panel_pre["n_orders"] >= MIN_WEEK_CELL_ORDERS).mean()
        ),
        "treated_states": int(treated["customer_state"].nunique()),
        "control_states": int(control["customer_state"].nunique()),
        "n_week_cells": int(len(panel_pre)),
    }


def evaluate_gate(event: EventDefinition, panel_pre: pd.DataFrame) -> dict[str, Any]:
    fc = feasibility_counts(panel_pre)
    c1 = bool(event.source and event.boundary_date)
    arms = set(event.treated_states) | set(event.control_states)
    c2 = (
        set(event.treated_states).isdisjoint(event.control_states)
        and arms <= ALL_UFS
        and bool(event.treated_states and event.control_states)
    )
    c4 = (
        fc["treated_orders"] >= MIN_CELL_ORDERS
        and fc["control_orders"] >= MIN_CELL_ORDERS
        and fc["week_cell_share_ge_20"] >= MIN_WEEK_CELL_SHARE
        and fc["treated_states"] >= MIN_STATES_PER_ARM
        and fc["control_states"] >= MIN_STATES_PER_ARM
    )
    pt = pretrends_check(panel_pre, event.outcome, event.boundary_date)
    c3 = (
        pt.wald_p > ALPHA_PRETRENDS
        and pt.max_lead_abs <= pt.band
        and pt.n_leads >= MIN_LEADS
    )
    conditions = {
        "dated_boundary": {"passed": c1, "boundary_date": event.boundary_date},
        "exogenous_assignment": {
            "passed": c2,
            "treated_states": list(event.treated_states),
            "control_states": list(event.control_states),
            "excluded_states": list(event.excluded_states),
        },
        "parallel_pretrends": {
            "passed": c3,
            "wald_p": pt.wald_p,
            "max_lead_abs": pt.max_lead_abs,
            "band": pt.band,
            "n_leads": pt.n_leads,
            "min_detectable_lead": pt.min_detectable_lead,
            "leads": {str(k): v for k, v in pt.leads.items()},
        },
        "adequate_n": {"passed": c4, **fc},
    }
    all_pass = c1 and c2 and c3 and c4
    return {
        "event": event.name,
        "outcome": event.outcome,
        "verdict": "GO" if all_pass else "FAIL",
        "conditions": conditions,
    }


def write_verdict(verdict: dict[str, Any], path: Path) -> None:
    write_results_json(verdict, path)
