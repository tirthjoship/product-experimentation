# Dashboard v3 — Descriptive & Interactive Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the read-only Plan-5 Streamlit dashboard into a self-explaining, decision-maker-friendly "company dashboard" — persistent header, 5 tabs, plain-language bottom-line tiles, layered hovers (chip rationale + chart ⓘ + glossary), value color-coding, diversified responsive charts, plus a What-if effect-grid and a power calculator — without breaking the read-only / no-invented-metrics architecture.

**Architecture:** Keep v2's split: a PURE layer (`dashboard/data.py`, `charts.py`, `theme.py`, new `glossary.py`, new `valuecolor.py`) carries all logic and keeps the 90% coverage gate; render-only glue (`dashboard/app.py`, `dashboard/sections/*`) is coverage-omitted. Interactivity is honest: What-if reads a precomputed `reports/experiment_grid.json` (built offline by reusing `src.experiment.run_scenarios` + `results_to_json`); the power calculator is analytical (`src.experiment.power`). Every number traces to a committed report or a labeled formula.

**Tech Stack:** Python 3.12, Streamlit ≥1.52, Plotly, duckdb (offline grid build only), pytest, mypy --strict. Use `.venv/bin/...` for all tooling.

**Reference:** The approved clickable mockup is committed at `docs/mockups/dashboard-v3/index.html` (+ `data.json`). It is the source of truth for layout, copy, tooltip text, color logic, and chart choices. Open it while implementing. Spec: `docs/superpowers/specs/2026-06-13-dashboard-v3-descriptive-interactive-design.md`.

**Honesty rules (non-negotiable):** (1) no invented metrics — every number from `reports/*.json` or a labeled analytical formula; (2) SIMULATED + CALCULATOR banners stay loud; (3) tests use fixtures only, never full Olist; (4) verdict comes from the report's existing `recommend()` — the dashboard maps verdict→color, never recomputes the rule.

