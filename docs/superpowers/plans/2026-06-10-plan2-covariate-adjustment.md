# Plan 2 — Covariate-Adjusted Variance Reduction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add ANCOVA/CUPED-style regression adjustment on `freight_value` to shrink AOV CI width and remove baseline arm-imbalance bias, reported side-by-side with unadjusted numbers.

**Architecture:** Surface per-order `freight_value` through `cohort.sql` into the experiment frame; new pure-numpy `src/experiment/cuped.py` computes θ (pooled, pre-injection) and adjusts Y; `run()` adds an `aov_adjusted` block; reports show both rows; balance guard gains a baseline-metric check. Verdicts (headline + scenarios) switch to the **adjusted** CI; unadjusted stays printed.

**Tech Stack:** Python 3.12, numpy, pandas, DuckDB, pytest, mypy --strict. Spec: `docs/superpowers/specs/2026-06-10-plan2-covariate-adjustment.md`.

**Resolved open decisions:** covariate = `freight_value` (confirm corr ≥ ~0.3 in Task 6; swap only if grossly worse than item count); adjust scenario sweep too; write ADR 0007.

---

### Task 0: Branch

- [ ] **Step 1:** `git checkout dev && git pull --ff-only && git checkout -b feat/plan2-covariate-adjustment`

---

### Task 1: Surface `freight_value` into the experiment frame

**Files:**
- Create: `tests/fixtures/order_items.csv`
- Modify: `sql/experiment/cohort.sql`, `tests/conftest.py`, `tests/test_loader.py:9-19,39-55`, `tests/fixtures/experiment_frame.csv`, `docs/METRICS.md`
- Test: `tests/test_loader.py`

- [ ] **Step 1: Create fixture `tests/fixtures/order_items.csv`.** Match order_ids in `tests/fixtures/orders.csv` (o1..o6 etc. — check actual ids first). Two items for o1 (tests SUM), one for others, and deliberately **omit one order** (tests LEFT JOIN → 0). Example shape (adapt ids to real fixture):

```csv
order_id,order_item_id,product_id,seller_id,price,freight_value
o1,1,p1,s1,50.0,10.0
o1,2,p2,s1,60.0,5.5
o2,1,p3,s2,80.0,12.0
o3,1,p4,s2,40.0,8.0
o4,1,p5,s3,30.0,6.0
o5,1,p6,s3,20.0,4.0
```
(o6 intentionally absent → freight 0.)

- [ ] **Step 2: Write failing tests** in `tests/test_loader.py`:

```python
def test_freight_value_sums_per_order(base_con):
    df = build_experiment_frame(base_con).set_index("order_id")
    assert df.loc["o1", "freight_value"] == pytest.approx(15.5)


def test_freight_value_zero_when_no_items(base_con):
    df = build_experiment_frame(base_con).set_index("order_id")
    assert df.loc["o6", "freight_value"] == pytest.approx(0.0)
```

Also update `test_frame_columns_and_size` expected set to include `"freight_value"`.

- [ ] **Step 3:** Update `tests/conftest.py` `base_con` table list to `["customers", "orders", "order_payments", "order_items"]`, and `test_empty_cohort_raises` to also register `empty_items = pd.DataFrame(columns=["order_id", "order_item_id", "product_id", "seller_id", "price", "freight_value"])`.

- [ ] **Step 4: Run** `.venv/bin/pytest tests/test_loader.py -v` → new tests FAIL (no `freight_value` column).

- [ ] **Step 5: Modify `sql/experiment/cohort.sql`:**

```sql
-- Cohort orders in the stable window, with order_value = SUM(payment_value) per order
-- and freight_value = SUM(order_items.freight_value) per order (0 if no items).
-- Window bounds are passed as parameters ($start, $end) from src.constants.
SELECT
    o.order_id,
    c.customer_unique_id,
    o.order_status,
    p.order_value,
    COALESCE(f.freight_value, 0.0) AS freight_value,
    o.order_purchase_timestamp
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN (
    SELECT order_id, SUM(payment_value) AS order_value
    FROM order_payments
    GROUP BY order_id
) p ON o.order_id = p.order_id
LEFT JOIN (
    SELECT order_id, SUM(freight_value) AS freight_value
    FROM order_items
    GROUP BY order_id
) f ON o.order_id = f.order_id
WHERE o.order_purchase_timestamp >= $start
  AND o.order_purchase_timestamp <  $end
ORDER BY o.order_id;
```

