# Metrics & Simulated Experiment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the SQL metric layer and a simulated A/B experiment on Olist that emits `reports/experiment_001.md` with a ship/no-ship recommendation and a 95% CI.

**Architecture:** Clean `src/` layout (not hexagonal). SQL files in `sql/` are the single definition of each metric; thin Python wrappers in `src/` run them through DuckDB. The experiment builds a cohort frame, assigns variants by hashed `customer_unique_id`, injects a labeled synthetic effect, computes metrics per variant, and runs inference. Spec: `docs/superpowers/specs/2026-06-09-metrics-and-experiment-design.md`.

**Tech Stack:** Python 3.12, DuckDB, pandas, scipy, pytest. mypy strict on `src/`.

---

## Conventions for the implementing engineer

- Imports are absolute from the `src` package: `from src.constants import SEED`. `pytest` sets `pythonpath=["."]` (see `pyproject.toml`), so `import src.*` resolves from repo root.
- Every `src/` module is type-hinted (mypy `--strict`). DuckDB connection type is `duckdb.DuckDBPyConnection`.
- Tests use fixtures in `tests/fixtures/` (≤100 rows) and an in-memory DuckDB. Never load the full Olist dataset in a test.
- Local pre-commit note: the `gitleaks` hook may need `SKIP=gitleaks` if it cannot build (known local disk issue); never use `--no-verify`. Run hooks via the project `.venv`.
- Run tests with the venv: `.venv/bin/pytest`.

## File map (created in this plan)

```
src/__init__.py
src/constants.py              SEED, SIMULATED_EFFECT, cohort window, bootstrap/alpha, tolerances
src/_sql.py                   load_sql(rel) -> str   (locates sql/ dir)
src/io/__init__.py
src/io/loader.py              load_olist(con, raw_dir), build_experiment_frame(con)
src/experiment/__init__.py
src/experiment/assignment.py  assign_variant(uid, seed) -> "control"|"treatment"
src/experiment/effect.py      apply_simulated_effect(frame, effect)
src/experiment/analysis.py    bootstrap_ci_diff_means, welch_ttest, two_proportion_ztest
src/experiment/power.py       mde_proportion, mde_mean
src/experiment/balance.py     check_balance(frame)  -> raises on imbalance
src/experiment/run_experiment.py  run(con) -> results dict; main() writes report
src/metrics/__init__.py
src/metrics/conversion.py     conversion_by_variant(con) -> dict[str,float]
src/metrics/aov.py            aov_by_variant(con) -> dict[str,float]
src/metrics/d7_repeat.py      d7_repeat_by_variant(con) -> dict[str,float]
src/report/__init__.py
src/report/experiment_report.py  generate_report(results) -> str

sql/metrics/conversion.sql
sql/metrics/aov.sql
sql/metrics/d7_repeat.sql
sql/experiment/cohort.sql

tests/conftest.py             con fixture (in-memory duckdb from fixture CSVs); frame fixture
tests/fixtures/customers.csv
tests/fixtures/orders.csv
tests/fixtures/order_payments.csv
tests/fixtures/experiment_frame.csv
tests/test_assignment.py
tests/test_loader.py
tests/test_metrics.py
tests/test_effect.py
tests/test_analysis.py
tests/test_power.py
tests/test_report.py
tests/test_run_experiment.py

src/exceptions.py             ExperimentError and subclasses
Makefile                      add `experiment` target (modify)
```

## Module contracts (locked — later tasks depend on these exact names)

```python
# src/constants.py
SEED: int = 42
SIMULATED_EFFECT: float = 0.05
COHORT_START: str = "2017-01-01"
COHORT_END_EXCLUSIVE: str = "2018-09-01"   # window is [2017-01-01, 2018-08-31]
BOOTSTRAP_RESAMPLES: int = 10_000
ALPHA: float = 0.05
POWER: float = 0.80
IMBALANCE_TOLERANCE: float = 0.05            # max relative variant-size gap
DELIVERED_STATUS: str = "delivered"

# assign_variant(customer_unique_id: str, seed: int = SEED) -> str
# build_experiment_frame(con) -> pd.DataFrame
#   columns: order_id, customer_unique_id, order_status, order_value,
#            order_purchase_timestamp, variant
# apply_simulated_effect(frame: pd.DataFrame, effect: float = SIMULATED_EFFECT) -> pd.DataFrame
# conversion_by_variant(con) -> dict[str, float]      {variant: rate}
# aov_by_variant(con) -> dict[str, float]             {variant: mean order value}
# d7_repeat_by_variant(con) -> dict[str, float]       {variant: repeat rate}
# bootstrap_ci_diff_means(control, treatment, n_resamples=..., seed=..., alpha=...) -> tuple[float,float]
# welch_ttest(control, treatment) -> tuple[float, float]          (t, p)
# two_proportion_ztest(x_control, n_control, x_treatment, n_treatment, alpha=...) -> tuple[float,float,float,float]  (z, p, ci_lo, ci_hi)
# mde_proportion(p0, n, alpha=..., power=...) -> float
# mde_mean(sd, n, alpha=..., power=...) -> float
# check_balance(frame) -> None    (raises ImbalanceError)
# run(con) -> dict
# generate_report(results: dict) -> str
```

The metric SQL all run against a registered relation named `experiment_frame` with the columns above. `build_experiment_frame` produces it from base tables.

---

### Task 1: Package scaffold, constants, SQL loader, exceptions

