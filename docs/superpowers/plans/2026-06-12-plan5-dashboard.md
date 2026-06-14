# Plan 5 — Results Dashboard (Streamlit) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Read-only Streamlit dashboard surfacing committed `reports/*.json` — story tab (verdict, motivation, forest plot, DiD honest rejection) + interactive scenario explorer — with fixture tests, CI smoke gate, and a deploy path.

**Architecture:** Pure layer (`dashboard/data.py` typed loaders, `dashboard/charts.py` plotly builders, `dashboard/theme.py`) carries all logic and the 90% coverage gate; `dashboard/sections/*` + `app.py` are render-only glue excluded from coverage. Verdicts are READ from JSON, never recomputed. Fail loud: missing files/fields raise `ReportSchemaError`, never default values.

**Tech Stack:** Python 3.12, Streamlit ≥1.40, Plotly, pytest + Hypothesis (fixtures only), mypy strict, existing GitHub Actions CI.

**Spec:** `docs/superpowers/specs/2026-06-12-plan5-dashboard-design.md`

**Branch:** create `feat/plan5-dashboard` off `dev` before Task 1.

**Key facts the implementer must know:**
- `reports/did_feasibility.json` is a **top-level LIST** (one event). `leads` is a dict keyed by **string negatives** (`"-5"`…`"-2"`).
- `reports/experiment_001.json` has **no `verdict` field**. The hero verdict is read from the `"large"` scenario in `reports/experiment_scenarios.json`. Never compute a verdict in dashboard code.
- Use `.venv/bin/pytest`, `.venv/bin/mypy`, `.venv/bin/python` (bare `python` may not resolve).
- Commit with `SKIP=gitleaks git commit ...` (disk-space caveat; CI runs gitleaks server-side). Never `--no-verify`.

---

### Task 1: Tooling — declare plotly, packaging, mypy, coverage, Makefile

**Files:**
- Modify: `pyproject.toml`
- Modify: `Makefile`

- [ ] **Step 1: pyproject — add plotly to dashboard extra**

In `[project.optional-dependencies]`, change:

```toml
dashboard = [
    "streamlit>=1.40.0",
    "plotly>=5.24.0",
]
```

- [ ] **Step 2: pyproject — package dashboard/ so CI editable-install can import it**

```toml
[tool.setuptools.packages.find]
include = ["src*", "dashboard*"]
```

- [ ] **Step 3: pyproject — mypy override for plotly (untyped)**

Extend the existing third-party override list:

```toml
[[tool.mypy.overrides]]
module = ["pandas.*", "duckdb.*", "scipy.*", "matplotlib.*", "numpy.*", "statsmodels.*", "plotly.*"]
ignore_missing_imports = true
```

Do NOT add `dashboard/` to `exclude` — it is strict-checked.

- [ ] **Step 4: pyproject — coverage omit for render glue (precise paths)**

Add new section:

```toml
[tool.coverage.run]
omit = ["dashboard/sections/*", "dashboard/app.py"]
```

- [ ] **Step 5: Makefile — extend typecheck + test-cov, add dashboard targets**

```makefile
test-cov:
	pytest tests/ -v --cov=src --cov=dashboard --cov-fail-under=90 --tb=short

typecheck:
	mypy src/ scripts/ dashboard/ --strict

dashboard:
	.venv/bin/python -m streamlit run dashboard/app.py

dashboard-smoke:
	.venv/bin/python scripts/dashboard_smoke.py
```

Add `dashboard dashboard-smoke` to the `.PHONY` line.

- [ ] **Step 6: install dashboard extra locally**

Run: `.venv/bin/pip install -e ".[dev,dashboard]"`
Expected: plotly + streamlit installed, no resolver errors.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml Makefile
SKIP=gitleaks git commit -m "chore: declare plotly dep, dashboard packaging, mypy/coverage config for Plan 5"
```

---

### Task 2: `dashboard/theme.py` (TDD)

**Files:**
- Create: `dashboard/__init__.py` (empty)
- Create: `dashboard/theme.py`
- Create: `tests/dashboard/__init__.py` (empty)
- Test: `tests/dashboard/test_theme.py`

- [ ] **Step 1: Write the failing test**

```python
"""Tests for dashboard theme — verdict colors and plotly layout defaults."""

import pytest

from dashboard import theme


def test_verdict_colors_are_semantic() -> None:
    assert theme.verdict_color("SHIP") == theme.GREEN
    assert theme.verdict_color("DO NOT SHIP") == theme.RED
    assert theme.verdict_color("NEED MORE DATA") == theme.AMBER


def test_unknown_verdict_raises() -> None:
    with pytest.raises(ValueError, match="Unknown verdict"):
        theme.verdict_color("MAYBE")


def test_plotly_layout_merges_overrides() -> None:
    layout = theme.plotly_layout(title="x")
    assert layout["title"] == "x"
    assert layout["showlegend"] is False
    assert layout["paper_bgcolor"] == "white"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/dashboard/test_theme.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dashboard'` (after creating the empty `__init__.py` files, import error on `theme`).

- [ ] **Step 3: Write `dashboard/theme.py`**