**Branch:** Extend `feat/plan5-dashboard` (one dashboard PR; v2 not yet PR'd). Confirm clean tree before starting: `git status`.

---

## File Structure

**Create:**
- `scripts/build_experiment_grid.py` — offline: sweep injected effect −10%..+10% @1% → `reports/experiment_grid.json` (reuses `run_scenarios` + `results_to_json`).
- `reports/experiment_grid.json` — generated artifact (committed).
- `dashboard/glossary.py` — single source of term → one-line definition (pure dict + getter).
- `dashboard/valuecolor.py` — pure good/average/poor classification for values (returns a semantic class string), unit-tested thresholds.
- `dashboard/sections/header.py` — persistent project header (title, subtitle, context chips with rationale tooltips).
- `dashboard/sections/overview.py` — Overview tab body.
- `dashboard/sections/whatif.py` — What-if slider over the grid.
- `dashboard/sections/calculator.py` — analytical power calculator.
- `tests/dashboard/test_glossary.py`, `tests/dashboard/test_valuecolor.py`, `tests/dashboard/test_charts_v3.py`, `tests/dashboard/test_data_grid.py`
- `tests/test_build_experiment_grid.py` — fixture-based grid build test.
- `tests/fixtures/experiment_grid.json` — tiny 3-point grid fixture.

**Modify:**
- `dashboard/theme.py` — new palette/fonts (white · Space Grotesk · Inter · IBM Plex Mono · oxblood) + responsive CSS + helper for value-color CSS classes + chart-info/glossary tooltip CSS.
- `dashboard/data.py` — add `load_grid()` (thin wrapper of the scenarios parser on the grid path).
- `dashboard/charts.py` — add builders: `dumbbell`, `range_plot`, `split_bar`, `diverging_marker`, `lift_forest` (guardrail lift-vs-zero), `mde_vs_n`, `power_vs_effect`; allow verdict-coloring of the primary AOV forest dot.
- `dashboard/sections/{hero,results,scenarios,motivation,did,guardrail,notes}.py` — rework into the 5-tab content with tiles, ⓘ tooltips, glossary, value colors. (Some may be absorbed/renamed; see tasks.)
- `dashboard/app.py` — 5-tab shell (Overview / Experiment results / Scenario explorer / Power & design / Natural experiment), persistent header, new caches (`_grid`), responsive columns.
- `scripts/dashboard_smoke.py` — also validate `experiment_grid.json`.
- `Makefile` — add `experiment-grid` target.
- `README.md`, `docs/STATUS.md` — document v3.

**Coverage policy:** `dashboard/sections/*` and `dashboard/app.py` are render-only and stay in the coverage omit list (see `pyproject.toml [tool.coverage.run] omit`). Logic that needs testing lives in `data.py`/`charts.py`/`glossary.py`/`valuecolor.py`/`theme.py`.

---

## Phase 0 — Preflight

### Task 0: Branch + baseline green

- [ ] **Step 1: Confirm branch + clean tree**

Run: `cd "$(git rev-parse --show-toplevel)" && git status && git branch --show-current`
Expected: branch `feat/plan5-dashboard`, working tree clean.

- [ ] **Step 2: Baseline gate green before changes**

Run: `.venv/bin/pytest -q && .venv/bin/mypy dashboard src --strict && .venv/bin/python scripts/dashboard_smoke.py`
Expected: all pass (≈152 tests, mypy clean, smoke green). If not, STOP and fix baseline first.

---

## Phase 1 — What-if effect grid (offline data)

### Task 1: Grid fixture + `load_grid` (TDD)

**Files:**
- Create: `tests/fixtures/experiment_grid.json`
- Create: `tests/dashboard/test_data_grid.py`
- Modify: `dashboard/data.py`

- [ ] **Step 1: Create the tiny grid fixture**

Create `tests/fixtures/experiment_grid.json` — a 3-element list reusing the scenario element shape (copy 3 elements from the real `reports/experiment_scenarios.json` but set distinct `scenario`/`simulated_effect`). Minimum each element needs (to parse via `_parse_experiment`): `sample_sizes`, `aov` (with `ci`), `conversion` (with `ci`), `d7`, `mde`, `simulated_effect`, `alpha`, `aov_adjusted` (with `ci`, `theta`, `ci_width_ratio`), `baseline_balance`, `scenario`, `verdict`. Use effects -0.05, 0.0, 0.05 and verdicts "DO NOT SHIP", "NEED MORE DATA", "SHIP".

- [ ] **Step 2: Write the failing test**

```python
# tests/dashboard/test_data_grid.py
from pathlib import Path

import pytest

from dashboard import data

FIX = Path(__file__).parent.parent / "fixtures" / "experiment_grid.json"


def test_load_grid_parses_all_points() -> None:
    grid = data.load_grid(FIX)
    assert len(grid) == 3
    effects = sorted(p.result.simulated_effect for p in grid)
    assert effects == [-0.05, 0.0, 0.05]
    # verdict is read, never recomputed
    assert {p.verdict for p in grid} == {"DO NOT SHIP", "NEED MORE DATA", "SHIP"}


def test_load_grid_rejects_non_list(tmp_path: Path) -> None:
    bad = tmp_path / "g.json"
    bad.write_text('{"not": "a list"}')
    with pytest.raises(data.ReportSchemaError):
        data.load_grid(bad)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/bin/pytest tests/dashboard/test_data_grid.py -v`
Expected: FAIL — `AttributeError: module 'dashboard.data' has no attribute 'load_grid'`.

- [ ] **Step 4: Implement `load_grid`**

In `dashboard/data.py`, add after `load_scenarios` (a grid point IS a scenario element, so reuse the same parsing):

```python
def load_grid(
    path: Path = REPORTS_DIR / "experiment_grid.json",
) -> list[ScenarioResult]:
    """What-if grid: each point is a scenario element (same schema/writer as the
    scenario sweep). Verdict is READ from JSON, never recomputed."""
    return load_scenarios(path)
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/pytest tests/dashboard/test_data_grid.py -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add dashboard/data.py tests/dashboard/test_data_grid.py tests/fixtures/experiment_grid.json
git commit -m "feat(dashboard): load_grid reads experiment_grid.json as scenario points"
```

### Task 2: Grid build script (TDD with fixture-sized data)

**Files:**
- Create: `scripts/build_experiment_grid.py`
- Create: `tests/test_build_experiment_grid.py`
- Modify: `Makefile`

- [ ] **Step 1: Write the failing test (uses the fixture duckdb path the other experiment tests use)**

Look at `tests/` for how existing experiment tests build a duckdb fixture connection (search: `.venv/bin/grep -rn "duckdb" tests | head`). Reuse that helper/fixture. Then:

```python
# tests/test_build_experiment_grid.py
import json

from scripts.build_experiment_grid import build_grid


def test_build_grid_shape(fixture_con) -> None:  # reuse existing duckdb fixture
    rows = build_grid(fixture_con, pct_lo=-2, pct_hi=2, step=1)
    assert len(rows) == 5  # -2,-1,0,1,2
    effects = [r["simulated_effect"] for r in rows]
    assert effects == [-0.02, -0.01, 0.0, 0.01, 0.02]
    for r in rows:
        assert "aov_adjusted" in r and "verdict" in r and "scenario" in r
```

If there is no shared duckdb fixture, create one in `tests/conftest.py` mirroring the existing experiment tests' setup (small CSV/dataframe → `duckdb.connect(":memory:")` → register). Keep it tiny (fixtures only).

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_build_experiment_grid.py -v`
Expected: FAIL — module `scripts.build_experiment_grid` not found.

- [ ] **Step 3: Implement the script**

```python
# scripts/build_experiment_grid.py
"""Offline: sweep the injected effect across a fine grid for the What-if tab.

Reuses the exact experiment machinery (run_scenarios + results_to_json) so each
grid point has the same schema as reports/experiment_scenarios.json. NOT run in
the app or in pytest against full data — it loads full Olist and runs the full
experiment (incl. 10k bootstrap) once per grid point (minutes, not seconds).
"""

from pathlib import Path

import duckdb

from src.experiment.run_experiment import RAW_DIR
from src.experiment.scenarios import run_scenarios
from src.io.loader import load_olist
from src.report.results_io import results_to_json

GRID_JSON_PATH = Path("reports/experiment_grid.json")


def _grid(pct_lo: int, pct_hi: int, step: int) -> tuple[tuple[str, float], ...]:
    return tuple(
        (f"eff_{pct:+d}", pct / 100.0) for pct in range(pct_lo, pct_hi + 1, step)
    )


def build_grid(
    con: duckdb.DuckDBPyConnection, pct_lo: int = -10, pct_hi: int = 10, step: int = 1
) -> list[dict[str, object]]:
    return run_scenarios(con, _grid(pct_lo, pct_hi, step))


def main(raw_dir: Path = RAW_DIR, out_path: Path = GRID_JSON_PATH) -> None:
    con = duckdb.connect(":memory:")
    load_olist(con, raw_dir)
    rows = build_grid(con)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(results_to_json(rows) + "\n")
    print(f"wrote {out_path} ({len(rows)} points)")


if __name__ == "__main__":
    main()
```

Verify imports against the real modules first: `.venv/bin/grep -n "RAW_DIR\|def load_olist\|def results_to_json\|def run_scenarios" src/experiment/run_experiment.py src/io/loader.py src/report/results_io.py src/experiment/scenarios.py`. Fix import paths if they differ.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_build_experiment_grid.py -v`
Expected: PASS.

- [ ] **Step 5: Add Makefile target**

In `Makefile` add:

```makefile
experiment-grid:
	.venv/bin/python scripts/build_experiment_grid.py
```

- [ ] **Step 6: Generate the real grid (requires full Olist in data/raw/olist)**

Run: `make experiment-grid`
Expected: `wrote reports/experiment_grid.json (21 points)`. Sanity check: `.venv/bin/python -c "import json;d=json.load(open('reports/experiment_grid.json'));print(len(d), d[0]['simulated_effect'], d[-1]['simulated_effect'], d[10]['verdict'])"` → `21 -0.1 0.1 ...`.
If raw Olist is absent, note it and defer this step to a machine that has it; the rest of the plan can proceed against the fixture.

- [ ] **Step 7: Commit**

```bash
git add scripts/build_experiment_grid.py tests/test_build_experiment_grid.py Makefile reports/experiment_grid.json tests/conftest.py
git commit -m "feat(experiment): offline build_experiment_grid sweeps effect -10..10% into reports/experiment_grid.json"
```

### Task 3: Smoke-guard the new report

**Files:** Modify `scripts/dashboard_smoke.py`

- [ ] **Step 1: Read current smoke script**

Run: `.venv/bin/cat scripts/dashboard_smoke.py` — note how it loads each report and asserts schema.

- [ ] **Step 2: Add grid validation**

Add a block that calls `data.load_grid()` and asserts `len(grid) >= 1` and the first/last `simulated_effect` are present, mirroring the existing pattern for `load_scenarios`.

- [ ] **Step 3: Run smoke**

Run: `.venv/bin/python scripts/dashboard_smoke.py`
Expected: green, includes the grid check.

- [ ] **Step 4: Commit**

```bash
git add scripts/dashboard_smoke.py
git commit -m "ci(dashboard): smoke-guard experiment_grid.json schema"
```

---

## Phase 2 — Pure helpers: glossary + value colors

### Task 4: Glossary module (TDD)

**Files:** Create `dashboard/glossary.py`, `tests/dashboard/test_glossary.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/dashboard/test_glossary.py
import pytest

from dashboard import glossary


def test_known_terms_have_nonempty_defs() -> None:
    for term in ["AOV", "CI", "MDE", "raw lift", "adjusted lift", "theta",
                 "conversion", "D7", "power", "alpha", "pre-trends", "guardrail"]:
        d = glossary.define(term)
        assert isinstance(d, str) and len(d) > 10


def test_unknown_term_raises() -> None:
    with pytest.raises(KeyError):
        glossary.define("not-a-real-term")
```

- [ ] **Step 2: Run to verify fail**

Run: `.venv/bin/pytest tests/dashboard/test_glossary.py -v` → FAIL (no module).

- [ ] **Step 3: Implement glossary**

```python
# dashboard/glossary.py
"""Single source of plain-language definitions for metrics/terms.

Copy the exact wording from docs/mockups/dashboard-v3/index.html tooltips so the
dashboard and the approved mockup stay in sync.
"""

_TERMS: dict[str, str] = {
    "AOV": "Average order value — mean BRL spent per order; the primary metric the cap change targets.",
    "CI": "Confidence interval — the plausible range for the true effect at 95% confidence.",
    "MDE": "Minimum Detectable Effect — the smallest true effect this design could reliably catch at the chosen alpha and 80% power.",
    "raw lift": "Treatment mean minus control mean, with no covariate correction.",
    "adjusted lift": "The treatment-control difference after ANCOVA covariate correction, which removes pre-experiment imbalance and usually tightens the interval.",
    "theta": "ANCOVA coefficient on freight_value, estimated pre-injection; used to remove covariate-driven variance.",
    "conversion": "Share of customers who place an order. A guardrail — the cap change must not hurt it.",
    "D7": "Share of customers returning to purchase within 7 days. A retention guardrail.",
    "power": "Probability of detecting a true effect of the target size (0.80 = 80% chance).",
    "alpha": "Significance level — the tolerated false-positive rate (0.05 = 5%).",
    "pre-trends": "Treated-minus-control gap in each week before an event; for a valid DiD these must sit inside the band (near zero).",
    "guardrail": "A metric that must NOT move — watched to ensure the change does no harm.",
}


def define(term: str) -> str:
    """Return the definition for a term, or raise KeyError if unknown."""
    return _TERMS[term]
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/pytest tests/dashboard/test_glossary.py -v` → PASS.

- [ ] **Step 5: Commit**

```bash
git add dashboard/glossary.py tests/dashboard/test_glossary.py
git commit -m "feat(dashboard): glossary module — single source of metric definitions"
```

### Task 5: Value-color classification (TDD)

**Files:** Create `dashboard/valuecolor.py`, `tests/dashboard/test_valuecolor.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/dashboard/test_valuecolor.py
from dashboard import valuecolor as vc


def test_power_thresholds() -> None:
    assert vc.power_class(0.95) == "good"
    assert vc.power_class(0.65) == "average"
    assert vc.power_class(0.30) == "poor"


def test_verdict_value_class() -> None:
    assert vc.verdict_class("SHIP") == "good"
    assert vc.verdict_class("NEED MORE DATA") == "average"
    assert vc.verdict_class("DO NOT SHIP") == "poor"


def test_mde_detectability() -> None:
    # detectable when |adjusted lift| >= mde
    assert vc.mde_class(adjusted_lift=8.63, mde=4.32) == "good"
    assert vc.mde_class(adjusted_lift=0.54, mde=4.11) == "average"
```

- [ ] **Step 2: Run to verify fail**

Run: `.venv/bin/pytest tests/dashboard/test_valuecolor.py -v` → FAIL.

- [ ] **Step 3: Implement valuecolor**

```python
# dashboard/valuecolor.py
"""Pure good/average/poor classification of values for color-coding.

Returns a class string ("good" | "average" | "poor" | "neutral"). The render
layer maps the class to a CSS color (theme.value_color). Thresholds are
interpretation, not new metrics — keep them here, documented and tested.
"""

_VERDICT = {"SHIP": "good", "NEED MORE DATA": "average", "DO NOT SHIP": "poor"}


def verdict_class(verdict: str) -> str:
    return _VERDICT.get(verdict, "neutral")


def power_class(power: float) -> str:
    if power >= 0.80:
        return "good"
    if power >= 0.50:
        return "average"
    return "poor"


def mde_class(adjusted_lift: float, mde: float) -> str:
    """Good when the effect is detectable (|lift| >= MDE), else average."""
    return "good" if abs(adjusted_lift) >= mde else "average"
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/pytest tests/dashboard/test_valuecolor.py -v` → PASS.

- [ ] **Step 5: Commit**

```bash
git add dashboard/valuecolor.py tests/dashboard/test_valuecolor.py
git commit -m "feat(dashboard): valuecolor — good/average/poor thresholds for value coloring"
```

---

## Phase 3 — Theme overhaul + new chart builders

### Task 6: Theme — new palette/fonts + responsive + value/tooltip CSS

**Files:** Modify `dashboard/theme.py`; Test `tests/dashboard/test_theme.py` (create or extend)

- [ ] **Step 1: Write/extend the failing test**

```python
# tests/dashboard/test_theme.py
from dashboard import theme


def test_value_color_maps_classes() -> None:
    assert theme.value_color("good") == theme.GREEN
    assert theme.value_color("average") == theme.AMBER
    assert theme.value_color("poor") == theme.RED
    assert theme.value_color("neutral") == theme.INK


def test_verdict_color_still_works() -> None:
    assert theme.verdict_color("SHIP") == theme.GREEN


def test_css_imports_new_fonts() -> None:
    assert "Space+Grotesk" in theme.CSS
    assert "Inter" in theme.CSS
```

- [ ] **Step 2: Run to verify fail**

Run: `.venv/bin/pytest tests/dashboard/test_theme.py -v` → FAIL.

- [ ] **Step 3: Update theme.py**

Replace palette/fonts and CSS, add `value_color`, keep `verdict_color`/`plotly_layout`:

```python
PAPER = "#FFFFFF"
CARD_BORDER = "#EAECEF"
INK = "#0D0F12"
SLATE = "#5C6B7A"
GREEN = "#2F7D4F"
RED = "#B3261E"
AMBER = "#B7791F"
ACCENT = "#7A1F2B"  # oxblood

FONT_BODY = "Inter, sans-serif"
FONT_DISPLAY = "Space Grotesk, sans-serif"
FONT_MONO = "IBM Plex Mono, monospace"

_VALUE_COLORS = {"good": GREEN, "average": AMBER, "poor": RED, "neutral": INK}


def value_color(cls: str) -> str:
    """Map a valuecolor class string to its CSS color."""
    return _VALUE_COLORS.get(cls, INK)
```

Replace `CSS` with the v3 stylesheet: import Space Grotesk + Inter + IBM Plex Mono; white `.stApp`; `h1,h2,h3` → Space Grotesk; body → Inter; `code`/numbers → IBM Plex Mono; oxblood `.section-label`; plus classes used by sections — `.takeaway`, `.vtag.good/.avg/.bad`, `.ci` (chart-info icon), `.term` (glossary), and responsive rules (no horizontal scroll; charts `max-width:100%`). **Copy the rules verbatim from `docs/mockups/dashboard-v3/index.html` `<style>`**, adapting selectors for Streamlit's DOM. Update `plotly_layout` font default to `FONT_BODY` (now Inter) and tighter margins.

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/pytest tests/dashboard/test_theme.py -v` → PASS. Also run existing chart tests that import theme: `.venv/bin/pytest tests/dashboard/ -q`.

- [ ] **Step 5: Commit**

```bash
git add dashboard/theme.py tests/dashboard/test_theme.py
git commit -m "feat(dashboard): v3 theme — white/Space Grotesk/Inter/oxblood + value_color + responsive CSS"
```

### Task 7: New chart builders (TDD, one builder per sub-step)

**Files:** Modify `dashboard/charts.py`; Create `tests/dashboard/test_charts_v3.py`

Charts are pure `go.Figure` builders. Tests assert structure (trace count, key values, colors), NOT pixels. Build each with a small inline `ScenarioResult`/values. Reuse existing `forest`, `bucket_bar`, `coef_plot` where they already fit.

- [ ] **Step 1: Write failing tests for all new builders**

```python
# tests/dashboard/test_charts_v3.py
import plotly.graph_objects as go

from dashboard import charts, theme


def test_dumbbell_has_two_endpoint_markers() -> None:
    fig = charts.dumbbell(label="D7 %", control=0.87, treatment=0.84, fmt="{:.2%}")
    assert isinstance(fig, go.Figure)
    # one connector line + two marker traces
    assert len(fig.data) == 3


def test_range_plot_orders_two_intervals() -> None:
    fig = charts.range_plot([
        ("unadjusted", (-8.69, -3.24), theme.SLATE),
        ("adjusted", (-9.93, -5.19), theme.ACCENT),
    ])
    assert len(fig.data) == 2


def test_split_bar_segments_sum_visible() -> None:
    fig = charts.split_bar([("control", 49694, theme.SLATE), ("treatment", 49398, theme.GREEN)])
    assert len(fig.data) == 2


def test_diverging_marker_inside_band() -> None:
    fig = charts.diverging_marker(value=0.52, band=2.0, unit="BRL")
    assert isinstance(fig, go.Figure)


def test_lift_forest_colors_by_argument() -> None:
    fig = charts.lift_forest(label="conv. lift", est=0.18, ci=(-0.03, 0.39), color=theme.SLATE)
    assert fig.data[0].error_x is not None


def test_mde_vs_n_marks_current() -> None:
    fig = charts.mde_vs_n(sd=180.0, alpha=0.05, power=0.80, n_current=49000)
    assert len(fig.data) >= 2  # curve + current marker


def test_power_vs_effect_has_target_line() -> None:
    fig = charts.power_vs_effect(sd=180.0, alpha=0.05, n=49000)
    assert len(fig.data) >= 2  # curve + 0.8 reference
```

- [ ] **Step 2: Run to verify fail**

Run: `.venv/bin/pytest tests/dashboard/test_charts_v3.py -v` → FAIL (builders missing).

- [ ] **Step 3: Implement the builders in `dashboard/charts.py`**

Add the following (import `math` and reuse `theme`). Port the visual intent from the mockup's JS builders (`dumbbell`, `rangeplot`, `splitbar`, `diverging`, `mde`/`powAt` formulas). For `mde_vs_n`/`power_vs_effect`, reuse the project's analytical functions: `from src.experiment.power import mde_mean` and a two-sample normal power formula (the mockup's `powAt`). Confirm `mde_mean` signature first.

```python
import math
from src.experiment.power import mde_mean


def dumbbell(label: str, control: float, treatment: float, fmt: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[control, treatment], y=[label, label], mode="lines",
                             line={"color": "#CDD2D8", "width": 3}, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[control], y=[label], mode="markers", marker={"size": 14, "color": theme.SLATE},
                             hovertemplate=f"control {fmt}<extra></extra>".format(control)))
    fig.add_trace(go.Scatter(x=[treatment], y=[label], mode="markers", marker={"size": 14, "color": theme.GREEN},
                             hovertemplate=f"treatment {fmt}<extra></extra>".format(treatment)))
    fig.update_layout(**theme.plotly_layout(height=130, showlegend=False))
    return fig