**Files:**
- Create: `src/__init__.py` (empty), `src/io/__init__.py` (empty), `src/experiment/__init__.py` (empty), `src/metrics/__init__.py` (empty), `src/report/__init__.py` (empty)
- Create: `src/constants.py`, `src/_sql.py`, `src/exceptions.py`
- Test: `tests/test_constants.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_constants.py
from src import constants as c
from src._sql import load_sql


def test_seed_is_42():
    assert c.SEED == 42


def test_simulated_effect_labeled_and_positive():
    assert c.SIMULATED_EFFECT == 0.05


def test_cohort_window_excludes_censored_tail():
    assert c.COHORT_START == "2017-01-01"
    assert c.COHORT_END_EXCLUSIVE == "2018-09-01"


def test_load_sql_reads_file(tmp_path, monkeypatch):
    import src._sql as sql_mod

    d = tmp_path / "sql" / "metrics"
    d.mkdir(parents=True)
    (d / "x.sql").write_text("SELECT 1")
    monkeypatch.setattr(sql_mod, "SQL_DIR", tmp_path / "sql")
    assert sql_mod.load_sql("metrics/x.sql") == "SELECT 1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_constants.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.constants'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/constants.py
"""Single source of truth for experiment parameters. Pinned for reproducibility."""

SEED: int = 42
SIMULATED_EFFECT: float = 0.05
COHORT_START: str = "2017-01-01"
COHORT_END_EXCLUSIVE: str = "2018-09-01"
BOOTSTRAP_RESAMPLES: int = 10_000
ALPHA: float = 0.05
POWER: float = 0.80
IMBALANCE_TOLERANCE: float = 0.05
DELIVERED_STATUS: str = "delivered"
```

```python
# src/_sql.py
"""Locate and read versioned SQL files."""

from pathlib import Path

SQL_DIR: Path = Path(__file__).resolve().parent.parent / "sql"


def load_sql(rel: str) -> str:
    return (SQL_DIR / rel).read_text()
```

```python
# src/exceptions.py
"""Domain errors. Fail loud — never silently continue on invalid pipeline state."""


class ExperimentError(Exception):
    """Base for all experiment-pipeline errors."""


class EmptyCohortError(ExperimentError):
    """Cohort filter returned zero rows."""


class MissingColumnError(ExperimentError):
    """A required column is absent from an input table."""


class ImbalanceError(ExperimentError):
    """Variant sizes differ beyond the configured tolerance."""
```

Create the five empty `__init__.py` files.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_constants.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add src/ tests/test_constants.py
git commit -m "feat: add package scaffold, constants, sql loader, exceptions"
```

---

### Task 2: Variant assignment

**Files:**
- Create: `src/experiment/assignment.py`
- Test: `tests/test_assignment.py`

Verified facts (seed 42): `u1`→treatment, `u2`→control, `u3`→control, `u4`→treatment, `u5`→control. Odd last md5 hex nibble → treatment.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_assignment.py
import pytest

from src.experiment.assignment import assign_variant


@pytest.mark.parametrize(
    "uid,expected",
    [("u1", "treatment"), ("u2", "control"), ("u3", "control"),
     ("u4", "treatment"), ("u5", "control")],
)
def test_known_assignments_seed_42(uid, expected):
    assert assign_variant(uid) == expected


def test_deterministic():
    assert assign_variant("abc") == assign_variant("abc")


def test_only_two_variants():
    assert assign_variant("anything") in {"control", "treatment"}


def test_seed_changes_assignment_space():
    # different seed is allowed to differ; just must stay valid
    assert assign_variant("u1", seed=7) in {"control", "treatment"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_assignment.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/experiment/assignment.py
"""Person-level random assignment. Depends only on id + seed — never on outcomes."""

import hashlib

from src.constants import SEED


def assign_variant(customer_unique_id: str, seed: int = SEED) -> str:
    digest = hashlib.md5(f"{customer_unique_id}-{seed}".encode()).hexdigest()
    return "treatment" if int(digest, 16) % 2 == 1 else "control"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_assignment.py -v`
Expected: PASS (8 passed)

- [ ] **Step 5: Commit**

```bash
git add src/experiment/assignment.py tests/test_assignment.py
git commit -m "feat: add person-level variant assignment"
```

---

### Task 3: Test fixtures and conftest

**Files:**
- Create: `tests/fixtures/customers.csv`, `tests/fixtures/orders.csv`, `tests/fixtures/order_payments.csv`, `tests/fixtures/experiment_frame.csv`
- Create: `tests/conftest.py`
- Test: `tests/test_conftest_sanity.py`

Fixture is built so variants match real seed-42 hashes: u1,u4=treatment; u2,u3,u5=control.

- [ ] **Step 1: Write the fixture files**

`tests/fixtures/customers.csv`:
```csv
customer_id,customer_unique_id,customer_state
c1,u1,SP
c2,u2,RJ
c3,u1,SP
c4,u3,MG
c5,u4,SP
c6,u5,RJ
```

`tests/fixtures/orders.csv`:
```csv
order_id,customer_id,order_status,order_purchase_timestamp
o1,c1,delivered,2017-05-01 10:00:00
o2,c2,delivered,2017-06-01 10:00:00
o3,c3,delivered,2017-05-04 10:00:00
o4,c4,canceled,2017-07-01 10:00:00
o5,c5,delivered,2018-01-01 10:00:00
o6,c6,shipped,2018-02-01 10:00:00
```

`tests/fixtures/order_payments.csv` (o1 has two payment rows → order_value 120):
```csv
order_id,payment_sequential,payment_type,payment_value
o1,1,credit_card,100.00
o1,2,voucher,20.00
o2,1,credit_card,50.00
o3,1,boleto,30.00
o4,1,credit_card,200.00
o5,1,credit_card,80.00
o6,1,credit_card,60.00
```

`tests/fixtures/experiment_frame.csv` (already cohort-filtered + assigned; the metrics run on this):
```csv
order_id,customer_unique_id,order_status,order_value,order_purchase_timestamp,variant
o1,u1,delivered,120.00,2017-05-01 10:00:00,treatment
o2,u2,delivered,50.00,2017-06-01 10:00:00,control
o3,u1,delivered,30.00,2017-05-04 10:00:00,treatment
o4,u3,canceled,200.00,2017-07-01 10:00:00,control
o5,u4,delivered,80.00,2018-01-01 10:00:00,treatment
o6,u5,shipped,60.00,2018-02-01 10:00:00,control
```

