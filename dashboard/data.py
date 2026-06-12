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