def range_plot(rows: list[tuple[str, tuple[float, float], str]]) -> go.Figure:
    fig = go.Figure()
    for label, ci, color in rows:
        fig.add_trace(go.Scatter(x=list(ci), y=[label, label], mode="lines",
                                 line={"color": color, "width": 6},
                                 hovertemplate=f"{label}: [{ci[0]:.2f}, {ci[1]:.2f}] width {ci[1]-ci[0]:.2f}<extra></extra>"))
    fig.update_layout(**theme.plotly_layout(height=130, xaxis_title="lift (BRL)"))
    return fig


def split_bar(parts: list[tuple[str, float, str]]) -> go.Figure:
    total = sum(v for _, v, _ in parts)
    fig = go.Figure()
    for name, val, color in parts:
        fig.add_trace(go.Bar(x=[val], y=[""], name=name, orientation="h", marker_color=color,
                             text=[f"{name} {val:,.0f} ({100*val/total:.1f}%)"], textposition="inside",
                             insidetextanchor="middle", textfont={"color": "white", "family": theme.FONT_MONO}))
    fig.update_layout(barmode="stack", **theme.plotly_layout(height=86, showlegend=False))
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
    return fig


def diverging_marker(value: float, band: float, unit: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[-band, band], y=["", ""], mode="lines",
                             line={"color": "#E0C9CC", "width": 14}, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[value], y=[""], mode="markers+text",
                             marker={"size": 16, "color": theme.ACCENT, "symbol": "diamond"},
                             text=[f"{value:.3f} {unit}"], textposition="top center",
                             hovertemplate=f"gap {value:.3f}<extra></extra>"))
    fig.update_layout(**theme.plotly_layout(height=96, showlegend=False))
    fig.update_yaxes(visible=False)
    return fig