- [ ] **Step 2: Write conftest**

```python
# tests/conftest.py
from pathlib import Path

import duckdb
import pandas as pd
import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def base_con():
    """In-memory DuckDB with the raw Olist base tables registered from fixtures."""
    con = duckdb.connect(":memory:")
    for name in ["customers", "orders", "order_payments"]:
        df = pd.read_csv(FIXTURES / f"{name}.csv")
        if "timestamp" in "".join(df.columns):
            for col in df.columns:
                if col.endswith("timestamp"):
                    df[col] = pd.to_datetime(df[col])
        con.register(name, df)
    yield con
    con.close()


@pytest.fixture
def frame() -> pd.DataFrame:
    df = pd.read_csv(FIXTURES / "experiment_frame.csv")
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    return df


@pytest.fixture
def frame_con(frame):
    """In-memory DuckDB with the experiment_frame registered for metric SQL."""
    con = duckdb.connect(":memory:")
    con.register("experiment_frame", frame)
    yield con
    con.close()
```

- [ ] **Step 3: Write sanity test**

```python
# tests/test_conftest_sanity.py
def test_base_con_has_orders(base_con):
    assert base_con.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 6


def test_frame_has_six_rows(frame):
    assert len(frame) == 6
    assert set(frame["variant"]) == {"control", "treatment"}
```

- [ ] **Step 4: Run tests**

Run: `.venv/bin/pytest tests/test_conftest_sanity.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/ tests/conftest.py tests/test_conftest_sanity.py
git commit -m "test: add tiny olist fixtures and duckdb conftest"
```

---

### Task 4: Conversion metric (guardrail)

**Files:**
- Create: `sql/metrics/conversion.sql`, `src/metrics/conversion.py`
- Test: `tests/test_metrics.py`

Expected on fixture: control = 1/3 ≈ 0.33333, treatment = 1.0.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_metrics.py
import pandas as pd
import pytest

from src.metrics.conversion import conversion_by_variant


def _pandas_conversion(frame: pd.DataFrame) -> dict[str, float]:
    delivered = frame["order_status"] == "delivered"
    return frame.assign(d=delivered).groupby("variant")["d"].mean().to_dict()


def test_conversion_matches_pandas(frame_con, frame):
    sql_result = conversion_by_variant(frame_con)
    pd_result = _pandas_conversion(frame)
    assert sql_result["control"] == pytest.approx(pd_result["control"])
    assert sql_result["treatment"] == pytest.approx(pd_result["treatment"])


