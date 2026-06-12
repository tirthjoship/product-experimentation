# Plan 4 — Gated DiD Natural Experiment — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the gated DiD infrastructure (event catalog, blinded panel, TWFE estimator,
pre-registered gate, report writers) and run the outcome-blind feasibility stage — stopping
before Phase C lock for user review.

**Architecture:** `src/did/` mirrors the house pattern: versioned SQL in `sql/did/` + thin
DuckDB adapters; frozen-dataclass event catalog written from public record only; post-period
rows are code-blinded until a committed GO verdict exists; statsmodels TWFE with state-clustered
SEs; md/json writers via `src/report/results_io.py`. Spec:
`docs/superpowers/specs/2026-06-11-plan4-did-natural-experiment-design.md`.

**Tech Stack:** Python 3.12, DuckDB, pandas, statsmodels (new dep), hypothesis (new dev dep),
pytest fixtures only, mypy strict.

**Conventions for every task:** run tools as `.venv/bin/pytest`, `.venv/bin/mypy`. Commit with
`SKIP=gitleaks git commit` (disk full; CI runs gitleaks server-side). Never load full Olist in
tests. Seed 42 anywhere stochastic. One deliberate deviation from spec §7: the verdict JSON has
**no `computed_at` timestamp** — committed artifacts must be byte-deterministic (Phase F
lesson); git history is the timestamp.

---

### Task 0: Branch + dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Create branch off dev**

```bash
git checkout dev && git pull origin dev && git checkout -b feat/plan4-did-natural-experiment
```

- [ ] **Step 2: Add statsmodels (runtime) and hypothesis (dev) to `pyproject.toml`**

In `[project] dependencies` add `"statsmodels>=0.14.0",` after the scipy line. In
`[project.optional-dependencies]` dev list add `"hypothesis>=6.100",`. In the mypy overrides
section, extend the ignore-missing-imports module list:

```toml
module = ["pandas.*", "duckdb.*", "scipy.*", "matplotlib.*", "numpy.*", "statsmodels.*"]
```

- [ ] **Step 3: Install and verify**

Run: `.venv/bin/pip install -e ".[dev]" -q && .venv/bin/python -c "import statsmodels, hypothesis; print('ok')"`
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml && SKIP=gitleaks git commit -m "chore: add statsmodels + hypothesis for Plan 4 DiD"
```

---

### Task 1: Exceptions + event catalog module

**Files:**
- Modify: `src/exceptions.py`
- Create: `src/did/__init__.py` (empty), `src/did/catalog.py`
- Test: `tests/test_did_catalog.py`

- [ ] **Step 1: Write failing tests**

```python
"""Catalog invariants: 27 UFs, disjoint donut arms, geography-only construction."""

import pytest

from src.did.catalog import ALL_UFS, CATALOG, get_event, viable_candidates
from src.exceptions import UnknownEventError


def test_all_ufs_is_27():
    assert len(ALL_UFS) == 27


def test_catalog_has_three_dated_candidates():
    assert len(CATALOG) >= 3
    for e in CATALOG:
        assert e.boundary_date  # dated boundary (gate condition 1)
        assert e.source  # citable public record
        assert e.estimation_start < e.boundary_date < e.estimation_end_exclusive


def test_donut_arms_disjoint_and_geographic():
    for e in CATALOG:
        treated, control, excluded = (
            set(e.treated_states),
            set(e.control_states),
            set(e.excluded_states),
        )
        assert treated and control
        assert treated.isdisjoint(control)
        assert treated.isdisjoint(excluded)
        assert control.isdisjoint(excluded)
        assert (treated | control | excluded) <= ALL_UFS


def test_expected_sign_is_unit():
    for e in CATALOG:
        assert e.expected_sign in (-1, 1)
        assert e.outcome in ("delivery_days", "log_orders")


def test_viable_candidates_subset():
    viable = viable_candidates()
    assert all(e.viable_on_paper for e in viable)
    assert {e.name for e in viable} <= {e.name for e in CATALOG}


def test_get_event_unknown_raises():
    with pytest.raises(UnknownEventError):
        get_event("nonexistent")
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/pytest tests/test_did_catalog.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.did'`

- [ ] **Step 3: Add exceptions**

Append to `src/exceptions.py`:

```python
class UnknownEventError(ExperimentError):
    """Requested event name is not in the Plan 4 catalog."""


class BlindingError(ExperimentError):
    """Post-period data requested without a committed GO gate verdict."""
```

- [ ] **Step 4: Implement `src/did/catalog.py`**

Create empty `src/did/__init__.py`, then:

```python
"""Phase A event catalog — written from public record ONLY, before any data access.

Each entry pre-registers hypothesis, primary outcome, expected sign, and donut
assignment (treated bloc / control bloc / excluded middle) per spec §4 + §6.
Selection among viable candidates is mechanical: feasibility (Phase B) checks
pre-period cell counts only, never outcomes.
"""

from dataclasses import dataclass

from src.exceptions import UnknownEventError

# Brazilian UFs by IBGE macro-region (public record).
NORTH = ("AC", "AM", "AP", "PA", "RO", "RR", "TO")
NORTHEAST = ("AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE")
CENTER_WEST = ("DF", "GO", "MS", "MT")
SOUTHEAST = ("ES", "MG", "RJ", "SP")
SOUTH = ("PR", "RS", "SC")
ALL_UFS = frozenset(NORTH + NORTHEAST + CENTER_WEST + SOUTHEAST + SOUTH)


@dataclass(frozen=True)
class EventDefinition:
    name: str
    description: str
    source: str  # public-record citation (gate condition 1)
    boundary_date: str  # ISO date; post period starts here (inclusive)
    estimation_start: str
    estimation_end_exclusive: str
    outcome: str  # "delivery_days" | "log_orders"
    expected_sign: int  # +1 / -1
    treated_states: tuple[str, ...]
    control_states: tuple[str, ...]
    excluded_states: tuple[str, ...]
    viable_on_paper: bool
    rationale: str


CATALOG: tuple[EventDefinition, ...] = (
    EventDefinition(
        name="truckers_strike_2018",
        description=(
            "Nationwide truckers' strike (greve dos caminhoneiros), 2018-05-21 to "
            "2018-05-30: road freight halted; long-haul routes to North/Northeast "
            "depend on trucking from Southeast distribution hubs."
        ),
        source=(
            "Widely documented national event; e.g. "
            "https://en.wikipedia.org/wiki/2018_Brazil_truck_drivers%27_strike"
        ),
        boundary_date="2018-05-21",
        estimation_start="2018-01-01",
        estimation_end_exclusive="2018-09-01",
        outcome="delivery_days",
        expected_sign=1,  # deliveries slower, more so far from hubs
        treated_states=NORTH + NORTHEAST,
        control_states=SOUTHEAST + SOUTH,
        excluded_states=CENTER_WEST,
        viable_on_paper=True,
        rationale=(
            "Externally dated; exposure gradient is geographic (freight distance "
            "from SE hubs); donut drops ambiguous Center-West."
        ),
    ),
    EventDefinition(
        name="black_friday_2017",
        description="Black Friday demand spike, 2017-11-24.",
        source="Annual retail calendar date (public record).",
        boundary_date="2017-11-24",
        estimation_start="2017-08-01",
        estimation_end_exclusive="2018-01-01",
        outcome="log_orders",
        expected_sign=1,
        treated_states=NORTH + NORTHEAST,
        control_states=SOUTHEAST + SOUTH,
        excluded_states=CENTER_WEST,
        viable_on_paper=False,
        rationale=(
            "NOT viable on paper: exposure is national — no geography-only "
            "treated/control contrast exists (gate condition 2 unsatisfiable). "
            "Kept in catalog to document the rejection."
        ),
    ),
    EventDefinition(
        name="carnival_2018",
        description="Carnival week, 2018-02-13 (Shrove Tuesday).",
        source="Brazilian national calendar (public record).",
        boundary_date="2018-02-13",
        estimation_start="2017-11-01",
        estimation_end_exclusive="2018-04-01",
        outcome="log_orders",
        expected_sign=-1,
        treated_states=("RJ", "BA", "PE", "SP"),  # major public celebrations
        control_states=SOUTH + ("MG", "ES"),
        excluded_states=NORTH
        + ("AL", "CE", "MA", "PB", "PI", "RN", "SE")
        + CENTER_WEST,
        viable_on_paper=False,
        rationale=(
            "NOT viable on paper: ~1-week transient shock with ambiguous sign and "
            "too few post-boundary weeks of differential exposure for ≥3 lead/lag "
            "structure. Kept to document the rejection."
        ),
    ),
)


def viable_candidates() -> tuple[EventDefinition, ...]:
    return tuple(e for e in CATALOG if e.viable_on_paper)


def get_event(name: str) -> EventDefinition:
    for e in CATALOG:
        if e.name == name:
            return e
    raise UnknownEventError(f"event not in catalog: {name!r}")
```

- [ ] **Step 5: Run tests**

Run: `.venv/bin/pytest tests/test_did_catalog.py -q`
Expected: all PASS (carnival's excluded list deliberately omits BA/PE — they are treated —
so the disjointness test holds).

- [ ] **Step 6: mypy + commit**

Run: `.venv/bin/mypy src/ --strict` → clean.

```bash
git add src/exceptions.py src/did/ tests/test_did_catalog.py
SKIP=gitleaks git commit -m "feat: Plan 4 event catalog (frozen, public-record-only) + catalog invariant tests"
```

---

### Task 2: Phase A catalog document (pre-registration artifact)

**Files:**
- Create: `docs/superpowers/specs/2026-06-11-plan4-event-catalog.md`

