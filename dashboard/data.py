"""Pure loaders: committed reports/*.json -> frozen dataclasses.

The dashboard renders ONLY numbers present in these files. No recompute,
no defaults: a missing or malformed field raises ReportSchemaError — never
becomes 0, [0, 0], or "N/A" (no-invented-metrics applies to failure modes).
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


class ReportSchemaError(Exception):
    """A report JSON is missing a field or holds a malformed value."""

    def __init__(self, path: Path, field: str, detail: str) -> None:
        self.path = path
        self.field = field
        super().__init__(f"{path.name}: field '{field}' — {detail}")


def _read_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Missing report: {path}")
    with path.open() as f:
        return json.load(f)


def _get(obj: dict[str, Any], field: str, path: Path) -> Any:
    if field not in obj:
        raise ReportSchemaError(path, field, "missing")
    return obj[field]


def _ci(obj: dict[str, Any], field: str, path: Path) -> tuple[float, float]:
    raw = _get(obj, field, path)
    if not isinstance(raw, (list, tuple)) or len(raw) != 2:
        raise ReportSchemaError(path, field, "CI must have exactly 2 elements")
    lo, hi = float(raw[0]), float(raw[1])
    if lo > hi:
        raise ReportSchemaError(
            path, field, f"CI must satisfy lo <= hi, got ({lo}, {hi})"
        )
    return (lo, hi)


@dataclass(frozen=True)
class ArmEffect:
    """Unadjusted treatment-control comparison."""

    control: float
    treatment: float
    lift: float
    ci: tuple[float, float]
    p: float


@dataclass(frozen=True)
class AdjustedEffect:
    """ANCOVA covariate-adjusted comparison (decision basis)."""

    control: float
    treatment: float
    lift: float
    ci: tuple[float, float]
    theta: float
    ci_width_ratio: float


@dataclass(frozen=True)
class GuardrailEffect:
    """Delivered-rate guardrail (two-proportion z-test)."""

    control: float
    treatment: float
    z: float
    p: float
    ci: tuple[float, float]


@dataclass(frozen=True)
class ExperimentResult:
    n_control: int
    n_treatment: int
    aov: ArmEffect
    aov_adjusted: AdjustedEffect
    conversion: GuardrailEffect
    d7_control: float
    d7_treatment: float
    mde_aov: float
    mde_conversion: float
    simulated_effect: float
    alpha: float
    balance_gap: float


def _parse_experiment(raw: dict[str, Any], path: Path) -> ExperimentResult:
    sizes = _get(raw, "sample_sizes", path)
    aov = _get(raw, "aov", path)
    adj = _get(raw, "aov_adjusted", path)
    conv = _get(raw, "conversion", path)
    d7 = _get(raw, "d7", path)
    mde = _get(raw, "mde", path)
    balance = _get(raw, "baseline_balance", path)
    return ExperimentResult(
        n_control=int(_get(sizes, "control", path)),
        n_treatment=int(_get(sizes, "treatment", path)),
        aov=ArmEffect(
            control=float(_get(aov, "control", path)),
            treatment=float(_get(aov, "treatment", path)),
            lift=float(_get(aov, "lift", path)),
            ci=_ci(aov, "ci", path),
            p=float(_get(aov, "p", path)),
        ),
        aov_adjusted=AdjustedEffect(
            control=float(_get(adj, "control", path)),
            treatment=float(_get(adj, "treatment", path)),
            lift=float(_get(adj, "lift", path)),
            ci=_ci(adj, "ci", path),
            theta=float(_get(adj, "theta", path)),
            ci_width_ratio=float(_get(adj, "ci_width_ratio", path)),
        ),
        conversion=GuardrailEffect(
            control=float(_get(conv, "control", path)),
            treatment=float(_get(conv, "treatment", path)),
            z=float(_get(conv, "z", path)),
            p=float(_get(conv, "p", path)),
            ci=_ci(conv, "ci", path),
        ),
        d7_control=float(_get(d7, "control", path)),
        d7_treatment=float(_get(d7, "treatment", path)),
        mde_aov=float(_get(mde, "aov", path)),
        mde_conversion=float(_get(mde, "conversion", path)),
        simulated_effect=float(_get(raw, "simulated_effect", path)),
        alpha=float(_get(raw, "alpha", path)),
        balance_gap=float(_get(balance, "order_value_gap", path)),
    )


def load_experiment(
    path: Path = REPORTS_DIR / "experiment_001.json",
) -> ExperimentResult:
    return _parse_experiment(_read_json(path), path)


@dataclass(frozen=True)
class ScenarioResult:
    """One scenario from the sweep. Verdict is READ from JSON, never recomputed."""

    scenario: str
    verdict: str
    result: ExperimentResult


def load_scenarios(
    path: Path = REPORTS_DIR / "experiment_scenarios.json",
) -> list[ScenarioResult]:
    raw = _read_json(path)
    if not isinstance(raw, list):
        raise ReportSchemaError(path, "<root>", "expected a list of scenarios")
    return [
        ScenarioResult(
            scenario=str(_get(item, "scenario", path)),
            verdict=str(_get(item, "verdict", path)),
            result=_parse_experiment(item, path),
        )
        for item in raw
    ]


def load_grid(
    path: Path = REPORTS_DIR / "experiment_grid.json",
) -> list[ScenarioResult]:
    """What-if grid: each point is a scenario element (same schema/writer as the
    scenario sweep). Verdict is READ from JSON, never recomputed."""
    return load_scenarios(path)


@dataclass(frozen=True)
class Bucket:
    bucket: str
    n_orders: int
    aov: float


@dataclass(frozen=True)
class MotivationStats:
    cohort_start: str
    cohort_end: str
    n_orders: int
    buckets: tuple[Bucket, ...]
    share_multi_installment: float
    credit_card_value_share: float


def load_motivation(
    path: Path = REPORTS_DIR / "installment_motivation.json",
) -> MotivationStats:
    raw = _read_json(path)
    window = _get(raw, "cohort_window", path)
    buckets = tuple(
        Bucket(
            bucket=str(_get(b, "bucket", path)),
            n_orders=int(_get(b, "n_orders", path)),
            aov=float(_get(b, "aov", path)),
        )
        for b in _get(raw, "buckets", path)
    )
    return MotivationStats(
        cohort_start=str(window[0]),
        cohort_end=str(window[1]),
        n_orders=int(_get(raw, "n_orders", path)),
        buckets=buckets,
        share_multi_installment=float(
            _get(raw, "share_multi_installment_orders", path)
        ),
        credit_card_value_share=float(_get(raw, "credit_card_value_share", path)),
    )


@dataclass(frozen=True)
class PreTrends:
    passed: bool
    wald_p: float
    max_lead_abs: float
    band: float
    n_leads: int
    min_detectable_lead: float
    leads: dict[int, float]


@dataclass(frozen=True)
class AdequateN:
    passed: bool
    treated_orders: int
    control_orders: int
    week_cell_share_ge_20: float
    treated_states: int
    control_states: int
    n_week_cells: int


@dataclass(frozen=True)
class DidFeasibility:
    event: str
    outcome: str
    verdict: str
    dated_boundary_passed: bool
    boundary_date: str
    exogenous_passed: bool
    treated_state_codes: tuple[str, ...]
    control_state_codes: tuple[str, ...]
    excluded_state_codes: tuple[str, ...]
    pretrends: PreTrends
    adequate_n: AdequateN


def load_did(path: Path = REPORTS_DIR / "did_feasibility.json") -> DidFeasibility:
    raw = _read_json(path)
    # did_feasibility.json is a TOP-LEVEL LIST (one event today).
    if not isinstance(raw, list) or not raw:
        raise ReportSchemaError(path, "<root>", "expected a non-empty list of events")
    event = raw[0]
    conditions = _get(event, "conditions", path)
    boundary = _get(conditions, "dated_boundary", path)
    exog = _get(conditions, "exogenous_assignment", path)
    pre = _get(conditions, "parallel_pretrends", path)
    n = _get(conditions, "adequate_n", path)
    # leads arrive keyed by STRING negatives ("-5".."-2") — parse to int.
    leads = {int(k): float(v) for k, v in _get(pre, "leads", path).items()}
    return DidFeasibility(
        event=str(_get(event, "event", path)),
        outcome=str(_get(event, "outcome", path)),
        verdict=str(_get(event, "verdict", path)),
        dated_boundary_passed=bool(_get(boundary, "passed", path)),
        boundary_date=str(_get(boundary, "boundary_date", path)),
        exogenous_passed=bool(_get(exog, "passed", path)),
        treated_state_codes=tuple(_get(exog, "treated_states", path)),
        control_state_codes=tuple(_get(exog, "control_states", path)),
        excluded_state_codes=tuple(_get(exog, "excluded_states", path)),
        pretrends=PreTrends(
            passed=bool(_get(pre, "passed", path)),
            wald_p=float(_get(pre, "wald_p", path)),
            max_lead_abs=float(_get(pre, "max_lead_abs", path)),
            band=float(_get(pre, "band", path)),
            n_leads=int(_get(pre, "n_leads", path)),
            min_detectable_lead=float(_get(pre, "min_detectable_lead", path)),
            leads=leads,
        ),
        adequate_n=AdequateN(
            passed=bool(_get(n, "passed", path)),
            treated_orders=int(_get(n, "treated_orders", path)),
            control_orders=int(_get(n, "control_orders", path)),
            week_cell_share_ge_20=float(_get(n, "week_cell_share_ge_20", path)),
            treated_states=int(_get(n, "treated_states", path)),
            control_states=int(_get(n, "control_states", path)),
            n_week_cells=int(_get(n, "n_week_cells", path)),
        ),
    )