def lift_forest(label: str, est: float, ci: tuple[float, float], color: str) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=[est], y=[label], mode="markers", marker={"size": 11, "color": color},
        error_x={"type": "data", "symmetric": False, "array": [ci[1]-est],
                 "arrayminus": [est-ci[0]], "color": color, "thickness": 2, "width": 7},
        hovertemplate=f"{label}: %{{x:.2f}}<br>CI [{ci[0]:.2f}, {ci[1]:.2f}]<extra></extra>"))
    fig.update_layout(**theme.plotly_layout(height=150, xaxis_title="lift", xaxis={"zeroline": True}))
    return fig


def _power_at(effect: float, sd: float, n: int, alpha: float) -> float:
    from statistics import NormalDist
    z = NormalDist().inv_cdf(1 - alpha / 2)
    se = sd * math.sqrt(2 / n)
    nd = NormalDist()
    return 1 - nd.cdf(z - abs(effect) / se) + nd.cdf(-z - abs(effect) / se)


def mde_vs_n(sd: float, alpha: float, power: float, n_current: int) -> go.Figure:
    ns = list(range(4000, 80001, 4000))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ns, y=[mde_mean(sd, n, alpha, power) for n in ns],
                             mode="lines", line={"color": theme.SLATE, "width": 2}))
    fig.add_trace(go.Scatter(x=[n_current], y=[mde_mean(sd, n_current, alpha, power)],
                             mode="markers", marker={"size": 11, "color": theme.ACCENT}))
    fig.update_layout(**theme.plotly_layout(height=220, xaxis_title="n per arm", yaxis_title="MDE (BRL)"))
    return fig