```python
"""Visual constants and plotly defaults — 'lab notebook meets financial terminal'.

Color carries meaning ONLY: verdict colors are semantic; everything else is ink.
"""

from typing import Any

PAPER = "#FAF8F3"
CARD_BORDER = "#E5E0D5"
INK = "#1A1A1A"
SLATE = "#5A6B7B"
GREEN = "#2E7D4F"
RED = "#C0392B"
AMBER = "#C99A2E"

FONT_BODY = "Source Sans 3, sans-serif"
FONT_DISPLAY = "Fraunces, serif"
FONT_MONO = "IBM Plex Mono, monospace"

_VERDICT_COLORS = {"SHIP": GREEN, "DO NOT SHIP": RED, "NEED MORE DATA": AMBER}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Source+Sans+3:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap');
.stApp { background-color: #FAF8F3; }
html, body, p, li, label { font-family: 'Source Sans 3', sans-serif; color: #1A1A1A; }
h1, h2, h3 { font-family: 'Fraunces', serif; color: #1A1A1A; }
code { font-family: 'IBM Plex Mono', monospace; }
.section-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem;
  letter-spacing: 0.12em; color: #5A6B7B; text-transform: uppercase; }
</style>
"""


def verdict_color(verdict: str) -> str:
    """Map a verdict string (read from reports JSON) to its semantic color."""
    try:
        return _VERDICT_COLORS[verdict]
    except KeyError:
        raise ValueError(f"Unknown verdict: {verdict!r}") from None


def plotly_layout(**overrides: Any) -> dict[str, Any]:
    """Base plotly layout: white card, body font, no legend, no clutter."""
    base: dict[str, Any] = {
        "paper_bgcolor": "white",
        "plot_bgcolor": "white",
        "font": {"family": FONT_BODY, "color": INK, "size": 14},
        "margin": {"l": 70, "r": 40, "t": 60, "b": 50},
        "showlegend": False,
    }
    base.update(overrides)
    return base
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/dashboard/test_theme.py -v`
Expected: 3 PASS.

- [ ] **Step 5: Typecheck and commit**

Run: `.venv/bin/mypy dashboard/ --strict` — expected: clean.

```bash
git add dashboard/__init__.py dashboard/theme.py tests/dashboard/__init__.py tests/dashboard/test_theme.py
SKIP=gitleaks git commit -m "feat: dashboard theme — semantic verdict colors, plotly defaults, CSS"
```

---

### Task 3: Test fixtures (hand-built, tiny)

**Files:**
- Create: `tests/dashboard/fixtures/experiment.json`
- Create: `tests/dashboard/fixtures/scenarios.json`
- Create: `tests/dashboard/fixtures/motivation.json`
- Create: `tests/dashboard/fixtures/did.json`

- [ ] **Step 1: `tests/dashboard/fixtures/experiment.json`**

```json
{
  "sample_sizes": {"control": 100, "treatment": 98},
  "aov": {"control": 150.0, "treatment": 160.15, "lift": 10.15, "ci": [7.36, 13.11], "p": 0.001},
  "conversion": {"control": 0.97, "treatment": 0.9718, "z": 1.71, "p": 0.087, "ci": [-0.0003, 0.0039]},
  "d7": {"control": 0.0088, "treatment": 0.0084},
  "mde": {"aov": 4.32, "conversion": 0.003},
  "simulated_effect": 0.05,
  "alpha": 0.05,
  "aov_adjusted": {"control": 151.0, "treatment": 159.63, "lift": 8.63, "ci": [6.15, 11.15], "theta": 4.96, "ci_width_ratio": 0.868},
  "baseline_balance": {"order_value_gap": 0.0129}
}
```

- [ ] **Step 2: `tests/dashboard/fixtures/scenarios.json`** (3 elements — adverse / null / large)

```json
[
  {
    "sample_sizes": {"control": 100, "treatment": 98},
    "aov": {"control": 150.0, "treatment": 143.96, "lift": -6.04, "ci": [-8.69, -3.24], "p": 0.00001},
    "conversion": {"control": 0.97, "treatment": 0.9718, "z": 1.71, "p": 0.087, "ci": [-0.0003, 0.0039]},
    "d7": {"control": 0.0088, "treatment": 0.0084},
    "mde": {"aov": 3.91, "conversion": 0.003},
    "simulated_effect": -0.05,
    "alpha": 0.05,
    "aov_adjusted": {"control": 151.0, "treatment": 143.44, "lift": -7.56, "ci": [-9.93, -5.19], "theta": 4.96, "ci_width_ratio": 0.869},
    "baseline_balance": {"order_value_gap": 0.0129},
    "scenario": "adverse",
    "verdict": "DO NOT SHIP"
  },
  {
    "sample_sizes": {"control": 100, "treatment": 98},
    "aov": {"control": 150.0, "treatment": 152.06, "lift": 2.06, "ci": [-0.67, 4.93], "p": 0.145},
    "conversion": {"control": 0.97, "treatment": 0.9718, "z": 1.71, "p": 0.087, "ci": [-0.0003, 0.0039]},
    "d7": {"control": 0.0088, "treatment": 0.0084},
    "mde": {"aov": 3.91, "conversion": 0.003},
    "simulated_effect": 0.0,
    "alpha": 0.05,
    "aov_adjusted": {"control": 151.0, "treatment": 151.54, "lift": 0.54, "ci": [-1.83, 2.91], "theta": 4.96, "ci_width_ratio": 0.869},
    "baseline_balance": {"order_value_gap": 0.0129},
    "scenario": "null",
    "verdict": "NEED MORE DATA"
  },
  {
    "sample_sizes": {"control": 100, "treatment": 98},
    "aov": {"control": 150.0, "treatment": 160.15, "lift": 10.15, "ci": [7.36, 13.11], "p": 0.001},
    "conversion": {"control": 0.97, "treatment": 0.9718, "z": 1.71, "p": 0.087, "ci": [-0.0003, 0.0039]},
    "d7": {"control": 0.0088, "treatment": 0.0084},
    "mde": {"aov": 3.91, "conversion": 0.003},
    "simulated_effect": 0.05,
    "alpha": 0.05,
    "aov_adjusted": {"control": 151.0, "treatment": 159.63, "lift": 8.63, "ci": [6.15, 11.15], "theta": 4.96, "ci_width_ratio": 0.868},
    "baseline_balance": {"order_value_gap": 0.0129},
    "scenario": "large",
    "verdict": "SHIP"
  }
]
```

- [ ] **Step 3: `tests/dashboard/fixtures/motivation.json`**

```json
{
  "cohort_window": ["2017-01-01", "2018-09-01"],
  "n_orders": 1000,
  "buckets": [
    {"bucket": "1", "n_orders": 480, "aov": 120.98},
    {"bucket": "2-3", "n_orders": 230, "aov": 136.11},
    {"bucket": "4-6", "n_orders": 160, "aov": 182.69},
    {"bucket": "7+", "n_orders": 130, "aov": 337.03}
  ],
  "share_multi_installment_orders": 0.514,
  "credit_card_value_share": 0.784
}
```