- [ ] **Step 1: Write the document** — human-readable mirror of `catalog.py` (the code is
authoritative; the doc explains). Content: one section per candidate with description, source,
boundary date, hypothesis (outcome + expected sign + mechanism), donut state lists, viability
verdict + rationale; a header stating *"Written from public record only. Committed before any
Phase B query ran — git history is the timestamp"*; and the mechanical selection rule:
*"first `viable_on_paper` candidate whose pre-period feasibility passes gate condition 4(pre)
is selected; no outcome data informs selection."*

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/specs/2026-06-11-plan4-event-catalog.md
SKIP=gitleaks git commit -m "docs: Plan 4 Phase A event catalog (pre-registration artifact)"
```

---

### Task 3: Panel SQL + DiD fixtures + blinded panel builder

**Files:**
- Create: `sql/did/panel.sql`, `tests/fixtures/did_orders.csv`, `tests/fixtures/did_customers.csv`
- Create: `src/did/panel.py`
- Test: `tests/test_did_panel.py`

- [ ] **Step 1: Create fixtures** (≤20 rows; 2 treated states PA/BA, 1 control SP; weeks
around a 2018-05-21 boundary so blinding is testable).

`tests/fixtures/did_customers.csv`:

```csv
customer_id,customer_unique_id,customer_state
dc1,du1,PA
dc2,du2,PA
dc3,du3,BA
dc4,du4,SP
dc5,du5,SP
dc6,du6,GO
```

`tests/fixtures/did_orders.csv` (GO row must be excluded by donut; post rows after 2018-05-21
must vanish when blinded; one undelivered order checks NULL delivery_days handling):

```csv
order_id,customer_id,order_status,order_purchase_timestamp,order_delivered_customer_date
do1,dc1,delivered,2018-05-07 10:00:00,2018-05-17 10:00:00
do2,dc2,delivered,2018-05-08 10:00:00,2018-05-20 10:00:00
do3,dc3,delivered,2018-05-09 10:00:00,2018-05-14 10:00:00
do4,dc4,delivered,2018-05-07 11:00:00,2018-05-10 11:00:00
do5,dc5,shipped,2018-05-08 11:00:00,
do6,dc6,delivered,2018-05-09 11:00:00,2018-05-12 11:00:00
do7,dc1,delivered,2018-05-28 10:00:00,2018-06-15 10:00:00
do8,dc4,delivered,2018-05-29 10:00:00,2018-06-01 10:00:00
```

- [ ] **Step 2: Write failing tests**

```python
"""Panel builder: SQL aggregation correctness + code-enforced post-period blinding."""

from pathlib import Path

import duckdb
import pandas as pd
import pytest

from src.did.catalog import get_event
from src.did.panel import build_panel, require_go
from src.exceptions import BlindingError

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def did_con():
    con = duckdb.connect(":memory:")
    for name in ["customers", "orders"]:
        df = pd.read_csv(FIXTURES / f"did_{name}.csv")
        for col in df.columns:
            if col.endswith("timestamp"):
                df[col] = pd.to_datetime(df[col])
        # order_delivered_customer_date stays a string; the SQL TRY_CASTs it
        con.register(name, df)
    yield con
    con.close()


EVENT = get_event("truckers_strike_2018")


def test_blinded_panel_has_no_post_rows(did_con):
    panel = build_panel(did_con, EVENT)
    assert (panel["week"] < pd.Timestamp(EVENT.boundary_date)).all()
    assert not panel["post"].any()


def test_excluded_states_dropped(did_con):
    panel = build_panel(did_con, EVENT)
    assert "GO" not in set(panel["customer_state"])  # Center-West donut hole


def test_aggregates_correct(did_con):
    panel = build_panel(did_con, EVENT)
    pa = panel[panel["customer_state"] == "PA"].iloc[0]
    # do1 (10 days) + do2 (12 days), same ISO week
    assert pa["n_orders"] == 2
    assert pa["delivery_days"] == pytest.approx(11.0)
    assert bool(pa["treated"]) is True
    sp = panel[panel["customer_state"] == "SP"].iloc[0]
    # do4 delivered (3 days); do5 not delivered -> excluded from AVG, counted in n
    assert sp["n_orders"] == 2
    assert sp["delivery_days"] == pytest.approx(3.0)
    assert bool(sp["treated"]) is False


def test_log_orders_column(did_con):
    panel = build_panel(did_con, EVENT)
    import numpy as np

    assert panel["log_orders"].tolist() == pytest.approx(
        np.log1p(panel["n_orders"]).tolist()
    )


def test_unblind_without_verdict_raises(did_con, tmp_path):
    with pytest.raises(BlindingError):
        build_panel(did_con, EVENT, unblind_post=True, verdict_path=tmp_path / "missing.json")


def test_unblind_with_fail_verdict_raises(did_con, tmp_path):
    p = tmp_path / "v.json"
    p.write_text('{"event": "truckers_strike_2018", "verdict": "FAIL"}')
    with pytest.raises(BlindingError):
        build_panel(did_con, EVENT, unblind_post=True, verdict_path=p)


def test_unblind_with_go_verdict_includes_post(did_con, tmp_path):
    p = tmp_path / "v.json"
    p.write_text('{"event": "truckers_strike_2018", "verdict": "GO"}')
    panel = build_panel(did_con, EVENT, unblind_post=True, verdict_path=p)
    assert panel["post"].any()


def test_go_verdict_for_wrong_event_raises(did_con, tmp_path):
    p = tmp_path / "v.json"
    p.write_text('{"event": "black_friday_2017", "verdict": "GO"}')
    with pytest.raises(BlindingError):
        require_go(p, "truckers_strike_2018")
```

- [ ] **Step 3: Run to verify failure**

Run: `.venv/bin/pytest tests/test_did_panel.py -q`
Expected: FAIL — `No module named 'src.did.panel'`

- [ ] **Step 4: Create `sql/did/panel.sql`**

```sql
-- State × ISO-week DiD panel (spec §10). Aggregation only; assignment, donut filter,
-- and post-period blinding live in src/did/panel.py. ORDER BY pinned: the bootstrap
-- determinism incident (Phase F) taught us never to rely on engine row order.
SELECT
    c.customer_state,
    DATE_TRUNC('week', o.order_purchase_timestamp) AS week,
    COUNT(*) AS n_orders,
    AVG(
        CASE
            WHEN o.order_status = 'delivered'
            THEN date_diff(
                'day',
                o.order_purchase_timestamp,
                TRY_CAST(o.order_delivered_customer_date AS TIMESTAMP)
            )
        END
    ) AS delivery_days