def power_vs_effect(sd: float, alpha: float, n: int) -> go.Figure:
    effs = [e / 2 for e in range(0, 31)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=effs, y=[_power_at(e, sd, n, alpha) for e in effs],
                             mode="lines", line={"color": theme.ACCENT, "width": 2}))
    fig.add_trace(go.Scatter(x=[0, 15], y=[0.8, 0.8], mode="lines",
                             line={"color": "#C9CCD1", "width": 1, "dash": "dot"}, hoverinfo="skip"))
    fig.update_layout(**theme.plotly_layout(height=220, xaxis_title="true effect (BRL)", yaxis_title="power"))
    return fig
```

Verify `mde_mean(sd, n, alpha, power)` arg order against `src/experiment/power.py` before running (the file showed `mde_mean(sd, n, alpha=ALPHA, power=POWER)`).

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/pytest tests/dashboard/test_charts_v3.py -v` → PASS (7 tests). Then `.venv/bin/mypy dashboard --strict`.

- [ ] **Step 5: Commit**

```bash
git add dashboard/charts.py tests/dashboard/test_charts_v3.py
git commit -m "feat(dashboard): diversified chart builders — dumbbell, range_plot, split_bar, diverging, lift_forest, mde_vs_n, power_vs_effect"
```

### Task 8: Verdict-color the primary AOV forest