- [ ] **Step 4: `tests/dashboard/fixtures/did.json`** (NOTE: top-level list; string-negative lead keys)

```json
[
  {
    "event": "truckers_strike_2018",
    "outcome": "delivery_days",
    "verdict": "FAIL",
    "conditions": {
      "dated_boundary": {"passed": true, "boundary_date": "2018-05-21"},
      "exogenous_assignment": {
        "passed": true,
        "treated_states": ["AM", "BA", "CE"],
        "control_states": ["SP", "RJ"],
        "excluded_states": ["DF"]
      },
      "parallel_pretrends": {
        "passed": false,
        "wald_p": 0.018,
        "max_lead_abs": 3.4,
        "band": 1.93,
        "n_leads": 4,
        "min_detectable_lead": 3.85,
        "leads": {"-5": -2.48, "-4": -1.32, "-3": -0.83, "-2": 3.4}
      },
      "adequate_n": {
        "passed": false,
        "treated_orders": 3604,
        "control_orders": 27884,
        "week_cell_share_ge_20": 0.45,
        "treated_states": 16,
        "control_states": 7,
        "n_week_cells": 431
      }
    }
  }
]
```

- [ ] **Step 5: Commit**

```bash
git add tests/dashboard/fixtures/
SKIP=gitleaks git commit -m "test: hand-built JSON fixtures for dashboard loaders"
```

---

### Task 4: `dashboard/data.py` — errors, CI validation, experiment loader (TDD)

**Files:**
- Create: `dashboard/data.py`
- Test: `tests/dashboard/test_data_experiment.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Loader tests — experiment_001 shape, fail-loud schema errors."""

import json
from pathlib import Path

import pytest

from dashboard.data import ReportSchemaError, load_experiment

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_experiment_parses_fields() -> None:
    exp = load_experiment(FIXTURES / "experiment.json")
    assert exp.n_control == 100
    assert exp.n_treatment == 98
    assert exp.aov.lift == pytest.approx(10.15)
    assert exp.aov.ci == (7.36, 13.11)
    assert exp.aov_adjusted.lift == pytest.approx(8.63)
    assert exp.aov_adjusted.ci_width_ratio == pytest.approx(0.868)
    assert exp.conversion.ci == (-0.0003, 0.0039)
    assert exp.mde_aov == pytest.approx(4.32)
    assert exp.balance_gap == pytest.approx(0.0129)


def test_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_experiment(FIXTURES / "nope.json")


def test_missing_ci_field_raises_schema_error(tmp_path: Path) -> None:
    raw = json.loads((FIXTURES / "experiment.json").read_text())
    del raw["aov"]["ci"]
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(raw))
    with pytest.raises(ReportSchemaError, match="ci"):
        load_experiment(bad)


def test_inverted_ci_raises_schema_error(tmp_path: Path) -> None:
    raw = json.loads((FIXTURES / "experiment.json").read_text())
    raw["aov"]["ci"] = [13.11, 7.36]
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(raw))
    with pytest.raises(ReportSchemaError, match="lo <= hi"):
        load_experiment(bad)


def test_wrong_length_ci_raises_schema_error(tmp_path: Path) -> None:
    raw = json.loads((FIXTURES / "experiment.json").read_text())
    raw["aov"]["ci"] = [7.36]
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(raw))
    with pytest.raises(ReportSchemaError, match="2 elements"):
        load_experiment(bad)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/dashboard/test_data_experiment.py -v`
Expected: FAIL — `ImportError: cannot import name 'ReportSchemaError'`.

- [ ] **Step 3: Write `dashboard/data.py` (first slice: helpers + experiment loader)**

```python
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
        raise ReportSchemaError(path, field, f"CI must satisfy lo <= hi, got ({lo}, {hi})")
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


def load_experiment(path: Path = REPORTS_DIR / "experiment_001.json") -> ExperimentResult:
    return _parse_experiment(_read_json(path), path)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/dashboard/test_data_experiment.py -v`
Expected: 5 PASS.

- [ ] **Step 5: Typecheck and commit**

Run: `.venv/bin/mypy dashboard/ --strict` — expected clean.

```bash
git add dashboard/data.py tests/dashboard/test_data_experiment.py
SKIP=gitleaks git commit -m "feat: experiment loader with fail-loud schema validation"
```

---

### Task 5: `dashboard/data.py` — scenarios, motivation, DiD loaders (TDD)

**Files:**
- Modify: `dashboard/data.py` (append)
- Test: `tests/dashboard/test_data_other.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Loader tests — scenarios (verdict verbatim), motivation, DiD list shape."""

from pathlib import Path

import pytest

from dashboard.data import load_did, load_motivation, load_scenarios

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_scenarios_reads_verdicts_verbatim() -> None:
    scenarios = load_scenarios(FIXTURES / "scenarios.json")
    assert [s.scenario for s in scenarios] == ["adverse", "null", "large"]
    assert [s.verdict for s in scenarios] == ["DO NOT SHIP", "NEED MORE DATA", "SHIP"]
    null = scenarios[1]
    assert null.result.aov.lift == pytest.approx(2.06)
    assert null.result.aov_adjusted.lift == pytest.approx(0.54)


def test_load_motivation_preserves_bucket_order() -> None:
    stats = load_motivation(FIXTURES / "motivation.json")
    assert [b.bucket for b in stats.buckets] == ["1", "2-3", "4-6", "7+"]
    assert stats.buckets[-1].aov == pytest.approx(337.03)
    assert 0.0 <= stats.share_multi_installment <= 1.0
    assert 0.0 <= stats.credit_card_value_share <= 1.0
    assert stats.n_orders == 1000


def test_load_did_handles_list_shape_and_string_lead_keys() -> None:
    did = load_did(FIXTURES / "did.json")
    assert did.event == "truckers_strike_2018"
    assert did.verdict == "FAIL"
    assert did.dated_boundary_passed is True
    assert did.boundary_date == "2018-05-21"
    assert did.exogenous_passed is True
    assert did.pretrends.passed is False
    assert did.pretrends.wald_p == pytest.approx(0.018)
    assert did.pretrends.band == pytest.approx(1.93)
    # string keys "-5".."-2" parsed to ints
    assert sorted(did.pretrends.leads) == [-5, -4, -3, -2]
    assert did.pretrends.leads[-2] == pytest.approx(3.4)
    assert did.adequate_n.passed is False
    assert did.adequate_n.treated_orders == 3604
    assert did.adequate_n.week_cell_share_ge_20 == pytest.approx(0.45)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/dashboard/test_data_other.py -v`