FROM orders o
JOIN customers c USING (customer_id)
WHERE o.order_purchase_timestamp >= $start
  AND o.order_purchase_timestamp <  $end
GROUP BY 1, 2
ORDER BY 1, 2;
```

- [ ] **Step 5: Implement `src/did/panel.py`**

```python
"""Blinded state×week panel builder. Post-period rows exist only after a committed
GO verdict — the verdict JSON is the key (spec §5, §7)."""

import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from src._sql import load_sql
from src.did.catalog import EventDefinition
from src.exceptions import BlindingError

VERDICT_JSON = Path("reports/did_gate_verdict.json")


def require_go(verdict_path: Path, event_name: str) -> None:
    if not verdict_path.exists():
        raise BlindingError(
            f"no gate verdict at {verdict_path}; post-period data stays blinded"
        )
    verdict = json.loads(verdict_path.read_text())
    if verdict.get("event") != event_name or verdict.get("verdict") != "GO":
        raise BlindingError(
            f"gate verdict is not GO for {event_name!r}: {verdict!r}"
        )


def build_panel(
    con: duckdb.DuckDBPyConnection,
    event: EventDefinition,
    *,
    unblind_post: bool = False,
    verdict_path: Path = VERDICT_JSON,
) -> pd.DataFrame:
    if unblind_post:
        require_go(verdict_path, event.name)
        end = event.estimation_end_exclusive
    else:
        end = event.boundary_date
    df = con.execute(
        load_sql("did/panel.sql"), {"start": event.estimation_start, "end": end}
    ).fetchdf()
    keep = set(event.treated_states) | set(event.control_states)
    df = df[df["customer_state"].isin(keep)].reset_index(drop=True)
    df["treated"] = df["customer_state"].isin(set(event.treated_states))
    df["post"] = df["week"] >= pd.Timestamp(event.boundary_date)
    df["log_orders"] = np.log1p(df["n_orders"])
    return df.sort_values(["customer_state", "week"]).reset_index(drop=True)
```

- [ ] **Step 6: Run tests**

Run: `.venv/bin/pytest tests/test_did_panel.py -q`
Expected: all PASS

- [ ] **Step 7: mypy + commit**

Run: `.venv/bin/mypy src/ --strict` → clean.

```bash
git add sql/did/ src/did/panel.py tests/test_did_panel.py tests/fixtures/did_*.csv
SKIP=gitleaks git commit -m "feat: blinded DiD panel builder + panel SQL + fixtures"
```

---

### Task 4: Synthetic panel factory (test infrastructure)

**Files:**
- Create: `tests/did_factory.py`
- Test: `tests/test_did_factory.py`

- [ ] **Step 1: Write failing test**

```python
"""Sanity checks on the synthetic DiD panel factory used by estimator/gate tests."""

import pandas as pd

from tests.did_factory import make_synthetic_panel


def test_factory_shape_and_columns():
    panel = make_synthetic_panel()
    assert set(panel.columns) >= {
        "customer_state", "week", "n_orders", "delivery_days",
        "treated", "post", "log_orders",
    }
    assert panel["treated"].sum() > 0 and (~panel["treated"]).sum() > 0
    assert panel["post"].sum() > 0 and (~panel["post"]).sum() > 0


def test_factory_deterministic():
    a = make_synthetic_panel(seed=42)
    b = make_synthetic_panel(seed=42)
    pd.testing.assert_frame_equal(a, b)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/pytest tests/test_did_factory.py -q` → FAIL (no module)

- [ ] **Step 3: Implement `tests/did_factory.py`**

```python
"""Synthetic state×week panel with KNOWN injected DiD effect — the estimator must
recover it (same known-truth philosophy as the simulated RCT, ADR 0004)."""

import numpy as np
import pandas as pd

BOUNDARY = pd.Timestamp("2018-05-21")


def make_synthetic_panel(
    n_treated: int = 6,
    n_control: int = 6,
    n_weeks: int = 24,
    boundary_week: int = 16,
    effect: float = 0.0,
    pre_trend: float = 0.0,  # extra per-week slope on treated states (breaks parallelism)
    noise: float = 0.5,
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
```

- [ ] **Step 4: Run tests** → PASS. **Step 5: Commit**

```bash
git add tests/did_factory.py tests/test_did_factory.py
SKIP=gitleaks git commit -m "test: synthetic DiD panel factory with injectable effect + pre-trend break"
```

---

### Task 5: TWFE estimator

**Files:**
- Create: `src/did/estimator.py`
- Test: `tests/test_did_estimator.py`

- [ ] **Step 1: Write failing tests**

```python
"""TWFE DiD: must recover a known injected effect; CI must cover 0 under null;
estimate invariant to state-constant shifts (hypothesis property)."""

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.did.estimator import fit_twfe
from tests.did_factory import make_synthetic_panel


def test_recovers_injected_effect():
    panel = make_synthetic_panel(effect=5.0, seed=42)
    res = fit_twfe(panel, "delivery_days")
    assert res.beta == pytest.approx(5.0, abs=0.5)
    assert res.ci[0] < 5.0 < res.ci[1]
    assert res.n_clusters == 12


def test_null_effect_ci_covers_zero():
    panel = make_synthetic_panel(effect=0.0, seed=42)
    res = fit_twfe(panel, "delivery_days")
    assert res.ci[0] < 0.0 < res.ci[1]


@settings(max_examples=20, deadline=None)
@given(shift=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False))
def test_beta_invariant_to_global_shift(shift):
    panel = make_synthetic_panel(effect=3.0, seed=42)
    res_base = fit_twfe(panel, "delivery_days")
    shifted = panel.copy()
    shifted["delivery_days"] = shifted["delivery_days"] + shift
    res_shift = fit_twfe(shifted, "delivery_days")
    assert res_shift.beta == pytest.approx(res_base.beta, abs=1e-8)
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/pytest tests/test_did_estimator.py -q` → FAIL (no module)

- [ ] **Step 3: Implement `src/did/estimator.py`**

```python
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
```

- [ ] **Step 4: Run tests** → PASS (statsmodels may emit small-cluster warnings; fine).

- [ ] **Step 5: mypy + commit**

```bash
git add src/did/estimator.py tests/test_did_estimator.py
SKIP=gitleaks git commit -m "feat: TWFE DiD estimator with state-clustered SEs; recovers injected effect"
```

---

### Task 6: Pre-trends check (event-study leads, Wald + magnitude band)

**Files:**
- Modify: `src/did/estimator.py`
- Test: `tests/test_did_pretrends.py`

- [ ] **Step 1: Write failing tests**

```python
"""Two-sided pre-trends gate input: Wald on leads catches divergence; the magnitude
band exists so vacuous non-significance can't pass silently (spec §6 condition 3)."""