- [ ] **Step 6:** Add a `freight_value` column to `tests/fixtures/experiment_frame.csv` (any positive floats correlated loosely with `order_value`, e.g. ~10% of it).

- [ ] **Step 7: Run** `.venv/bin/pytest tests/ -v` → all PASS.

- [ ] **Step 8:** Add `freight_value` row to the `experiment_frame` schema table in `docs/METRICS.md` ("SUM(order_items.freight_value) per order; 0 when order has no items; pre-treatment covariate for ANCOVA adjustment").

- [ ] **Step 9: Commit** `feat: surface freight_value covariate into experiment frame`

---

### Task 2: `src/experiment/cuped.py`

**Files:**
- Create: `src/experiment/cuped.py`, `tests/test_cuped.py`

- [ ] **Step 1: Write failing tests** `tests/test_cuped.py`:

```python
import numpy as np
import pytest

from src.experiment.cuped import cuped_adjust, cuped_theta


def test_theta_zero_when_uncorrelated():
    rng = np.random.default_rng(42)
    y = rng.normal(100, 10, 5000)
    x = rng.normal(50, 5, 5000)  # independent
    assert abs(cuped_theta(y, x)) < 0.1


def test_theta_recovers_known_slope():
    rng = np.random.default_rng(42)
    x = rng.normal(50, 5, 5000)
    y = 3.0 * x + rng.normal(0, 1, 5000)
    assert cuped_theta(y, x) == pytest.approx(3.0, abs=0.05)


def test_adjust_preserves_mean():
    rng = np.random.default_rng(42)
    x = rng.normal(50, 5, 5000)
    y = 3.0 * x + rng.normal(0, 1, 5000)
    theta = cuped_theta(y, x)
    y_adj = cuped_adjust(y, x, theta, float(x.mean()))
    assert y_adj.mean() == pytest.approx(y.mean(), rel=1e-9)


def test_adjust_reduces_variance():
    rng = np.random.default_rng(42)
    x = rng.normal(50, 5, 5000)
    y = 3.0 * x + rng.normal(0, 1, 5000)
    theta = cuped_theta(y, x)
    y_adj = cuped_adjust(y, x, theta, float(x.mean()))
    assert y_adj.var() < 0.2 * y.var()


def test_theta_zero_variance_x_raises():
    y = np.array([1.0, 2.0, 3.0])
    x = np.array([5.0, 5.0, 5.0])
    with pytest.raises(ValueError):
        cuped_theta(y, x)
```

- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_cuped.py -v` → FAIL (module missing).

- [ ] **Step 3: Implement `src/experiment/cuped.py`:**

```python
"""ANCOVA/CUPED-style covariate adjustment: Y_adj = Y - theta*(X - x_mean).

theta is estimated pooled across arms on PRE-injection data so the synthetic
effect cannot contaminate it (Deng et al. 2013, generalized to any
pre-treatment covariate). See docs/adr/0007-covariate-adjustment-not-cuped.md.
"""

import numpy as np
from numpy.typing import NDArray


def cuped_theta(y: NDArray[np.float64], x: NDArray[np.float64]) -> float:
    """theta = cov(Y, X) / var(X), estimated treatment-independently."""
    var_x = float(np.var(x, ddof=1))
    if var_x == 0.0:
        raise ValueError("covariate has zero variance; cannot estimate theta")
    cov_yx = float(np.cov(y, x, ddof=1)[0, 1])
    return cov_yx / var_x


def cuped_adjust(
    y: NDArray[np.float64],
    x: NDArray[np.float64],
    theta: float,
    x_mean: float,
) -> NDArray[np.float64]:
    """Adjusted outcome with same expected arm difference, lower variance."""
    return np.asarray(y - theta * (x - x_mean), dtype=np.float64)