Expected: FAIL — `ImportError: cannot import name 'load_did'`.

- [ ] **Step 3: Append to `dashboard/data.py`**

```python
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
        share_multi_installment=float(_get(raw, "share_multi_installment_orders", path)),
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/dashboard/ -v`
Expected: all PASS (theme + both data test files).

- [ ] **Step 5: Typecheck and commit**

Run: `.venv/bin/mypy dashboard/ --strict` — expected clean.

```bash
git add dashboard/data.py tests/dashboard/test_data_other.py
SKIP=gitleaks git commit -m "feat: scenarios, motivation, DiD loaders (list shape, string lead keys)"
```

---

### Task 6: Hypothesis property tests on the data transform

**Files:**
- Test: `tests/dashboard/test_properties.py`

- [ ] **Step 1: Write the property tests** (these test existing `_ci` behavior — expected to pass immediately; they pin the invariant)

```python
"""Property tests on the data transform — CI ordering invariants.

Per design review: property-test the transform, NOT plotly trace geometry
(brittle, version-coupled).
"""

from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from dashboard.data import ReportSchemaError, _ci

FAKE = Path("fake.json")

finite = st.floats(allow_nan=False, allow_infinity=False, width=32)


@given(lo=finite, hi=finite)
def test_valid_ci_roundtrips_ordered(lo: float, hi: float) -> None:
    lo, hi = min(lo, hi), max(lo, hi)
    out = _ci({"ci": [lo, hi]}, "ci", FAKE)
    assert out == (lo, hi)
    assert out[0] <= out[1]


@given(lo=finite, hi=finite)
def test_inverted_ci_always_raises(lo: float, hi: float) -> None:
    lo, hi = min(lo, hi), max(lo, hi)
    if lo == hi:
        return
    with pytest.raises(ReportSchemaError):
        _ci({"ci": [hi, lo]}, "ci", FAKE)


@given(st.lists(finite, min_size=0, max_size=5).filter(lambda x: len(x) != 2))
def test_wrong_length_ci_always_raises(raw: list[float]) -> None:
    with pytest.raises(ReportSchemaError):
        _ci({"ci": raw}, "ci", FAKE)
```

- [ ] **Step 2: Run tests**

Run: `.venv/bin/pytest tests/dashboard/test_properties.py -v`
Expected: 3 PASS. If any fail, fix `_ci` in `dashboard/data.py` — the property is the contract.

- [ ] **Step 3: Commit**

```bash
git add tests/dashboard/test_properties.py
SKIP=gitleaks git commit -m "test: Hypothesis properties pin CI-ordering contract in loaders"
```

---

### Task 7: `dashboard/charts.py` — plotly builders (TDD, presence-level assertions)

**Files:**
- Create: `dashboard/charts.py`
- Test: `tests/dashboard/test_charts.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Chart builder tests — presence-level only (no trace-geometry internals)."""

from pathlib import Path

import plotly.graph_objects as go

from dashboard import charts
from dashboard.data import load_did, load_experiment, load_motivation, load_scenarios

FIXTURES = Path(__file__).parent / "fixtures"


def test_bucket_bar_returns_figure_with_all_buckets() -> None:
    stats = load_motivation(FIXTURES / "motivation.json")
    fig = charts.bucket_bar(stats)
    assert isinstance(fig, go.Figure)
    assert list(fig.data[0].x) == ["1", "2-3", "4-6", "7+"]


def test_forest_has_two_rows_zero_line_and_annotations() -> None:
    exp = load_experiment(FIXTURES / "experiment.json")
    fig = charts.forest(exp)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2  # unadjusted + adjusted
    assert len(fig.layout.shapes) >= 1  # zero line
    texts = " ".join(a.text for a in fig.layout.annotations)
    assert "tighter" in texts  # variance-reduction callout
    assert "MDE" in texts  # power callout


def test_coef_plot_has_band_and_flags_violating_lead() -> None:
    did = load_did(FIXTURES / "did.json")
    fig = charts.coef_plot(did.pretrends)
    assert isinstance(fig, go.Figure)
    assert len(fig.layout.shapes) >= 2  # band rect + zero line
    colors = list(fig.data[0].marker.color)
    assert colors.count("#C0392B") == 1  # exactly one lead (-2: 3.4) breaks band 1.93


def test_guardrail_plot_one_row_per_scenario() -> None:
    scenarios = load_scenarios(FIXTURES / "scenarios.json")
    fig = charts.guardrail_plot(scenarios)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 3
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/dashboard/test_charts.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'dashboard.charts'`.

- [ ] **Step 3: Write `dashboard/charts.py`**