import pytest

from src.did.estimator import pretrends_check
from tests.did_factory import make_synthetic_panel


def test_parallel_panel_passes_wald():
    panel = make_synthetic_panel(effect=5.0, pre_trend=0.0, seed=42)
    pt = pretrends_check(panel, "delivery_days", "2018-05-21")
    assert pt.wald_p > 0.10
    assert pt.n_leads >= 3
    assert pt.max_lead_abs <= pt.band


def test_diverging_pretrend_fails_wald():
    panel = make_synthetic_panel(effect=5.0, pre_trend=1.0, seed=42)
    pt = pretrends_check(panel, "delivery_days", "2018-05-21")
    assert pt.wald_p <= 0.10 or pt.max_lead_abs > pt.band


def test_pretrends_uses_pre_period_only():
    # identical pre-periods, wildly different post-periods -> identical results
    a = make_synthetic_panel(effect=0.0, seed=42)
    b = make_synthetic_panel(effect=50.0, seed=42)
    pt_a = pretrends_check(a, "delivery_days", "2018-05-21")
    pt_b = pretrends_check(b, "delivery_days", "2018-05-21")
    assert pt_a.wald_p == pytest.approx(pt_b.wald_p)
    assert pt_a.leads == pt_b.leads
```

- [ ] **Step 2: Run to verify failure** → FAIL (`pretrends_check` not defined)

- [ ] **Step 3: Append to `src/did/estimator.py`**

```python
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
    wald = res.wald_test(
        ", ".join(f"{c} = 0" for c in cols), use_f=True, scalar=True
    )
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
```

- [ ] **Step 4: Run tests** → PASS

- [ ] **Step 5: mypy + commit**

```bash
git add src/did/estimator.py tests/test_did_pretrends.py
SKIP=gitleaks git commit -m "feat: event-study pre-trends check — joint Wald + magnitude band + MDL"
```

---

### Task 7: Gate evaluation + verdict writer

**Files:**
- Create: `src/did/gate.py`
- Test: `tests/test_did_gate.py`

- [ ] **Step 1: Write failing tests**

```python
"""Gate: 4 pre-registered conditions; verdict JSON unlocks (or keeps locked) post-period."""

import json

import pandas as pd

from src.did.catalog import get_event
from src.did.gate import evaluate_gate, feasibility_counts, write_verdict
from tests.did_factory import make_synthetic_panel

EVENT = get_event("truckers_strike_2018")


def _pre(panel: pd.DataFrame) -> pd.DataFrame:
    return panel[~panel["post"]].reset_index(drop=True)


def test_feasibility_counts_structure():
    pre = _pre(make_synthetic_panel(seed=42))
    fc = feasibility_counts(pre)
    assert fc["treated_orders"] > 0 and fc["control_orders"] > 0
    assert 0.0 <= fc["week_cell_share_ge_20"] <= 1.0
    assert fc["treated_states"] == 6 and fc["control_states"] == 6


def test_gate_go_on_clean_panel():
    pre = _pre(make_synthetic_panel(effect=0.0, pre_trend=0.0, seed=42))
    verdict = evaluate_gate(EVENT, pre)
    assert verdict["verdict"] == "GO"
    assert all(
        c["passed"] for c in verdict["conditions"].values()
    ), verdict["conditions"]


def test_gate_fail_on_diverging_pretrend():
    pre = _pre(make_synthetic_panel(effect=0.0, pre_trend=1.0, seed=42))
    verdict = evaluate_gate(EVENT, pre)
    assert verdict["verdict"] == "FAIL"
    assert not verdict["conditions"]["parallel_pretrends"]["passed"]


def test_gate_fail_on_thin_cells():
    pre = _pre(make_synthetic_panel(seed=42))
    thin = pre.copy()
    thin["n_orders"] = 1  # every cell below thresholds
    verdict = evaluate_gate(EVENT, thin)
    assert verdict["verdict"] == "FAIL"
    assert not verdict["conditions"]["adequate_n"]["passed"]