**Files:** Modify `dashboard/charts.py` (existing `forest`); extend `tests/dashboard/test_charts_v3.py`

- [ ] **Step 1: Add failing test**

```python
def test_forest_accepts_adjusted_color() -> None:
    # forest must let the adjusted row take a verdict color
    fig = charts.forest(...)  # build with adj_color=theme.GREEN per the real signature
    colors = [getattr(t.marker, "color", None) for t in fig.data if t.mode == "markers"]
    assert theme.GREEN in colors
```

Open `dashboard/charts.py` `forest`/`_ci_row` to learn the real signature, then write the assertion to match.

- [ ] **Step 2: Run → fail.** `.venv/bin/pytest tests/dashboard/test_charts_v3.py::test_forest_accepts_adjusted_color -v`

- [ ] **Step 3: Implement** — thread an optional `adj_color: str = theme.INK` (default keeps current look) into `forest`, applied to the adjusted row marker. Callers pass `theme.verdict_color(verdict)`.

- [ ] **Step 4: Run → pass.** Re-run the test + `.venv/bin/pytest tests/dashboard/ -q`.

- [ ] **Step 5: Commit**

```bash
git add dashboard/charts.py tests/dashboard/test_charts_v3.py
git commit -m "feat(dashboard): forest adjusted row can take verdict color"
```

---

## Phase 4 — Sections (render-only; coverage-omitted)

> These are glue. No unit tests; verify via `make dashboard-smoke` + manual screenshot at the end of the phase. Each section is a `render(...)` function taking already-loaded dataclasses. Copy exact copy/markup/tooltip text from `docs/mockups/dashboard-v3/index.html`. Use `st.markdown(..., unsafe_allow_html=True)` for tiles/chips/ⓘ/glossary spans (CSS classes defined in Task 6). Use `st.plotly_chart(fig, width="stretch")`.

### Task 9: Header section (chips + rationale tooltips)

**Files:** Create `dashboard/sections/header.py`

- [ ] **Step 1: Implement `render()`** — emits eyebrow, `<h1>` title, subtitle paragraph, and the 5 context chips, each chip an inline `.pill` with a hover `data-def` carrying the ADR-sourced rationale (copy verbatim from the mockup header). No data args needed (static), or pass `MotivationStats` for the cohort count.

- [ ] **Step 2: Smoke**

Run: `.venv/bin/python scripts/dashboard_smoke.py` → green.

- [ ] **Step 3: Commit** — `git add dashboard/sections/header.py && git commit -m "feat(dashboard): persistent project header with chip rationale tooltips"`

### Task 10: Reusable tile + ⓘ + glossary helpers

**Files:** Create `dashboard/sections/_ui.py`

- [ ] **Step 1: Implement small HTML helpers** (pure string builders, importable, can be unit-tested if desired):