```python
"""Pure plotly figure builders. No streamlit imports, no I/O.

Every number plotted comes from a loaded dataclass — charts never compute
statistics, only draw them.
"""

import plotly.graph_objects as go

from dashboard import theme
from dashboard.data import ExperimentResult, MotivationStats, PreTrends, ScenarioResult


def bucket_bar(stats: MotivationStats) -> go.Figure:
    """AOV by installment bucket — the affordability gradient."""
    labels = [b.bucket for b in stats.buckets]
    values = [b.aov for b in stats.buckets]
    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker_color=theme.SLATE,
            text=[f"R${v:,.2f}" for v in values],
            textposition="outside",
            textfont={"family": theme.FONT_MONO, "size": 13},
        )
    )
    fig.update_layout(
        **theme.plotly_layout(
            title="AOV by installment bucket (descriptive, not causal)",
            xaxis_title="installments per order",
            yaxis_title="AOV (BRL)",
        )
    )
    return fig


def _ci_row(
    fig: go.Figure, label: str, lift: float, ci: tuple[float, float], color: str, thick: float
) -> None:
    lo, hi = ci
    fig.add_trace(
        go.Scatter(
            x=[lift],
            y=[label],
            mode="markers",
            marker={"color": color, "size": 13},
            error_x={
                "type": "data",
                "symmetric": False,
                "array": [hi - lift],
                "arrayminus": [lift - lo],
                "color": color,
                "thickness": thick,
                "width": 8,
            },
            name=label,
        )
    )


def forest(result: ExperimentResult, title: str = "AOV lift (BRL) — 95% CI") -> go.Figure:
    """Unadjusted vs adjusted CI overlay; the bias story in one plot."""
    fig = go.Figure()
    _ci_row(fig, "unadjusted", result.aov.lift, result.aov.ci, theme.SLATE, 1.5)
    _ci_row(
        fig, "adjusted (ANCOVA)", result.aov_adjusted.lift, result.aov_adjusted.ci, theme.INK, 3.5
    )
    fig.add_vline(x=0.0, line_dash="dash", line_color=theme.RED, line_width=1)
    shrink = round((1.0 - result.aov_adjusted.ci_width_ratio) * 100)
    fig.add_annotation(
        text=f"adjusted CI {shrink}% tighter (ratio {result.aov_adjusted.ci_width_ratio:.3f}"
        " ≈ √(1−r²) optimum)",
        xref="paper",
        yref="paper",
        x=0.99,
        y=1.12,
        showarrow=False,
        font={"family": theme.FONT_MONO, "size": 12, "color": theme.SLATE},
    )
    fig.add_annotation(
        text=f"MDE ≥ R${result.mde_aov:.2f} at α={result.alpha}",
        xref="paper",
        yref="paper",
        x=0.99,
        y=1.04,
        showarrow=False,
        font={"family": theme.FONT_MONO, "size": 12, "color": theme.SLATE},
    )
    fig.update_layout(
        **theme.plotly_layout(title=title, xaxis_title="lift (BRL)", height=300)
    )
    return fig


def coef_plot(pre: PreTrends) -> go.Figure:
    """Lead coefficients vs ±band — visual proof of the honest DiD rejection."""
    leads = sorted(pre.leads)
    values = [pre.leads[k] for k in leads]
    colors = [theme.RED if abs(v) > pre.band else theme.SLATE for v in values]
    fig = go.Figure(
        go.Scatter(
            x=leads,
            y=values,
            mode="markers+lines",
            marker={"color": colors, "size": 13},
            line={"color": theme.SLATE, "width": 1},
        )
    )
    fig.add_hrect(
        y0=-pre.band, y1=pre.band, fillcolor=theme.SLATE, opacity=0.12, line_width=0
    )
    fig.add_hline(y=0.0, line_dash="dash", line_color=theme.INK, line_width=1)
    fig.add_annotation(
        text=f"Wald p = {pre.wald_p:.3f} (gate needs > 0.10) · max |lead| = "
        f"{pre.max_lead_abs:.2f} > band {pre.band:.2f}",
        xref="paper",
        yref="paper",
        x=0.99,
        y=1.08,
        showarrow=False,
        font={"family": theme.FONT_MONO, "size": 12, "color": theme.RED},
    )
    fig.update_layout(
        **theme.plotly_layout(
            title="Pre-trends: lead coefficients (treated − control)",
            xaxis_title="weeks before boundary",
            yaxis_title="coefficient (delivery days)",
            height=350,
        )
    )
    return fig


def guardrail_plot(scenarios: list[ScenarioResult]) -> go.Figure:
    """Delivered-rate difference + CI per scenario, colored by verdict."""
    fig = go.Figure()
    for s in scenarios:
        g = s.result.conversion
        diff = g.treatment - g.control
        _ci_row(fig, s.scenario, diff, g.ci, theme.verdict_color(s.verdict), 2.0)
    fig.add_vline(x=0.0, line_dash="dash", line_color=theme.INK, line_width=1)
    fig.update_layout(
        **theme.plotly_layout(
            title="Guardrail: delivered-rate difference — 95% CI",
            xaxis_title="treatment − control (delivered rate)",
            height=300,
        )
    )
    return fig
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/dashboard/test_charts.py -v`
Expected: 4 PASS.

- [ ] **Step 5: Typecheck and commit**

Run: `.venv/bin/mypy dashboard/ --strict` — expected clean (plotly is in the ignore-missing-imports override).

```bash
git add dashboard/charts.py tests/dashboard/test_charts.py
SKIP=gitleaks git commit -m "feat: plotly chart builders — forest, pre-trends coef, bucket bar, guardrail"
```

---

### Task 8: Sections + app shell (render glue — no unit tests, coverage-omitted)

**Files:**
- Create: `dashboard/sections/__init__.py` (empty)
- Create: `dashboard/sections/hero.py`
- Create: `dashboard/sections/motivation.py`
- Create: `dashboard/sections/notes.py`
- Create: `dashboard/sections/results.py`
- Create: `dashboard/sections/did.py`
- Create: `dashboard/sections/scenarios.py`
- Create: `dashboard/sections/guardrail.py`
- Create: `dashboard/app.py`

- [ ] **Step 1: `dashboard/sections/hero.py`**