def test_write_verdict_roundtrip(tmp_path):
    pre = _pre(make_synthetic_panel(seed=42))
    verdict = evaluate_gate(EVENT, pre)
    path = tmp_path / "verdict.json"
    write_verdict(verdict, path)
    assert json.loads(path.read_text())["event"] == "truckers_strike_2018"
    assert "computed_at" not in verdict  # determinism: git is the timestamp
```

- [ ] **Step 2: Run to verify failure** → FAIL (no module)

- [ ] **Step 3: Implement `src/did/gate.py`**

```python
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
```

- [ ] **Step 4: Run tests** → PASS. If `test_gate_go_on_clean_panel` fails on `adequate_n`,
the factory's `n_orders` range (30–80 × 12 states × 16 pre-weeks ≈ 10k/arm) exceeds 1,000 —
inspect the failing condition dict before touching thresholds.

- [ ] **Step 5: mypy + commit**

```bash
git add src/did/gate.py tests/test_did_gate.py
SKIP=gitleaks git commit -m "feat: pre-registered DiD gate — 4 conditions, deterministic verdict JSON"
```

---

### Task 8: Report writers (feasibility, GO report, FAIL rejection)

**Files:**
- Create: `src/did/report.py`
- Test: `tests/test_did_report.py`

- [ ] **Step 1: Write failing tests**

```python
"""Report writers: every number in md comes from the dict that also writes the JSON
(house rule 1). Simulation banner not needed — this analysis is observational."""

from src.did.catalog import get_event
from src.did.estimator import DidResult
from src.did.gate import evaluate_gate
from src.did.report import (
    generate_did_report_md,
    generate_feasibility_md,
    generate_rejection_md,
)
from tests.did_factory import make_synthetic_panel

EVENT = get_event("truckers_strike_2018")


def _verdict(pre_trend: float = 0.0):
    panel = make_synthetic_panel(pre_trend=pre_trend, seed=42)
    return evaluate_gate(EVENT, panel[~panel["post"]].reset_index(drop=True))


def test_feasibility_md_contains_counts():
    v = _verdict()
    md = generate_feasibility_md([v])
    n = v["conditions"]["adequate_n"]
    assert f"{n['treated_orders']:,}" in md
    assert f"{n['control_orders']:,}" in md
    assert "truckers_strike_2018" in md
    assert "outcome-blind" in md.lower()


def test_go_report_quotes_estimate_and_gate():
    v = _verdict()
    res = DidResult(
        beta=2.5, se=0.4, ci=(1.7, 3.3), p=0.001, n_obs=288, n_clusters=12,
        outcome="delivery_days",
    )
    md = generate_did_report_md(EVENT, res, v)
    assert "2.50" in md and "(1.70, 3.30)" in md
    assert "natural experiment" in md.lower()
    assert "threats to validity" in md.lower()


def test_rejection_md_names_broken_condition():
    v = _verdict(pre_trend=1.0)
    md = generate_rejection_md(EVENT, v)
    assert "REJECTED" in md
    assert "parallel_pretrends" in md
```

- [ ] **Step 2: Run to verify failure** → FAIL (no module)

- [ ] **Step 3: Implement `src/did/report.py`** — follow
`src/report/installment_motivation.py` style (list-of-lines, f-string formats that the
integrity test will mirror later):

```python
"""Markdown writers for the DiD natural experiment. Numbers always come from the same
dicts/dataclasses that produce the committed JSON (rule 1: no invented metrics)."""

from typing import Any

from src.did.catalog import EventDefinition
from src.did.estimator import DidResult


def _gate_table(verdict: dict[str, Any]) -> list[str]:
    lines = ["| Condition | Passed | Evidence |", "|---|---|---|"]
    for name, c in verdict["conditions"].items():
        evidence = {k: v for k, v in c.items() if k != "passed"}
        mark = "✅" if c["passed"] else "❌"
        lines.append(f"| {name} | {mark} | `{evidence}` |")
    return lines


def generate_feasibility_md(verdicts: list[dict[str, Any]]) -> str:
    lines = [
        "# DiD Feasibility — Phase B (outcome-blind)",
        "",
        "> Pre-period cell counts ONLY. No outcome × event-window data was inspected;",
        "> post-period rows are code-blinded until a committed GO verdict exists.",
        "",
    ]
    for v in verdicts:
        n = v["conditions"]["adequate_n"]
        lines += [
            f"## {v['event']}",
            "",
            f"- treated orders (pre): **{n['treated_orders']:,}**",
            f"- control orders (pre): **{n['control_orders']:,}**",
            f"- week-cells ≥ 20 orders: **{n['week_cell_share_ge_20']:.1%}**",
            f"- states per arm: {n['treated_states']} / {n['control_states']}",
            "",
        ]
    return "\n".join(lines)


def generate_did_report_md(
    event: EventDefinition, result: DidResult, verdict: dict[str, Any]
) -> str:
    lines = [
        f"# Experiment 002 — Natural Experiment (DiD): {event.name}",
        "",
        "> **Observational natural experiment** on real Olist data (no synthetic effect).",
        "> Identification rests on the pre-registered gate below, not on randomization.",
        "",
        event.description,
        "",
        f"**DiD estimate ({result.outcome}):** **{result.beta:.2f}** "
        f"(95% CI ({result.ci[0]:.2f}, {result.ci[1]:.2f}), p={result.p:.4f}, "
        f"SE {result.se:.2f}, clusters={result.n_clusters}, n={result.n_obs})",
        "",
        "## Pre-registered gate (decided before unblinding)",
        "",
        *_gate_table(verdict),
        "",
        "## Threats to validity",
        "",
        "- Spillovers: control states also faced the national shock → estimate is a",
        "  *differential*-exposure effect, biased toward zero if controls were hit too.",
        "- Composition: order mix may shift at the boundary (purchase-week assignment).",
        "- SUTVA: marketplace-level seller congestion can couple arms.",
        "",
    ]
    return "\n".join(lines)