```python
# dashboard/sections/_ui.py
from dashboard import glossary


def term(label: str, key: str) -> str:
    """Glossary-hover span."""
    return f'<span class="term" data-def="{glossary.define(key)}">{label}</span>'


def info(text: str) -> str:
    """Chart-info ⓘ icon with a how-to-read cloud."""
    return f'<span class="ci" data-def="{text}">i</span>'


def takeaway(kicker: str, question: str, verdict_label: str, verdict_cls: str, body_html: str) -> str:
    return (f'<div class="takeaway"><div class="lab">{kicker}</div>'
            f'<div class="q">{question}</div>'
            f'<div class="verdline"><span class="chip {verdict_cls}">{verdict_label}</span></div>'
            f'<p>{body_html}</p></div>')


def value(num: str, cls: str, tag: str | None = None) -> str:
    tagspan = f'<span class="vtag {cls}">{tag}</span>' if tag else ""
    return f'<span class="v-{cls}">{num}</span>{tagspan}'
```

(Optionally add `tests/dashboard/test_ui_helpers.py` asserting `term`/`info` embed the right text — these are pure.)

- [ ] **Step 2: Commit** — `git add dashboard/sections/_ui.py && git commit -m "feat(dashboard): _ui helpers — tiles, ⓘ tooltips, glossary spans, colored values"`

### Task 11: Overview tab

**Files:** Create `dashboard/sections/overview.py` (may absorb `hero.py`+`motivation.py` content)

- [ ] **Step 1: Implement `render(experiment, scenarios, motivation)`** — bottom-line tile (static SHIP copy from mockup) · verdict hero (color via `theme.verdict_color`) · 3 motivation KPIs as colored values (`valuecolor`→`theme.value_color`, "strong"/"ample" tags) · `charts.bucket_bar` with an ⓘ · headline `charts.forest` with adjusted row colored by the large-scenario verdict. Render charts with `width="stretch"`.

- [ ] **Step 2: Smoke** → green. **Step 3: Commit** — `git commit -am "feat(dashboard): Overview tab — tile, colored KPIs, headline forest"`

### Task 12: Experiment results tab

**Files:** Modify/replace `dashboard/sections/results.py`

- [ ] **Step 1: Implement `render(scenarios)`** using the `large` scenario as primary: tile ("YES, and the estimate is solid") · AOV `forest` (adjusted=verdict color) + ⓘ · `range_plot` variance reduction (unadjusted vs adjusted CI) + ⓘ · conversion `lift_forest` (slate) + ⓘ · D7 `dumbbell` + ⓘ · `split_bar` sample sizes + ⓘ · `diverging_marker` baseline balance (band ±2.0) + ⓘ. Lay out in `st.columns(2)` (collapses on narrow). Pull the conversion lift CI and d7 control/treatment from the `ExperimentResult` dataclass fields (check `data.py` field names: `GuardrailEffect`, `AdjustedEffect`, etc.).

- [ ] **Step 2: Smoke** → green. **Step 3: Commit** — `git commit -am "feat(dashboard): Experiment results tab — 3 metrics, variance reduction, balance"`

### Task 13: Scenario explorer + What-if tab

**Files:** Modify `dashboard/sections/scenarios.py`; use `whatif.py`

- [ ] **Step 1: Implement scenario explorer** — `st.radio` over the 3 committed scenarios → live verdict chip · colored raw/adjusted/MDE values (`valuecolor.verdict_class`/`mde_class`) · live bottom-line tile (3 pre-written variants from the mockup, pick by scenario) · AOV `forest` (verdict color) + conversion `lift_forest` + D7 `dumbbell`, each ⓘ, in `st.columns(3)`.

- [ ] **Step 2: Implement `whatif.render(grid)`** — `st.select_slider` over the grid points' `simulated_effect` (sorted) → snap to that point → SIMULATED banner · verdict chip · adjusted-lift colored value · `forest`/`lift_forest` colored by that point's verdict + ⓘ. Verdict & numbers READ from the grid point (never recomputed).

- [ ] **Step 3: Smoke** → green. **Step 4: Commit** — `git commit -am "feat(dashboard): Scenario explorer + What-if grid slider"`

### Task 14: Power & design tab

**Files:** Create `dashboard/sections/calculator.py`