```

- [ ] **Step 4: Run** `.venv/bin/pytest tests/test_cuped.py -v` → PASS; `.venv/bin/mypy src/ --strict` clean.

- [ ] **Step 5: Commit** `feat: add cuped theta estimation and adjustment functions`

---

### Task 3: Baseline-metric balance guard

**Files:**
- Modify: `src/experiment/balance.py`, `src/constants.py`, `tests/test_balance.py`

- [ ] **Step 1: Add constant** to `src/constants.py`:

```python
BASELINE_BALANCE_TOLERANCE: float = 0.05  # max relative arm-mean gap on pre-injection metric
```

- [ ] **Step 2: Write failing tests** in `tests/test_balance.py`:

```python
import pandas as pd
import pytest

from src.exceptions import ImbalanceError
from src.experiment.balance import check_metric_balance


def _frame(ctrl_vals, treat_vals):
    return pd.DataFrame(
        {
            "variant": ["control"] * len(ctrl_vals) + ["treatment"] * len(treat_vals),
            "order_value": list(ctrl_vals) + list(treat_vals),
        }
    )


def test_metric_balance_passes_small_gap():
    f = _frame([100.0, 102.0], [101.0, 103.0])  # ~1% gap
    check_metric_balance(f, "order_value")  # no raise


def test_metric_balance_raises_large_gap():
    f = _frame([100.0, 100.0], [120.0, 120.0])  # 20% gap
    with pytest.raises(ImbalanceError):
        check_metric_balance(f, "order_value")
```

- [ ] **Step 3: Run** `.venv/bin/pytest tests/test_balance.py -v` → new FAIL.

- [ ] **Step 4: Implement** in `src/experiment/balance.py` (keep existing `check_balance`):

```python
from src.constants import BASELINE_BALANCE_TOLERANCE, IMBALANCE_TOLERANCE


def check_metric_balance(
    frame: pd.DataFrame,
    column: str,
    tolerance: float = BASELINE_BALANCE_TOLERANCE,
) -> float:
    """Guard the PRE-injection metric baseline: relative arm-mean gap must be small.

    Catches the imbalance the null scenario exposed (lift +2.06 at zero effect).
    Returns the gap so run() can report it.
    """
    means = frame.groupby("variant")[column].mean()
    ctrl, treat = float(means["control"]), float(means["treatment"])
    if ctrl == 0.0:
        raise ImbalanceError(f"control mean of {column} is zero")
    gap = abs(treat - ctrl) / abs(ctrl)
    if gap > tolerance:
        raise ImbalanceError(
            f"baseline {column} arm gap {gap:.4f} exceeds tolerance {tolerance} "
            f"(control={ctrl:.2f}, treatment={treat:.2f})"
        )
    return gap
```

- [ ] **Step 5: Run** `.venv/bin/pytest tests/test_balance.py -v` → PASS.

- [ ] **Step 6: Commit** `feat: add pre-injection baseline metric balance guard`

---

### Task 4: Wire adjustment into `run()`

**Files:**
- Modify: `src/experiment/run_experiment.py:30-95`, `tests/test_run_experiment.py`

- [ ] **Step 1: Write failing test** in `tests/test_run_experiment.py` (reuse this file's existing run fixture/pattern — it builds a con from `base_con`-style fixtures; follow whatever existing tests do to call `run`):

```python
def test_run_includes_aov_adjusted_block(...existing fixture...):
    results = run(con)
    adj = results["aov_adjusted"]
    for key in ("control", "treatment", "lift", "ci", "theta", "ci_width_ratio"):
        assert key in adj
    assert results["baseline_balance"]["order_value_gap"] >= 0.0