def generate_rejection_md(event: EventDefinition, verdict: dict[str, Any]) -> str:
    broken = [k for k, c in verdict["conditions"].items() if not c["passed"]]
    lines = [
        "# Natural Experiment Feasibility — REJECTED",
        "",
        f"Candidate: **{event.name}** — gate verdict **{verdict['verdict']}**.",
        "",
        f"Broken condition(s): **{', '.join(broken)}**.",
        "",
        "Per the pre-registered protocol (spec §9), no estimate is computed or",
        "reported. This rejection is the deliverable: the identification assumptions",
        "required for a causal claim do not hold, and we do not manufacture one.",
        "",
        "## Gate evidence",
        "",
        *_gate_table(verdict),
        "",
    ]
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests** → PASS

- [ ] **Step 5: mypy + commit**

```bash
git add src/did/report.py tests/test_did_report.py
SKIP=gitleaks git commit -m "feat: DiD report writers — feasibility, GO readout, rejection"
```

---

### Task 9: CLI orchestrator + Make targets

**Files:**
- Create: `src/did/run_did.py`
- Modify: `Makefile`
- Test: `tests/test_did_run.py`

- [ ] **Step 1: Write failing test** (fixture-driven end-to-end of the *stage logic*, using
the synthetic factory via monkeypatched panel builder — never full Olist):

```python
"""Stage orchestration: feasibility writes artifacts; estimate refuses without GO."""

import json

import pytest

from src.did import run_did
from src.exceptions import BlindingError
from tests.did_factory import make_synthetic_panel


@pytest.fixture
def fake_panels(monkeypatch):
    def _build_panel(con, event, *, unblind_post=False, verdict_path=None):
        panel = make_synthetic_panel(seed=42)
        if not unblind_post:
            return panel[~panel["post"]].reset_index(drop=True)
        from src.did.panel import require_go

        require_go(verdict_path, event.name)
        return panel

    monkeypatch.setattr(run_did, "build_panel", _build_panel)
    monkeypatch.setattr(run_did, "_connect", lambda: None)


def test_feasibility_stage_writes_md_and_json(fake_panels, tmp_path):
    run_did.stage_feasibility(out_md=tmp_path / "f.md", out_json=tmp_path / "f.json")
    assert (tmp_path / "f.md").exists()
    data = json.loads((tmp_path / "f.json").read_text())
    assert data[0]["event"] == "truckers_strike_2018"


def test_gate_stage_writes_verdict(fake_panels, tmp_path):
    path = tmp_path / "verdict.json"
    run_did.stage_gate("truckers_strike_2018", verdict_path=path)
    assert json.loads(path.read_text())["verdict"] in ("GO", "FAIL")


def test_estimate_stage_blocked_without_go(fake_panels, tmp_path):
    with pytest.raises(BlindingError):
        run_did.stage_estimate(
            "truckers_strike_2018",
            verdict_path=tmp_path / "missing.json",
            out_md=tmp_path / "r.md",
            out_json=tmp_path / "r.json",
        )
```

- [ ] **Step 2: Run to verify failure** → FAIL (no module)

- [ ] **Step 3: Implement `src/did/run_did.py`**

```python
"""CLI for the gated DiD stages. Stage order is the protocol:
feasibility (blind) -> gate (pre-period only) -> estimate (requires committed GO)."""

import argparse
from dataclasses import asdict
from pathlib import Path

import duckdb

from src.did.catalog import get_event, viable_candidates
from src.did.gate import evaluate_gate, write_verdict
from src.did.panel import VERDICT_JSON, build_panel
from src.did.report import (
    generate_did_report_md,
    generate_feasibility_md,
    generate_rejection_md,
)
from src.did.estimator import fit_twfe, pretrends_check
from src.io.loader import load_olist
from src.report.results_io import write_results_json

RAW_DIR = Path("data/raw/olist")
FEASIBILITY_MD = Path("reports/did_feasibility.md")
FEASIBILITY_JSON = Path("reports/did_feasibility.json")
REPORT_MD = Path("reports/experiment_002_did.md")
REPORT_JSON = Path("reports/experiment_002_did.json")
REJECTION_MD = Path("reports/natural_experiment_feasibility.md")


def _connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(":memory:")
    load_olist(con, RAW_DIR)
    return con


def stage_feasibility(
    out_md: Path = FEASIBILITY_MD, out_json: Path = FEASIBILITY_JSON
) -> None:
    con = _connect()
    verdicts = []
    for event in viable_candidates():
        panel_pre = build_panel(con, event)  # blinded: pre-period only
        verdicts.append(evaluate_gate(event, panel_pre))
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(generate_feasibility_md(verdicts))
    write_results_json(verdicts, out_json)
    print(f"wrote {out_md} and {out_json}")


def stage_gate(event_name: str, verdict_path: Path = VERDICT_JSON) -> None:
    con = _connect()
    event = get_event(event_name)
    panel_pre = build_panel(con, event)
    verdict = evaluate_gate(event, panel_pre)
    write_verdict(verdict, verdict_path)
    print(f"{event_name}: {verdict['verdict']} -> {verdict_path}")


def stage_estimate(
    event_name: str,
    verdict_path: Path = VERDICT_JSON,
    out_md: Path = REPORT_MD,
    out_json: Path = REPORT_JSON,
) -> None:
    con = _connect()
    event = get_event(event_name)
    panel = build_panel(con, event, unblind_post=True, verdict_path=verdict_path)
    result = fit_twfe(panel, event.outcome)
    pre = panel[~panel["post"]].reset_index(drop=True)
    verdict = evaluate_gate(event, pre)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(generate_did_report_md(event, result, verdict))
    write_results_json(
        {"event": event.name, "result": asdict(result), "gate": verdict}, out_json
    )
    print(f"wrote {out_md} and {out_json}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage", required=True, choices=["feasibility", "gate", "estimate"]
    )
    parser.add_argument("--event", default="truckers_strike_2018")
    args = parser.parse_args()
    if args.stage == "feasibility":
        stage_feasibility()
    elif args.stage == "gate":
        stage_gate(args.event)
    else:
        stage_estimate(args.event)


if __name__ == "__main__":
    main()
```