```python
"""Hero: verdict badge + simulated-experiment disclaimer. Verdict READ from JSON."""

import streamlit as st

from dashboard import theme
from dashboard.data import ExperimentResult


def render(exp: ExperimentResult, verdict: str) -> None:
    st.markdown('<p class="section-label">00 / Decision</p>', unsafe_allow_html=True)
    st.warning(
        "**Simulated experiment.** Olist has no native A/B test. Variants are assigned "
        "by hashed `customer_unique_id` (seed 42) on historical data; the treatment "
        "effect is a labeled synthetic injection. Methodology demo — not a real lift."
    )
    color = theme.verdict_color(verdict)
    lo, hi = exp.aov_adjusted.ci
    st.markdown(
        f'<h1 style="font-family:Fraunces,serif;font-size:3.2rem;margin-bottom:0">'
        f'<span style="color:{color}">{verdict}</span> — installment cap 6x → 10x</h1>'
        f'<p style="font-family:IBM Plex Mono,monospace;font-size:1.1rem;color:{theme.SLATE}">'
        f"AOV +{exp.aov_adjusted.lift:.2f} BRL · covariate-adjusted 95% CI "
        f"({lo:.2f}, {hi:.2f}) · n = {exp.n_control:,} / {exp.n_treatment:,}</p>",
        unsafe_allow_html=True,
    )
```

- [ ] **Step 2: `dashboard/sections/motivation.py`**

```python
"""Motivation: real Olist descriptive numbers — the affordability mechanism."""

import streamlit as st

from dashboard import charts
from dashboard.data import MotivationStats


def render(stats: MotivationStats) -> None:
    st.markdown('<p class="section-label">01 / Motivation</p>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Orders paid in >1 installment", f"{stats.share_multi_installment:.1%}")
    c2.metric("Credit-card share of payment value", f"{stats.credit_card_value_share:.1%}")
    c3.metric("Cohort orders", f"{stats.n_orders:,}")
    st.plotly_chart(charts.bucket_bar(stats), use_container_width=True)
    st.caption(
        "Descriptive, not causal: the gradient shows the affordability mechanism exists. "
        "Estimating what the cap change *causes* is the experiment's job."
    )
```

- [ ] **Step 3: `dashboard/sections/notes.py`**

```python
"""How to read this — 3 bullets, link out for depth. No prose wall."""

import streamlit as st


def render() -> None:
    st.markdown('<p class="section-label">02 / How to read this</p>', unsafe_allow_html=True)
    st.markdown(
        "- **Randomization:** by `customer_unique_id` hash (seed 42) — customer-level, "
        "since a customer must always see the same cap.\n"
        "- **Inference:** BCa bootstrap CI on the AOV difference + ANCOVA adjustment on "
        "pre-treatment `freight_value` (removes baseline arm imbalance, tightens the CI).\n"
        "- **Decision rule:** ship only if the *adjusted* CI excludes zero and the "
        "delivered-rate guardrail shows no harm.\n\n"
        "Full memo: [`reports/experiment_001_readout.md`]"
        "(https://github.com/tirthjoship/product-experimentation-analytics/blob/main/"
        "reports/experiment_001_readout.md)"
    )
```

- [ ] **Step 4: `dashboard/sections/results.py`**

```python
"""Results: forest plot (bias story) + guardrail row."""

import streamlit as st

from dashboard import charts
from dashboard.data import ExperimentResult


def render(exp: ExperimentResult) -> None:
    st.markdown('<p class="section-label">03 / Results</p>', unsafe_allow_html=True)
    st.plotly_chart(charts.forest(exp), use_container_width=True)
    st.markdown(
        "Two rows on purpose: random assignment put slightly higher-value customers in "
        f"treatment (baseline gap {exp.balance_gap:.1%}). The adjusted row is the "
        "decision basis; showing both keeps the bias visible and auditable."
    )
    g = exp.conversion
    lo, hi = g.ci
    st.markdown(
        f"**Guardrail — delivered rate:** control {g.control:.4f} vs treatment "
        f"{g.treatment:.4f}, diff CI ({lo:+.4f}, {hi:+.4f}) — no detectable harm."
    )
```

- [ ] **Step 5: `dashboard/sections/did.py`**

```python
"""Plan 4 DiD: the honest rejection — gate checklist + pre-trends plot."""

import streamlit as st

from dashboard import charts
from dashboard.data import DidFeasibility

_CHECK = {True: "✅ PASS", False: "❌ FAIL"}


def render(did: DidFeasibility) -> None:
    st.markdown(
        '<p class="section-label">04 / Natural experiment — honest rejection</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"**Event:** {did.event} (boundary {did.boundary_date}) · "
        f"**outcome:** {did.outcome} · **verdict: {did.verdict}**"
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Dated boundary", _CHECK[did.dated_boundary_passed])
    c2.metric("Exogenous assignment", _CHECK[did.exogenous_passed])
    c3.metric("Parallel pre-trends", _CHECK[did.pretrends.passed])
    c4.metric("Adequate n", _CHECK[did.adequate_n.passed])
    st.plotly_chart(charts.coef_plot(did.pretrends), use_container_width=True)
    n = did.adequate_n
    st.markdown(
        f"Density also failed: {n.week_cell_share_ge_20:.1%} of week-cells had ≥20 orders "
        f"(gate needs 80%) — treated {n.treated_orders:,} orders across "
        f"{n.treated_states} states vs control {n.control_orders:,} across "
        f"{n.control_states}."
    )
    st.markdown(
        "Per the pre-registered protocol, **no post-period estimate was computed** — the "
        "event catalog was committed before any data query (git-verifiable). "
        "The rejection is the deliverable: it shows the gate has teeth. "
        "Full record: ADR 0009."
    )
```

- [ ] **Step 6: `dashboard/sections/scenarios.py`**