- [ ] **Step 1: Implement `render(experiment)`** — CALCULATOR banner · tile ("Yes — for effects above ~R$X") · `st.slider`s for n / α / SD / power (SD default seeded from a committed report's observed std, NOT hard-coded — read from `experiment` dataclass) · outputs MDE / CI half-width / power@observed as colored values (`valuecolor.power_class`) · `charts.mde_vs_n` + `charts.power_vs_effect`, each ⓘ, in `st.columns(2)`. All math via `charts._power_at` / `src.experiment.power.mde_mean` — analytical, no data load.

- [ ] **Step 2: Smoke** → green. **Step 3: Commit** — `git commit -am "feat(dashboard): Power & design tab — analytical calculator + curves"`

### Task 15: Natural experiment (DiD) tab

**Files:** Modify `dashboard/sections/did.py`

- [ ] **Step 1: Implement `render(did)`** — tile ("No — we reject this test honestly", red) · 4-condition gate checklist (PASS/FAIL with detail from `DidFeasibility` fields) · `coef_plot` pre-trends + band + ⓘ (out-of-band leads already handled; confirm red coloring) · `dumbbell` sample adequacy (treated vs control orders from `AdequateN`) + ⓘ · `split_bar` state geography (treated/control/excluded counts) + ⓘ.

- [ ] **Step 2: Smoke** → green. **Step 3: Commit** — `git commit -am "feat(dashboard): Natural experiment tab — gate, pre-trends, adequacy, geography"`

---

## Phase 5 — App shell + responsive

### Task 16: 5-tab app shell + header + grid cache

**Files:** Modify `dashboard/app.py`

- [ ] **Step 1: Rewrite the shell** keeping the `_render` isolation wrapper and `st.cache_data` loaders. Add `_grid = st.cache_data(data.load_grid)`. Render `header.render(...)` once above the tabs. Replace the 2 tabs with 5: `st.tabs(["Overview", "Experiment results", "Scenario explorer", "Power & design", "Natural experiment"])`. Wire each tab to its section via `_render("<name>", lambda: ...)`. Keep `theme.CSS` injection and `layout="wide"`.

```python
overview_t, results_t, scenarios_t, power_t, did_t = st.tabs(
    ["Overview", "Experiment results", "Scenario explorer", "Power & design", "Natural experiment"]
)
header.render(_motivation())
with overview_t:
    _render("overview", lambda: overview.render(_experiment(), _scenarios(), _motivation()))
with results_t:
    _render("results", lambda: results.render(_scenarios()))
with scenarios_t:
    _render("scenarios", lambda: scenarios.render(_scenarios()))
    _render("whatif", lambda: whatif.render(_grid()))
with power_t:
    _render("calculator", lambda: calculator.render(_experiment()))
with did_t:
    _render("did", lambda: did.render(_did()))
```

- [ ] **Step 2: Update imports** for the new sections; remove now-unused ones (or keep `notes`/`guardrail` if still referenced).

- [ ] **Step 3: Smoke + launch check**

Run: `.venv/bin/python scripts/dashboard_smoke.py` → green.
Run: `make dashboard` (Ctrl-C after it serves) — confirm no traceback in console.

- [ ] **Step 4: Commit** — `git commit -am "feat(dashboard): 5-tab shell + persistent header + grid cache"`

### Task 17: Responsive verification

**Files:** none (verify) — adjust `theme.CSS` if needed.

- [ ] **Step 1: Launch + screenshot at 3 widths** (use the same playwright-via-Chrome approach used during design, or resize the browser manually): phone ~390px, half ~720px, full ~1280px. Confirm NO horizontal scroll (`document.documentElement.scrollWidth === clientWidth`) and charts fill width. If overflow appears, ensure Plotly charts use `width="stretch"` and add the mockup's `min-width:0`/`max-width:100%` rules to `theme.CSS` for Streamlit's column/plot containers.

- [ ] **Step 2: Commit any CSS fix** — `git commit -am "fix(dashboard): responsive — no horizontal scroll at phone/half/full"`

---

## Phase 6 — Docs + final gate

### Task 18: README + STATUS

**Files:** Modify `README.md`, `docs/STATUS.md`

- [ ] **Step 1: README** — update the dashboard section to describe v3 (5 tabs, what-if, calculator, self-explaining hovers). Add `make experiment-grid` to the commands. Keep the screenshot block (re-capture in Task 19).
- [ ] **Step 2: STATUS** — overwrite to reflect v3 implemented on `feat/plan5-dashboard`, gates, and remaining manual steps (screenshots/deploy/PR).
- [ ] **Step 3: Commit** — `git commit -am "docs: dashboard v3 in README + STATUS"`

### Task 19: Full gate + fresh screenshots

- [ ] **Step 1: Full gate**

Run: `.venv/bin/pytest -q --cov=dashboard --cov-report=term-missing && .venv/bin/mypy dashboard src --strict && .venv/bin/python scripts/dashboard_smoke.py`
Expected: all tests pass; coverage on the pure layer ≥90%; mypy clean; smoke green.

- [ ] **Step 2: Capture screenshots** of the 5 tabs → `docs/img/` (overwrite `dashboard-story.png`/`dashboard-scenarios.png` or add per-tab images; update README accordingly).

- [ ] **Step 3: Commit** — `git add docs/img README.md && git commit -m "docs(dashboard): v3 screenshots"`

- [ ] **Step 4: Hand back** — report gate output verbatim; list remaining manual steps (deploy to Streamlit Community Cloud, open PR `feat/plan5-dashboard` → dev → main).

---

## Self-Review (author checklist — completed)

**Spec coverage:** header+chips (T9), 5 tabs (T11–16), bottom-line tiles (T10–15), chart ⓘ (T10–15), glossary (T4,T10), value coloring (T5,T6,T11–14), verdict coloring (T8,T11,T13), diversified charts (T7), What-if grid (T1–3,T13), power calculator (T14), responsive (T6,T17), theme/de-AI (T6), honesty banners (T13,T14), tests fixtures-only (T1–8), smoke guard (T3), docs (T18). No spec section left unmapped.

**Placeholders:** none — every code step shows code; render-only sections point to the committed mockup for exact verbatim copy (intentional, since the mockup is the locked source of truth) and give the structural code + smoke/manual verification.

**Type consistency:** `load_grid`→`list[ScenarioResult]` (matches `load_scenarios`); `valuecolor.*`→class strings consumed by `theme.value_color`; `verdict_class`/`verdict_color` distinct and consistent; chart builder names match between tasks and tests; `mde_mean(sd,n,alpha,power)` arg order flagged for verification before use.

**Open items for the implementer:** (1) confirm `mde_mean` signature + `results_to_json`/`load_olist`/`RAW_DIR` import paths before running (Tasks 2,7); (2) reuse the existing duckdb test fixture or create one in conftest (Task 2); (3) real-grid generation (Task 2 Step 6) needs full Olist — defer if absent; (4) check `ExperimentResult`/`GuardrailEffect`/`AdequateN` field names in `data.py` when wiring sections (Tasks 12,14,15).