Note: `DidResult.ci` is a tuple — `asdict` serializes it; `results_to_json` turns tuples into
arrays. `generate_rejection_md` is imported for Task 10's FAIL path: if `stage_gate` writes
FAIL, the runner of the real pipeline writes the rejection via
`REJECTION_MD.write_text(generate_rejection_md(event, verdict))` — add that branch inside
`stage_gate` after `write_verdict`:

```python
    if verdict["verdict"] == "FAIL":
        REJECTION_MD.parent.mkdir(parents=True, exist_ok=True)
        REJECTION_MD.write_text(generate_rejection_md(event, verdict))
        print(f"wrote {REJECTION_MD}")
```

- [ ] **Step 4: Add Make targets** (match existing bare-`python` style):

```make
did-feasibility:
	python -m src.did.run_did --stage feasibility

did-gate:
	python -m src.did.run_did --stage gate

did:
	python -m src.did.run_did --stage estimate
```

Also add the three names to the `.PHONY` line.

- [ ] **Step 5: Run tests** → `.venv/bin/pytest tests/test_did_run.py -q` → PASS

- [ ] **Step 6: mypy + commit**

```bash
git add src/did/run_did.py tests/test_did_run.py Makefile
SKIP=gitleaks git commit -m "feat: DiD stage CLI (feasibility/gate/estimate) + make targets"
```

---

### Task 10: Full check + docs sync

**Files:**
- Modify: `docs/STATUS.md`, `README.md` (badge counts only, from real output)

- [ ] **Step 1: Full suite**

Run: `.venv/bin/pytest tests/ -q` and `.venv/bin/pytest tests/ --cov=src --cov-fail-under=90 -q`
and `.venv/bin/mypy src/ --strict` and `make lint`
Expected: all green. Record the real test count and coverage % from output.

- [ ] **Step 2: Update README badges** with the REAL counts from Step 1 (rule 1 — never guess).

- [ ] **Step 3: Overwrite `docs/STATUS.md`** (~40 lines, keep Caveats): Plan 4 infra complete
on `feat/plan4-did-natural-experiment`; catalog committed before any Phase B query (git
verifiable); next action = run `make did-feasibility` on full data (outcome-blind, safe), then
STOP for user review before Phase C pre-registration lock.

- [ ] **Step 4: Commit**

```bash
git add docs/STATUS.md README.md
SKIP=gitleaks git commit -m "docs: STATUS + badges — Plan 4 DiD infrastructure complete"
```

---

### Task 11: Phase B — run feasibility on full data (CHECKPOINT — stops here)

- [ ] **Step 1: Run** `.venv/bin/python -m src.did.run_did --stage feasibility`
Expected: writes `reports/did_feasibility.{md,json}`. This stage is outcome-blind by
construction (blinded panel; pre-period counts only) — safe to run without unlocking anything.

- [ ] **Step 2: Commit artifacts**

```bash
git add reports/did_feasibility.md reports/did_feasibility.json
SKIP=gitleaks git commit -m "feat: Phase B feasibility artifacts (outcome-blind, pre-period counts)"
```

- [ ] **Step 3: STOP.** Present the feasibility report to the user. Phase C (pre-registration
lock commit) and beyond require explicit user sign-off — the lock is a protocol commitment,
not an implementation detail. Do NOT run `--stage gate` or `--stage estimate`.

---

## Deferred to Phase E (after user sign-off at the Task 11 checkpoint)

- `make did-gate` (Phase C/D: pre-registration lock commit + verdict) and `make did`
  (estimate, GO only) run in a later session with the user.
- `tests/test_did_readout_integrity.py` — mirror of `tests/test_readout_integrity.py` for
  `reports/experiment_002_did.md` vs `.json` (or the rejection md vs verdict json). It can
  only be written once those artifacts exist; spec §9 requires it before that PR merges.

## Verification (whole plan)

- `make check` green (lint + mypy strict + coverage ≥90%).
- `git log` shows the catalog commit strictly before any feasibility artifact commit.
- `tests/test_did_panel.py::test_unblind_without_verdict_raises` proves blinding is
  code-enforced.
- No test loads `data/raw/olist` (grep tests/ for `raw_dir` usage — only `run_did` does,
  and its tests monkeypatch `_connect`).