```

- [ ] **Step 2: Run** → FAIL (KeyError `aov_adjusted`).

- [ ] **Step 3: Implement in `run()`** after `check_balance(frame)` and BEFORE `apply_simulated_effect` compute θ; after injection compute adjusted arrays:

```python
from src.experiment.balance import check_balance, check_metric_balance
from src.experiment.cuped import cuped_adjust, cuped_theta

    # inside run(), after check_balance(frame):
    baseline_gap = check_metric_balance(frame, "order_value")
    y_pre = frame["order_value"].to_numpy(dtype=np.float64)
    x_pre = frame["freight_value"].to_numpy(dtype=np.float64)
    theta = cuped_theta(y_pre, x_pre)  # pooled, pre-injection: untouched by effect
    x_mean = float(x_pre.mean())

    # ... existing injected/aov/ci code unchanged ...

    is_ctrl = injected["variant"] == "control"
    is_treat = injected["variant"] == "treatment"
    y_adj_ctrl = cuped_adjust(
        injected.loc[is_ctrl, "order_value"].to_numpy(dtype=np.float64),
        injected.loc[is_ctrl, "freight_value"].to_numpy(dtype=np.float64),
        theta,
        x_mean,
    )
    y_adj_treat = cuped_adjust(
        injected.loc[is_treat, "order_value"].to_numpy(dtype=np.float64),
        injected.loc[is_treat, "freight_value"].to_numpy(dtype=np.float64),
        theta,
        x_mean,
    )
    ci_adj = bootstrap_ci_diff_means(y_adj_ctrl, y_adj_treat)
    width = ci[1] - ci[0]
    width_adj = ci_adj[1] - ci_adj[0]
```

Add to the returned dict:

```python
        "aov_adjusted": {
            "control": float(y_adj_ctrl.mean()),
            "treatment": float(y_adj_treat.mean()),
            "lift": float(y_adj_treat.mean() - y_adj_ctrl.mean()),
            "ci": ci_adj,
            "theta": theta,
            "ci_width_ratio": width_adj / width if width > 0 else 1.0,
        },
        "baseline_balance": {"order_value_gap": baseline_gap},
```

(`import numpy as np` at top.)

- [ ] **Step 4: Run** `.venv/bin/pytest tests/ -v` → PASS (some run/scenario/report tests may need the new keys — fix forward, never delete assertions). `.venv/bin/mypy src/ --strict` clean.

- [ ] **Step 5: Commit** `feat: add covariate-adjusted aov block to experiment results`

---

### Task 5: Reports — adjusted row, scenarios columns, verdict on adjusted CI

**Files:**
- Modify: `src/report/experiment_report.py`, `src/experiment/scenarios.py:21-23`, `tests/test_report.py`, `tests/test_scenarios.py`

- [ ] **Step 1: Write failing tests** (extend existing report tests' results dicts with an `aov_adjusted` block; follow their fixture style):

```python
def test_report_includes_adjusted_row(...):
    md = generate_report(results)
    assert "AOV (covariate-adjusted)" in md
    assert "variance" in md.lower()  # reduction note

def test_scenarios_report_has_adjusted_columns(...):
    md = generate_scenarios_report(scenarios)
    assert "Adj. lift" in md

def test_verdict_uses_adjusted_ci(...):
    # scenario with unadjusted CI spanning 0 but adjusted CI > 0 → SHIP
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement.** In `generate_report` after the AOV row:

```python
        f"| AOV (covariate-adjusted) | {adj['control']:.2f} | {adj['treatment']:.2f} | "
        f"{adj['lift']:.2f} | ({adj['ci'][0]:.2f}, {adj['ci'][1]:.2f}) | — |",
```

with `adj = results["aov_adjusted"]`, a note after the table:

```python
        "",
        f"Covariate adjustment (ANCOVA on pre-treatment `freight_value`, θ={adj['theta']:.4f}, "
        f"estimated pooled pre-injection): CI width is {adj['ci_width_ratio']:.0%} of the "
        "unadjusted width. Both rows shown for auditability.",
```

and switch `rec = recommend(adj["ci"])` with the Recommendation line saying "based on the **covariate-adjusted** AOV 95% bootstrap CI". In `generate_scenarios_report`, extend header/rows:

```python
        "| Scenario | Injected effect | Lift | 95% CI | Adj. lift | Adj. 95% CI | Verdict |",
        "|---|---|---|---|---|---|---|",
        # row:
        f"| {s['scenario']} | {s['simulated_effect']} | {aov['lift']:.2f} | "
        f"({aov['ci'][0]:.2f}, {aov['ci'][1]:.2f}) | {adj['lift']:.2f} | "
        f"({adj['ci'][0]:.2f}, {adj['ci'][1]:.2f}) | {s['verdict']} |"
```

In `scenarios.py` change verdict to the adjusted CI:

```python
        adj = cast("dict[str, object]", result["aov_adjusted"])
        result["verdict"] = recommend(cast("tuple[float, float]", adj["ci"]))
```

- [ ] **Step 4: Run** `.venv/bin/pytest tests/ -v` → PASS; mypy clean.

- [ ] **Step 5: Commit** `feat: report adjusted aov side-by-side; verdicts use adjusted ci`

---

### Task 6: ADR + design docs + correlation confirmation

**Files:**
- Create: `docs/adr/0007-covariate-adjustment-not-cuped.md`
- Modify: `docs/EXPERIMENT_DESIGN.md`

- [ ] **Step 1: Confirm covariate** (one-off, full data — record number in ADR):

```bash
.venv/bin/python -c "
import duckdb
from pathlib import Path
from src.io.loader import load_olist, build_experiment_frame
con = duckdb.connect(':memory:'); load_olist(con, Path('data/raw/olist'))
f = build_experiment_frame(con)
print('corr(order_value, freight_value) =', f['order_value'].corr(f['freight_value']))
"
```

If corr < 0.2, stop and flag to user before proceeding (covariate too weak).

- [ ] **Step 2: Write ADR 0007** (context: null-scenario +2.06 imbalance; options: classic CUPED — rejected, ~97% one-time customers so no pre-period AOV; ANCOVA on freight_value — chosen, pre-treatment + untouched by injected effect, corr = <measured>; item-count — viable alternative, deferred; consequences: verdicts now from adjusted CI, both reported). Follow format of existing `docs/adr/000*.md`.

- [ ] **Step 3:** Add "Covariate adjustment" section to `docs/EXPERIMENT_DESIGN.md`: formula, θ pooled pre-injection, freight pre-treatment rationale, both-numbers honesty rule.

- [ ] **Step 4: Commit** `docs: adr 0007 covariate adjustment rationale + design doc`

---

### Task 7: Regenerate artifacts + verification

**Files:**
- Modify: `reports/experiment_001.{md,json}`, `reports/experiment_scenarios.{md,json}`, `reports/sample_results.json` (regenerated), `docs/STATUS.md`, `README.md` (test count)

- [ ] **Step 1:** `.venv/bin/python -m src.experiment.run_experiment --scenarios`
- [ ] **Step 2: Determinism:** run again, `git diff reports/` must show changes only vs HEAD, second run no further diff (`git status` stable between run 1 and run 2 — copy outputs aside and `diff` if needed).
- [ ] **Step 3: Verify success criteria from spec:** adjusted CI width ≤ 85% of unadjusted in `experiment_001.json`; null-scenario adjusted lift closer to 0 than unadjusted. If not met, report to user — do NOT tune numbers.
- [ ] **Step 4:** Regenerate sample: check `Makefile`/`test_build_sample.py` for the sample-results command and rerun it.
- [ ] **Step 5:** `make check` (or `.venv/bin/pytest -v && .venv/bin/mypy src/ --strict && pre-commit run --all-files`) → all green. Update README test count if asserted anywhere.
- [ ] **Step 6:** Overwrite `docs/STATUS.md` (Plan 2 done, next = Plan 3 narrative memo).
- [ ] **Step 7: Commit** `feat: regenerate artifacts with covariate-adjusted block` (use `SKIP=gitleaks` if disk-full hook issue persists).
- [ ] **Step 8:** Push branch, open PR → dev: `gh pr create --base dev --title "feat: Plan 2 covariate adjustment (ANCOVA on freight_value)" --body "<summary + success-criteria numbers>"`