```python
"""Interactive: scenario radio → verdict flip + CI plot. All numbers precomputed."""

import streamlit as st

from dashboard import charts, theme
from dashboard.data import ScenarioResult

_LABELS = {
    "adverse": "adverse (injected −5%)",
    "null": "null (injected 0%)",
    "large": "large (injected +5%)",
}


def render(scenarios: list[ScenarioResult]) -> None:
    st.markdown('<p class="section-label">05 / Scenario explorer</p>', unsafe_allow_html=True)
    st.markdown(
        "Same pipeline, three injected effects — the decision rule must reject harm and "
        "withhold judgment on null, not just approve the favorable case."
    )
    names = [s.scenario for s in scenarios]
    chosen = st.radio(
        "Injected effect scenario",
        names,
        format_func=lambda n: _LABELS.get(n, n),
        horizontal=True,
    )
    s = next(sc for sc in scenarios if sc.scenario == chosen)
    color = theme.verdict_color(s.verdict)
    st.markdown(
        f'<h2 style="color:{color};font-family:Fraunces,serif">{s.verdict}</h2>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        charts.forest(s.result, title=f"AOV lift — scenario: {chosen}"),
        use_container_width=True,
    )
    raw, adj = s.result.aov.lift, s.result.aov_adjusted.lift
    st.markdown(
        f"Raw lift **{raw:+.2f}** → adjusted **{adj:+.2f}** BRL. "
        "The gap is baseline imbalance the ANCOVA removes — in the null scenario the "
        "raw number alone would overstate the effect."
    )
    if s.verdict == "NEED MORE DATA":
        st.info(
            f"Adjusted CI includes zero and the effect is below the detectable floor "
            f"(MDE ≈ R${s.result.mde_aov:.2f}): the honest call is more data, not a verdict."
        )
```

- [ ] **Step 7: `dashboard/sections/guardrail.py`**

```python
"""Interactive: delivered-rate guardrail across all scenarios."""

import streamlit as st

from dashboard import charts
from dashboard.data import ScenarioResult


def render(scenarios: list[ScenarioResult]) -> None:
    st.markdown('<p class="section-label">06 / Guardrail panel</p>', unsafe_allow_html=True)
    st.plotly_chart(charts.guardrail_plot(scenarios), use_container_width=True)
    st.caption(
        "Delivered-rate difference is statistically indistinguishable from zero in every "
        "scenario — the injected effect targets AOV only, and the guardrail correctly "
        "stays quiet."
    )
```

- [ ] **Step 8: `dashboard/app.py`**

```python
"""Tab shell. Per-section isolation: one broken section never kills the page.

Loaders are wrapped in st.cache_data HERE (not in data.py) so data.py stays
pure and fixture-testable. Cached returns are frozen dataclasses of plain
primitives — safe for Streamlit's serialized cache.
"""

from collections.abc import Callable

import streamlit as st

from dashboard import data, theme
from dashboard.sections import did, guardrail, hero, motivation, notes, results, scenarios

st.set_page_config(
    page_title="Olist Product Experimentation", page_icon="📋", layout="wide"
)
st.markdown(theme.CSS, unsafe_allow_html=True)

_experiment = st.cache_data(data.load_experiment)
_scenarios = st.cache_data(data.load_scenarios)
_motivation = st.cache_data(data.load_motivation)
_did = st.cache_data(data.load_did)


def _render(name: str, fn: Callable[[], None]) -> None:
    """Fail loud per section; siblings survive."""
    try:
        fn()
    except FileNotFoundError as exc:
        st.error(f"Section '{name}': {exc} — regenerate with the matching make target.")
    except data.ReportSchemaError as exc:
        st.error(f"Section '{name}': schema error — {exc}")


def _headline_verdict() -> str:
    """Hero verdict is READ from the 'large' scenario in scenarios JSON —
    experiment_001.json carries no verdict field and we never recompute one."""
    large = next(s for s in _scenarios() if s.scenario == "large")
    return large.verdict


story_tab, interactive_tab = st.tabs(["Story", "Interactive"])

with story_tab:
    _render("hero", lambda: hero.render(_experiment(), _headline_verdict()))
    st.divider()
    _render("motivation", lambda: motivation.render(_motivation()))
    st.divider()
    _render("notes", notes.render)
    st.divider()
    _render("results", lambda: results.render(_experiment()))
    st.divider()
    _render("did", lambda: did.render(_did()))

with interactive_tab:
    _render("scenarios", lambda: scenarios.render(_scenarios()))
    st.divider()
    _render("guardrail", lambda: guardrail.render(_scenarios()))
```

- [ ] **Step 9: Typecheck + full test suite**

Run: `.venv/bin/mypy src/ scripts/ dashboard/ --strict`
Expected: clean. If `st.cache_data` typing fights strict mode, add a targeted
`# type: ignore[arg-type]` on those four lines ONLY (no blanket ignores).

Run: `.venv/bin/pytest tests/ -v --tb=short`
Expected: all existing 132 + new dashboard tests PASS.

- [ ] **Step 10: Manual render check**

Run: `make dashboard` (i.e. `.venv/bin/python -m streamlit run dashboard/app.py`)
Expected: app serves on localhost:8501; both tabs render all sections against real
`reports/`; scenario radio flips verdict color/badge; no error cards visible.
Stop with Ctrl-C.

- [ ] **Step 11: Commit**

```bash
git add dashboard/sections/ dashboard/app.py
SKIP=gitleaks git commit -m "feat: dashboard sections and app shell with per-section error isolation"
```

---

### Task 9: Smoke script + Makefile target + CI job

**Files:**
- Create: `scripts/dashboard_smoke.py`
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: `scripts/dashboard_smoke.py`** (mypy-strict checked — `scripts/` is in the typecheck path)