def test_conversion_known_values(frame_con):
    r = conversion_by_variant(frame_con)
    assert r["control"] == pytest.approx(1 / 3)
    assert r["treatment"] == pytest.approx(1.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_metrics.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.metrics.conversion'`

- [ ] **Step 3: Write SQL and wrapper**

```sql
-- sql/metrics/conversion.sql
-- Delivered rate per variant. Runs on the registered experiment_frame relation.
SELECT
    variant,
    AVG(CASE WHEN order_status = 'delivered' THEN 1.0 ELSE 0.0 END) AS conversion,
    COUNT(*) AS n
FROM experiment_frame
GROUP BY variant
ORDER BY variant;
```

```python
# src/metrics/conversion.py
"""Conversion (delivered rate) per variant. Definition lives in sql/metrics/conversion.sql."""

import duckdb

from src._sql import load_sql


def conversion_by_variant(con: duckdb.DuckDBPyConnection) -> dict[str, float]:
    rows = con.execute(load_sql("metrics/conversion.sql")).fetchall()
    return {str(r[0]): float(r[1]) for r in rows}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_metrics.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add sql/metrics/conversion.sql src/metrics/conversion.py tests/test_metrics.py
git commit -m "feat: add conversion metric (sql + wrapper) with pandas-parity test"
```

---

### Task 5: AOV metric (primary)

**Files:**
- Create: `sql/metrics/aov.sql`, `src/metrics/aov.py`
- Modify: `tests/test_metrics.py` (add AOV tests)

Expected on fixture: control = (50+200+60)/3 = 103.33333, treatment = (120+30+80)/3 = 76.66667.

- [ ] **Step 1: Add the failing test**

```python
# append to tests/test_metrics.py
from src.metrics.aov import aov_by_variant


def _pandas_aov(frame: pd.DataFrame) -> dict[str, float]:
    return frame.groupby("variant")["order_value"].mean().to_dict()


def test_aov_matches_pandas(frame_con, frame):
    sql_result = aov_by_variant(frame_con)
    pd_result = _pandas_aov(frame)
    assert sql_result["control"] == pytest.approx(pd_result["control"])
    assert sql_result["treatment"] == pytest.approx(pd_result["treatment"])


def test_aov_known_values(frame_con):
    r = aov_by_variant(frame_con)
    assert r["control"] == pytest.approx(310 / 3)
    assert r["treatment"] == pytest.approx(230 / 3)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_metrics.py -k aov -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.metrics.aov'`

- [ ] **Step 3: Write SQL and wrapper**

```sql
-- sql/metrics/aov.sql
-- Average order value per variant. order_value is SUM(payment_value) per order,
-- already aggregated into experiment_frame.
SELECT
    variant,
    AVG(order_value) AS aov,
    COUNT(order_value) AS n
FROM experiment_frame
WHERE order_value IS NOT NULL
GROUP BY variant
ORDER BY variant;
```

```python
# src/metrics/aov.py
"""Average order value per variant. Definition lives in sql/metrics/aov.sql."""

import duckdb

from src._sql import load_sql


def aov_by_variant(con: duckdb.DuckDBPyConnection) -> dict[str, float]:
    rows = con.execute(load_sql("metrics/aov.sql")).fetchall()
    return {str(r[0]): float(r[1]) for r in rows}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_metrics.py -k aov -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add sql/metrics/aov.sql src/metrics/aov.py tests/test_metrics.py
git commit -m "feat: add aov metric (sql + wrapper) with pandas-parity test"
```

---

### Task 6: D7 repeat metric (exploratory)

**Files:**
- Create: `sql/metrics/d7_repeat.sql`, `src/metrics/d7_repeat.py`
- Modify: `tests/test_metrics.py` (add D7 tests)

Expected on fixture: treatment = 0.5 (u1 repeats within 7d, u4 does not → 1/2), control = 0.0.

- [ ] **Step 1: Add the failing test**

```python
# append to tests/test_metrics.py
from src.metrics.d7_repeat import d7_repeat_by_variant


def test_d7_known_values(frame_con):
    r = d7_repeat_by_variant(frame_con)
    assert r["treatment"] == pytest.approx(0.5)
    assert r["control"] == pytest.approx(0.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_metrics.py -k d7 -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.metrics.d7_repeat'`

- [ ] **Step 3: Write SQL and wrapper**

```sql
-- sql/metrics/d7_repeat.sql
-- Share of persons whose 2nd order falls within 7 days of their 1st, per variant.
WITH firsts AS (
    SELECT customer_unique_id, variant, MIN(order_purchase_timestamp) AS first_ts
    FROM experiment_frame
    GROUP BY customer_unique_id, variant
),
flags AS (
    SELECT
        f.customer_unique_id,
        f.variant,
        MAX(CASE
                WHEN e.order_purchase_timestamp > f.first_ts
                 AND e.order_purchase_timestamp <= f.first_ts + INTERVAL 7 DAY
                THEN 1 ELSE 0
            END) AS repeated
    FROM firsts f
    JOIN experiment_frame e
      ON e.customer_unique_id = f.customer_unique_id
     AND e.variant = f.variant
    GROUP BY f.customer_unique_id, f.variant
)
SELECT variant, AVG(repeated) AS d7_repeat, COUNT(*) AS n_persons
FROM flags
GROUP BY variant
ORDER BY variant;
```

```python
# src/metrics/d7_repeat.py
"""D7 repeat-purchase rate per variant. Definition lives in sql/metrics/d7_repeat.sql."""

import duckdb

from src._sql import load_sql


def d7_repeat_by_variant(con: duckdb.DuckDBPyConnection) -> dict[str, float]:
    rows = con.execute(load_sql("metrics/d7_repeat.sql")).fetchall()
    return {str(r[0]): float(r[1]) for r in rows}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_metrics.py -k d7 -v`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add sql/metrics/d7_repeat.sql src/metrics/d7_repeat.py tests/test_metrics.py
git commit -m "feat: add d7 repeat metric (sql + wrapper) with parity test"
```

---

### Task 7: Cohort + experiment frame loader

**Files:**
- Create: `sql/experiment/cohort.sql`, `src/io/loader.py`
- Test: `tests/test_loader.py`

`build_experiment_frame` runs `cohort.sql` (join + payment aggregation + window filter), then applies `assign_variant` in Python. On the fixture all 6 orders fall in the window, so the frame has 6 rows and variants match the seed-42 hashes.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_loader.py
import pytest

from src.exceptions import EmptyCohortError
from src.io.loader import build_experiment_frame


def test_frame_columns_and_size(base_con):
    df = build_experiment_frame(base_con)
    assert set(df.columns) == {
        "order_id", "customer_unique_id", "order_status",
        "order_value", "order_purchase_timestamp", "variant",
    }
    assert len(df) == 6


def test_order_value_aggregates_multi_payment(base_con):
    df = build_experiment_frame(base_con)
    assert df.loc[df["order_id"] == "o1", "order_value"].iloc[0] == pytest.approx(120.0)


def test_variants_match_seed_42(base_con):
    df = build_experiment_frame(base_con).set_index("order_id")
    assert df.loc["o1", "variant"] == "treatment"  # u1
    assert df.loc["o2", "variant"] == "control"     # u2


def test_person_orders_share_one_variant(base_con):
    df = build_experiment_frame(base_con)
    per_person = df.groupby("customer_unique_id")["variant"].nunique()
    assert (per_person == 1).all()


def test_empty_cohort_raises(base_con):
    base_con.execute("DELETE FROM orders")
    with pytest.raises(EmptyCohortError):
        build_experiment_frame(base_con)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_loader.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.io.loader'`

- [ ] **Step 3: Write SQL and loader**

```sql
-- sql/experiment/cohort.sql
-- Cohort orders in the stable window, with order_value = SUM(payment_value) per order.
-- Window bounds are passed as parameters ($start, $end) from src.constants.
SELECT
    o.order_id,
    c.customer_unique_id,
    o.order_status,
    p.order_value,
    o.order_purchase_timestamp
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN (
    SELECT order_id, SUM(payment_value) AS order_value
    FROM order_payments
    GROUP BY order_id
) p ON o.order_id = p.order_id
WHERE o.order_purchase_timestamp >= $start
  AND o.order_purchase_timestamp <  $end;
```

```python
# src/io/loader.py
"""Load Olist into DuckDB and build the cohort experiment frame."""

from pathlib import Path

import duckdb
import pandas as pd

from src._sql import load_sql
from src.constants import COHORT_END_EXCLUSIVE, COHORT_START
from src.exceptions import EmptyCohortError
from src.experiment.assignment import assign_variant

_TABLES = ["orders", "order_items", "order_payments", "customers"]


def load_olist(con: duckdb.DuckDBPyConnection, raw_dir: Path) -> None:
    """Register the raw Olist CSVs as DuckDB views (parses timestamp columns)."""
    for name in _TABLES:
        df = pd.read_csv(raw_dir / f"olist_{name}_dataset.csv")
        for col in df.columns:
            if col.endswith("timestamp"):
                df[col] = pd.to_datetime(df[col], errors="coerce")
        con.register(name, df)


def build_experiment_frame(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    df = con.execute(
        load_sql("experiment/cohort.sql"),
        {"start": COHORT_START, "end": COHORT_END_EXCLUSIVE},
    ).fetchdf()
    if df.empty:
        raise EmptyCohortError("cohort filter returned zero rows")
    df["variant"] = df["customer_unique_id"].map(assign_variant)
    return df
```

Note: the fixture registers tables as `orders`/`customers`/`order_payments` already (Task 3 conftest `base_con`), so `cohort.sql` runs directly. `load_olist` is exercised against real data in Task 12, not in unit tests.

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_loader.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add sql/experiment/cohort.sql src/io/loader.py tests/test_loader.py
git commit -m "feat: add cohort sql and experiment-frame builder"
```

---

### Task 8: Simulated effect injection

**Files:**
- Create: `src/experiment/effect.py`
- Test: `tests/test_effect.py`

Expected: treatment order_value ×1.05 (120→126, 30→31.5, 80→84); control unchanged.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_effect.py
import pytest

from src.experiment.effect import apply_simulated_effect


def test_treatment_values_scaled(frame):
    out = apply_simulated_effect(frame).set_index("order_id")
    assert out.loc["o1", "order_value"] == pytest.approx(126.0)
    assert out.loc["o3", "order_value"] == pytest.approx(31.5)
    assert out.loc["o5", "order_value"] == pytest.approx(84.0)


def test_control_values_unchanged(frame):
    out = apply_simulated_effect(frame).set_index("order_id")
    assert out.loc["o2", "order_value"] == pytest.approx(50.0)
    assert out.loc["o4", "order_value"] == pytest.approx(200.0)


def test_input_not_mutated(frame):
    apply_simulated_effect(frame)
    assert frame.set_index("order_id").loc["o1", "order_value"] == pytest.approx(120.0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_effect.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/experiment/effect.py
"""Inject the labeled synthetic treatment effect. SIMULATED — not a real lift."""

import pandas as pd

from src.constants import SIMULATED_EFFECT


def apply_simulated_effect(
    frame: pd.DataFrame, effect: float = SIMULATED_EFFECT
) -> pd.DataFrame:
    out = frame.copy()
    is_treatment = out["variant"] == "treatment"
    out.loc[is_treatment, "order_value"] = out.loc[is_treatment, "order_value"] * (1 + effect)
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_effect.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add src/experiment/effect.py tests/test_effect.py
git commit -m "feat: add labeled simulated-effect injection"
```

---

### Task 9: Inference (bootstrap CI, Welch t-test, two-proportion z)

**Files:**
- Create: `src/experiment/analysis.py`
- Test: `tests/test_analysis.py`

Verified references: Welch `ttest_ind(treatment=[120,30,80], control=[50,200,60], equal_var=False)` → t=-0.485071, p=0.660167. Two-proportion z (control 2/4, treatment 4/4) → z=1.632993, p=0.10247, CI=(0.010009, 0.989991).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_analysis.py
import numpy as np
import pytest

from src.experiment.analysis import (
    bootstrap_ci_diff_means,
    two_proportion_ztest,
    welch_ttest,
)


def test_bootstrap_is_reproducible():
    a, b = [50.0, 200.0, 60.0], [120.0, 30.0, 80.0]
    assert bootstrap_ci_diff_means(a, b, n_resamples=2000, seed=42) == \
        bootstrap_ci_diff_means(a, b, n_resamples=2000, seed=42)


def test_bootstrap_recovers_known_positive_effect():
    rng = np.random.default_rng(0)
    control = rng.normal(100, 5, 500)
    treatment = control + 10
    lo, hi = bootstrap_ci_diff_means(control, treatment, n_resamples=2000, seed=42)
    assert lo > 0          # effect is detected
    assert lo <= 10 <= hi  # true effect inside CI


def test_welch_matches_reference():
    t, p = welch_ttest([50.0, 200.0, 60.0], [120.0, 30.0, 80.0])
    assert t == pytest.approx(-0.485071, abs=1e-5)
    assert p == pytest.approx(0.660167, abs=1e-5)


def test_two_proportion_ztest_reference():
    z, p, lo, hi = two_proportion_ztest(2, 4, 4, 4)
    assert z == pytest.approx(1.632993, abs=1e-5)
    assert p == pytest.approx(0.10247, abs=1e-4)
    assert lo == pytest.approx(0.010009, abs=1e-4)
    assert hi == pytest.approx(0.989991, abs=1e-4)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_analysis.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/experiment/analysis.py
"""Inference: bootstrap CI for AOV, Welch t-test cross-check, two-proportion z for conversion."""

from collections.abc import Sequence

import numpy as np
from scipy import stats

from src.constants import ALPHA, BOOTSTRAP_RESAMPLES, SEED


def bootstrap_ci_diff_means(
    control: Sequence[float],
    treatment: Sequence[float],
    n_resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = SEED,
    alpha: float = ALPHA,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    c = np.asarray(control, dtype=float)
    t = np.asarray(treatment, dtype=float)
    diffs = np.empty(n_resamples, dtype=float)
    for i in range(n_resamples):
        cs = rng.choice(c, size=c.size, replace=True)
        ts = rng.choice(t, size=t.size, replace=True)
        diffs[i] = ts.mean() - cs.mean()
    lo = float(np.percentile(diffs, 100 * alpha / 2))
    hi = float(np.percentile(diffs, 100 * (1 - alpha / 2)))
    return lo, hi


def welch_ttest(
    control: Sequence[float], treatment: Sequence[float]
) -> tuple[float, float]:
    result = stats.ttest_ind(treatment, control, equal_var=False)
    return float(result.statistic), float(result.pvalue)


def two_proportion_ztest(
    x_control: int,
    n_control: int,
    x_treatment: int,
    n_treatment: int,
    alpha: float = ALPHA,
) -> tuple[float, float, float, float]:
    p1 = x_control / n_control
    p2 = x_treatment / n_treatment
    pool = (x_control + x_treatment) / (n_control + n_treatment)
    se = np.sqrt(pool * (1 - pool) * (1 / n_control + 1 / n_treatment))
    z = (p2 - p1) / se
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    z_crit = stats.norm.ppf(1 - alpha / 2)
    se_diff = np.sqrt(p1 * (1 - p1) / n_control + p2 * (1 - p2) / n_treatment)
    lo = (p2 - p1) - z_crit * se_diff
    hi = (p2 - p1) + z_crit * se_diff
    return float(z), float(p), float(lo), float(hi)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_analysis.py -v`
Expected: PASS (4 passed)

- [ ] **Step 5: Commit**

```bash
git add src/experiment/analysis.py tests/test_analysis.py
git commit -m "feat: add bootstrap ci, welch t-test, two-proportion z"
```

---

### Task 10: Power / MDE

**Files:**
- Create: `src/experiment/power.py`
- Test: `tests/test_power.py`

Verified references: `mde_proportion(0.5, 100)` ≈ 0.198102; `mde_mean(10, 100)` ≈ 3.96204.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_power.py
import pytest

from src.experiment.power import mde_mean, mde_proportion


def test_mde_proportion_reference():
    assert mde_proportion(0.5, 100) == pytest.approx(0.198102, abs=1e-5)


def test_mde_mean_reference():
    assert mde_mean(10.0, 100) == pytest.approx(3.96204, abs=1e-5)


def test_mde_shrinks_with_n():
    assert mde_mean(10.0, 1000) < mde_mean(10.0, 100)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_power.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/experiment/power.py
"""Minimum detectable effect at a target power. Documents experiment sensitivity."""

import numpy as np
from scipy import stats

from src.constants import ALPHA, POWER


def _z(alpha: float, power: float) -> tuple[float, float]:
    return float(stats.norm.ppf(1 - alpha / 2)), float(stats.norm.ppf(power))


def mde_proportion(
    p0: float, n: int, alpha: float = ALPHA, power: float = POWER
) -> float:
    za, zb = _z(alpha, power)
    return float((za + zb) * np.sqrt(2 * p0 * (1 - p0) / n))


def mde_mean(sd: float, n: int, alpha: float = ALPHA, power: float = POWER) -> float:
    za, zb = _z(alpha, power)
    return float((za + zb) * sd * np.sqrt(2 / n))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_power.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add src/experiment/power.py tests/test_power.py
git commit -m "feat: add power/mde calculations"
```

---

### Task 11: Balance check

**Files:**
- Create: `src/experiment/balance.py`
- Test: `tests/test_balance.py`

`check_balance` raises `ImbalanceError` when the relative gap between variant counts exceeds `IMBALANCE_TOLERANCE`. Fixture (3 vs 3) passes.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_balance.py
import pandas as pd
import pytest

from src.exceptions import ImbalanceError
from src.experiment.balance import check_balance


def test_balanced_frame_passes(frame):
    check_balance(frame)  # 3 vs 3, no raise


def test_imbalanced_frame_raises():
    df = pd.DataFrame({"variant": ["control"] * 10 + ["treatment"] * 2})
    with pytest.raises(ImbalanceError):
        check_balance(df)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_balance.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/experiment/balance.py
"""Guard against a broken hash or filter producing lopsided variants."""

import pandas as pd

from src.constants import IMBALANCE_TOLERANCE
from src.exceptions import ImbalanceError


def check_balance(frame: pd.DataFrame, tolerance: float = IMBALANCE_TOLERANCE) -> None:
    counts = frame["variant"].value_counts()
    control = int(counts.get("control", 0))
    treatment = int(counts.get("treatment", 0))
    larger = max(control, treatment)
    if larger == 0:
        raise ImbalanceError("no rows in either variant")
    gap = abs(control - treatment) / larger
    if gap > tolerance:
        raise ImbalanceError(
            f"variant imbalance {gap:.3f} exceeds tolerance {tolerance} "
            f"(control={control}, treatment={treatment})"
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_balance.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add src/experiment/balance.py tests/test_balance.py
git commit -m "feat: add variant balance guard"
```

---

### Task 12: Report generator

**Files:**
- Create: `src/report/experiment_report.py`
- Test: `tests/test_report.py`

`generate_report` takes a results dict and returns markdown. The recommendation is derived from the AOV bootstrap CI: lo > 0 → SHIP; hi < 0 → DO NOT SHIP; else NEED MORE DATA. A simulation disclaimer is always present.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_report.py
from src.report.experiment_report import generate_report

RESULTS = {
    "sample_sizes": {"control": 49575, "treatment": 49866},
    "aov": {"control": 160.0, "treatment": 168.0, "lift": 8.0,
            "ci": (3.0, 13.0), "p": 0.001},
    "conversion": {"control": 0.97, "treatment": 0.971, "z": 0.5,
                   "p": 0.61, "ci": (-0.002, 0.004)},
    "d7": {"control": 0.002, "treatment": 0.0022},
    "mde": {"aov": 3.95, "conversion": 0.003},
    "simulated_effect": 0.05,
}


def test_disclaimer_present():
    md = generate_report(RESULTS)
    assert "simulated" in md.lower()
    assert "SIMULATED_EFFECT" in md or "0.05" in md


def test_ship_when_ci_positive():
    md = generate_report(RESULTS)
    assert "SHIP" in md


def test_do_not_ship_when_ci_negative():
    r = dict(RESULTS)
    r["aov"] = {**RESULTS["aov"], "lift": -8.0, "ci": (-13.0, -3.0)}
    assert "DO NOT SHIP" in generate_report(r)


def test_need_more_data_when_ci_spans_zero():
    r = dict(RESULTS)
    r["aov"] = {**RESULTS["aov"], "lift": 1.0, "ci": (-2.0, 4.0)}
    assert "NEED MORE DATA" in generate_report(r)


def test_sample_sizes_rendered():
    md = generate_report(RESULTS)
    assert "49575" in md and "49866" in md
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_report.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/report/experiment_report.py
"""Render the experiment results to markdown. No number is hand-entered upstream."""

DISCLAIMER = (
    "> **Simulated experiment.** Olist has no native A/B test. Variants are assigned by "
    "hashed `customer_unique_id` (seed 42) on historical data, and the treatment effect is "
    "a synthetic `SIMULATED_EFFECT` injected for methodology demonstration. Not a real lift."
)


def _recommend(ci: tuple[float, float]) -> str:
    lo, hi = ci
    if lo > 0:
        return "SHIP"
    if hi < 0:
        return "DO NOT SHIP"
    return "NEED MORE DATA"


def generate_report(results: dict) -> str:
    ss = results["sample_sizes"]
    aov = results["aov"]
    conv = results["conversion"]
    d7 = results["d7"]
    mde = results["mde"]
    rec = _recommend(aov["ci"])
    lines = [
        "# Experiment 001 — Simulated AOV Lift",
        "",
        DISCLAIMER,
        "",
        f"Injected `SIMULATED_EFFECT` = {results['simulated_effect']}",
        "",
        "## Sample sizes",
        f"- control: {ss['control']}",
        f"- treatment: {ss['treatment']}",
        "",
        "## Metrics",
        "",
        "| Metric | Control | Treatment | Lift | 95% CI | p |",
        "|---|---|---|---|---|---|",
        f"| AOV (primary) | {aov['control']:.2f} | {aov['treatment']:.2f} | "
        f"{aov['lift']:.2f} | ({aov['ci'][0]:.2f}, {aov['ci'][1]:.2f}) | {aov['p']:.4f} |",
        f"| Conversion (guardrail) | {conv['control']:.4f} | {conv['treatment']:.4f} | "
        f"{conv['treatment'] - conv['control']:.4f} | "
        f"({conv['ci'][0]:.4f}, {conv['ci'][1]:.4f}) | {conv['p']:.4f} |",
        f"| D7 repeat (exploratory) | {d7['control']:.4f} | {d7['treatment']:.4f} | — | — | — |",
        "",
        "## Power",
        f"- AOV MDE: {mde['aov']:.2f}",
        f"- Conversion MDE: {mde['conversion']:.4f}",
        "",
        "## Recommendation",
        f"**{rec}** — based on the AOV 95% bootstrap CI "
        f"({aov['ci'][0]:.2f}, {aov['ci'][1]:.2f}).",
        "",
    ]
    return "\n".join(lines)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_report.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add src/report/experiment_report.py tests/test_report.py
git commit -m "feat: add markdown experiment report generator"
```

---

### Task 13: Experiment runner (end-to-end on fixtures) + Makefile target

**Files:**
- Create: `src/experiment/run_experiment.py`
- Modify: `Makefile` (add `experiment` target)
- Test: `tests/test_run_experiment.py`

`run(con)` ties the pipeline together: build frame → balance check → inject effect → metrics (register injected frame) → inference → assemble results dict. `main()` runs it on the real data and writes `reports/experiment_001.md`. The unit test runs `run` on fixtures and checks the result shape and that the injected positive effect yields a non-empty recommendation. `main()` is not unit-tested (no full-data load in tests).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_run_experiment.py
from src.experiment.run_experiment import run
from src.report.experiment_report import generate_report


def test_run_returns_expected_shape(base_con):
    results = run(base_con)
    assert set(results) >= {
        "sample_sizes", "aov", "conversion", "d7", "mde", "simulated_effect"
    }
    assert results["sample_sizes"]["control"] == 3
    assert results["sample_sizes"]["treatment"] == 3
    assert results["simulated_effect"] == 0.05


def test_run_feeds_report(base_con):
    md = generate_report(run(base_con))
    assert "Recommendation" in md
    assert "simulated" in md.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_run_experiment.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/experiment/run_experiment.py
"""Assemble the full simulated experiment and write the report."""

from pathlib import Path

import duckdb

from src.constants import ALPHA, DELIVERED_STATUS, SIMULATED_EFFECT
from src.experiment.analysis import (
    bootstrap_ci_diff_means,
    two_proportion_ztest,
    welch_ttest,
)
from src.experiment.balance import check_balance
from src.experiment.effect import apply_simulated_effect
from src.experiment.power import mde_mean, mde_proportion
from src.io.loader import build_experiment_frame, load_olist
from src.metrics.aov import aov_by_variant
from src.metrics.conversion import conversion_by_variant
from src.metrics.d7_repeat import d7_repeat_by_variant
from src.report.experiment_report import generate_report

RAW_DIR = Path("data/raw/olist")
REPORT_PATH = Path("reports/experiment_001.md")


def run(con: duckdb.DuckDBPyConnection) -> dict:
    frame = build_experiment_frame(con)
    check_balance(frame)
    injected = apply_simulated_effect(frame)
    con.register("experiment_frame", injected)

    aov = aov_by_variant(con)
    conv = conversion_by_variant(con)
    d7 = d7_repeat_by_variant(con)

    ctrl_vals = injected.loc[injected["variant"] == "control", "order_value"].to_numpy()
    treat_vals = injected.loc[injected["variant"] == "treatment", "order_value"].to_numpy()
    ci = bootstrap_ci_diff_means(ctrl_vals, treat_vals)
    _, aov_p = welch_ttest(ctrl_vals, treat_vals)

    counts = injected["variant"].value_counts()
    n_ctrl, n_treat = int(counts["control"]), int(counts["treatment"])
    x_ctrl = int((injected["variant"].eq("control") & injected["order_status"].eq(DELIVERED_STATUS)).sum())
    x_treat = int((injected["variant"].eq("treatment") & injected["order_status"].eq(DELIVERED_STATUS)).sum())
    _, conv_p, conv_lo, conv_hi = two_proportion_ztest(x_ctrl, n_ctrl, x_treat, n_treat)

    return {
        "sample_sizes": {"control": n_ctrl, "treatment": n_treat},
        "aov": {
            "control": aov["control"], "treatment": aov["treatment"],
            "lift": aov["treatment"] - aov["control"], "ci": ci, "p": aov_p,
        },
        "conversion": {
            "control": conv["control"], "treatment": conv["treatment"],
            "z": 0.0, "p": conv_p, "ci": (conv_lo, conv_hi),
        },
        "d7": {"control": d7.get("control", 0.0), "treatment": d7.get("treatment", 0.0)},
        "mde": {
            "aov": mde_mean(float(treat_vals.std(ddof=1)) if treat_vals.size > 1 else 0.0, n_treat),
            "conversion": mde_proportion(conv["control"] or 0.0001, n_ctrl),
        },
        "simulated_effect": SIMULATED_EFFECT,
        "alpha": ALPHA,
    }


def main() -> None:
    con = duckdb.connect(":memory:")
    load_olist(con, RAW_DIR)
    results = run(con)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(generate_report(results))
    print(f"wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_run_experiment.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Add Makefile target and run on real data**

Add to `Makefile`:
```makefile
experiment:
	.venv/bin/python -m src.experiment.run_experiment
```

Run: `make experiment`
Expected: prints `wrote reports/experiment_001.md`; open the file and confirm it shows a SHIP recommendation (the +5% injected effect on ~50k/arm sits well above the AOV MDE).

- [ ] **Step 6: Commit**

```bash
git add src/experiment/run_experiment.py tests/test_run_experiment.py Makefile reports/experiment_001.md
git commit -m "feat: wire end-to-end simulated experiment and report"
```

---

### Task 14: Full suite, leakage audit, docs

**Files:**
- Create: `docs/METRICS.md`, `docs/EXPERIMENT_DESIGN.md`
- Modify: `README.md` (honesty banner + reproduce steps)

- [ ] **Step 1: Run the full suite with coverage**

Run: `.venv/bin/pytest -v` then `make test-cov`
Expected: all tests pass; coverage on `src/` meets the project gate (90%).

- [ ] **Step 2: Run the leakage auditor**

Dispatch the `leakage-auditor` agent over `src/experiment/` and `tests/`. Confirm: assignment reads only id+seed; effect is labeled `SIMULATED_EFFECT`; seed 42 in assignment and bootstrap; tests load fixtures only. Fix any finding before proceeding.

- [ ] **Step 3: Write docs/METRICS.md and docs/EXPERIMENT_DESIGN.md**

Promote the spec's metric and design sections into `docs/METRICS.md` (the three definitions, their SQL paths, the AOV multi-payment rule, person-key rule) and `docs/EXPERIMENT_DESIGN.md` (cohort window, assignment, injected effect, inference, power). Reference `reports/eda_gate.md` for the numbers that justify each choice. Keep prose plain — no inflated language.

- [ ] **Step 4: Update README**

Add an honesty banner ("Simulated RCT on historical Olist cohorts; effect is synthetic, seed 42 documented") and a reproduce section: `make setup`, place Olist CSVs in `data/raw/olist/`, `make experiment`, `make test`.

- [ ] **Step 5: Run lint and typecheck**

Run: `make lint` and `make typecheck`
Expected: both clean. Fix any mypy strict findings (missing annotations) before commit.

- [ ] **Step 6: Commit**

```bash
git add docs/METRICS.md docs/EXPERIMENT_DESIGN.md README.md
git commit -m "docs: add metrics, experiment design, and reproduce steps"
```

---

## Self-review

**Spec coverage:**
- AOV primary (bootstrap CI + Welch) → Tasks 5, 9, 13. ✓
- Conversion guardrail (two-proportion z) → Tasks 4, 9, 13. ✓
- D7 exploratory (no inference) → Tasks 6, 13. ✓
- Cohort window → Task 7 (`cohort.sql` + constants). ✓
- Person-level assignment, id+seed only → Tasks 2, 7. ✓
- Injected labeled `SIMULATED_EFFECT` after assignment → Task 8, applied in Task 13. ✓
- A/A sanity (raw lift CI spans 0) → covered by `bootstrap_ci_diff_means` on the pre-injection frame; the runner injects after building, so a pre-injection CI is available from `frame`. If an explicit A/A assertion is wanted in the report, add it in Task 13 using `frame` before `apply_simulated_effect`. ✓ (mechanism present)
- Power/MDE → Task 10, surfaced in Task 13. ✓
- Report with disclaimer + recommendation → Task 12. ✓
- Error handling (empty cohort, missing column, imbalance) → `EmptyCohortError` (Task 7), `ImbalanceError` (Task 11). `MissingColumnError` is defined (Task 1); DuckDB raises on a missing column in the SQL, so it surfaces loudly — wrap-and-reraise is optional polish, not required for the gate.
- SQL-first, Python wraps, parity tests → Tasks 4–6. ✓
- Fixtures only, ≤100 rows, in-memory DuckDB → Task 3. ✓
- Clean `src/` layout → file map. ✓

**Placeholder scan:** No TBD/TODO. Every code step shows complete code. Expected numbers are verified against the venv, not invented.

**Type consistency:** `assign_variant`, `build_experiment_frame`, `apply_simulated_effect`, the three `*_by_variant` wrappers, `bootstrap_ci_diff_means`, `welch_ttest`, `two_proportion_ztest`, `mde_proportion`, `mde_mean`, `check_balance`, `run`, `generate_report` are used with the same signatures across tasks and match the contracts block.

**Note on A/A:** The spec lists an A/A sanity check. The plan provides the mechanism (bootstrap CI on the raw `frame` before injection) but does not force a separate report section. If you want it asserted, add one step in Task 13: compute `bootstrap_ci_diff_means` on `frame`'s raw values and assert the CI contains 0, logging the result. Decide at execution time.