```python
"""Schema-drift guard: run every dashboard loader against committed reports/.

If a report writer renames a field, this fails in CI before a broken
dashboard reaches the deployed app. Run via `make dashboard-smoke`.
"""

from dashboard.data import load_did, load_experiment, load_motivation, load_scenarios


def main() -> None:
    exp = load_experiment()
    scenarios = load_scenarios()
    motivation = load_motivation()
    did = load_did()

    if len(scenarios) != 3:
        raise SystemExit(f"expected 3 scenarios, got {len(scenarios)}")
    if not any(s.scenario == "large" for s in scenarios):
        raise SystemExit("missing 'large' scenario (hero verdict source)")
    if not did.pretrends.leads:
        raise SystemExit("DiD pre-trends leads empty")

    print(
        "dashboard-smoke OK — "
        f"experiment n={exp.n_control + exp.n_treatment:,}, "
        f"{len(scenarios)} scenarios, "
        f"{len(motivation.buckets)} buckets, "
        f"DiD verdict={did.verdict}"
    )


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run locally**

Run: `make dashboard-smoke`
Expected: `dashboard-smoke OK — experiment n=99,092, 3 scenarios, 4 buckets, DiD verdict=FAIL`

- [ ] **Step 3: CI — install dashboard extra in test job + add smoke job**

In `.github/workflows/ci.yml`, change the test job install line to include the dashboard extra (chart tests import plotly), update the coverage flags, and append the smoke job:

```yaml
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev,dashboard]"
      - name: Run tests with coverage
        run: |
          if [ -d "src" ]; then
            pytest tests/ -v --tb=short --cov=src --cov=dashboard --cov-fail-under=90
          else
            echo "src/ not yet created (Phase 0) — running tests without coverage gate"
            pytest tests/ -v --tb=short || true
          fi

  dashboard-smoke:
    name: Dashboard smoke (schema drift)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev,dashboard]"
      - name: Run loaders against committed reports
        run: python scripts/dashboard_smoke.py
```

- [ ] **Step 4: Verify everything still passes locally**

Run: `make check`
Expected: lint + `mypy src/ scripts/ dashboard/ --strict` + `pytest --cov=src --cov=dashboard --cov-fail-under=90` all pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/dashboard_smoke.py .github/workflows/ci.yml
SKIP=gitleaks git commit -m "ci: dashboard smoke job guards report-schema drift"
```

---

### Task 10: README — dashboard section, screenshots, deploy docs

**Files:**
- Modify: `README.md` (add a "Live dashboard" section near the top, after the existing intro/disclaimer)
- Create: `docs/img/` (screenshots — see Step 2)

- [ ] **Step 1: Add README section** (place directly after the simulated-experiment disclaimer; adjust anchor text to match existing README structure):

```markdown
## 📊 Live dashboard

![Story tab — verdict, forest plot](docs/img/dashboard-story.png)
![Interactive tab — scenario explorer](docs/img/dashboard-scenarios.png)

**[Open the live dashboard ↗](<APP_URL>)** — read-only view over the committed
`reports/*.json`: the SHIP decision with covariate-adjusted CIs, the scenario
explorer (watch the verdict flip on adverse/null/large injected effects), and the
Plan 4 DiD honest rejection with its pre-trends evidence.

Run locally:

​```bash
pip install -e ".[dashboard]"
make dashboard        # streamlit run dashboard/app.py
​```

> The app may take ~30–60 s to wake from Community Cloud sleep — the screenshots
> above show the same content.
```

- [ ] **Step 2: Capture screenshots (manual, with the user)**

1. Run `make dashboard`.
2. Capture: (a) Story tab top — hero verdict + disclaimer + forest plot; (b) Interactive tab — scenario radio + flipped verdict; optionally (c) DiD pre-trends plot.
3. Save as `docs/img/dashboard-story.png`, `docs/img/dashboard-scenarios.png` (and `docs/img/dashboard-did.png` if captured).
4. Keep each under ~500 KB (disk + repo size caveat).

- [ ] **Step 3: Deploy (manual, user account required)**

1. Push branch; merge per repo flow (feature → dev → main).
2. On https://share.streamlit.io: new app → repo `tirthjoship/product-experimentation-analytics`, branch `main`, entrypoint `dashboard/app.py`.
3. Advanced settings → Python 3.12. Community Cloud installs from `pyproject.toml`; if it misses the extra, add a `requirements.txt` at repo root containing exactly:
   ```
   streamlit>=1.40.0
   plotly>=5.24.0
   pandas>=2.0.0
   duckdb>=1.0.0
   scipy>=1.12.0
   statsmodels>=0.14.0
   matplotlib>=3.8.0
   ```
4. Replace `<APP_URL>` in README with the real URL. Commit.

- [ ] **Step 4: Commit**

```bash
git add README.md docs/img/
SKIP=gitleaks git commit -m "docs: README dashboard section with screenshots and deploy notes"
```

---

### Task 11: Final verification + docs trail

**Files:**
- Modify: `docs/STATUS.md` (overwrite per protocol)

- [ ] **Step 1: Full gate**

Run: `make check && make dashboard-smoke`
Expected: lint clean, mypy strict clean (src + scripts + dashboard), coverage ≥90%, smoke OK.

- [ ] **Step 2: Overwrite `docs/STATUS.md`** — Plan 5 dashboard state: what shipped, branch/PR, deploy URL status, next actions. Keep ~40 lines. (Also fix the stale "PR #23 merge in progress" line — Plans 1–4 are on main via PR #26.)

- [ ] **Step 3: Push and open PR**

```bash
git push -u origin feat/plan5-dashboard
gh pr create --base dev --title "feat: Plan 5 — results dashboard (Streamlit + plotly, read-only reports)" --body "Implements docs/superpowers/specs/2026-06-12-plan5-dashboard-design.md. Read-only over committed reports/*.json; verdicts read verbatim; fixture-only tests; CI smoke job guards schema drift."
```

Expected: PR opens; CI runs test + dashboard-smoke + lint + security jobs green.

---

## Self-review (done at write time)

- **Spec coverage:** §2 loaders → Tasks 4–5; §3 architecture → Tasks 2,7,8; §4 content map (incl. MDE + variance-reduction annotations, bias row, NEED-MORE-DATA power note) → Tasks 7–8; §5 visual direction → Tasks 2,7,8; §6 deps/tooling → Task 1; §7 error handling → Tasks 4,8; §8 testing + smoke → Tasks 3–7,9; §9 deployment → Task 10; §10 YAGNI respected (no sample_results, no live recompute).
- **Placeholder scan:** `<APP_URL>` in Task 10 is a deliberate post-deploy substitution documented in its own step — not an unresolved placeholder.
- **Type consistency:** `ScenarioResult.result: ExperimentResult` used consistently in charts (`s.result.conversion`) and sections; `PreTrends.leads: dict[int, float]` matches loader int-parsing and `coef_plot` sorting; `verdict_color` signature matches all call sites.
