# Phase F — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce the committed JSON result artifacts and the join-consistent labeled data sample that Phases P2 (dashboard) and P3 (regression gate) depend on.

**Architecture:** Add a JSON serializer for the existing `run()` results dict, wire `run_experiment.main()` to emit `reports/experiment_001.json` (full data) alongside the markdown, add a deterministic order-anchored sampler that writes `data/sample/`, generate + commit `reports/sample_results.json` from that sample, and add the `[dashboard]` optional-dep group. No change to metric/inference logic — this phase only adds artifacts and a sampler.

**Tech Stack:** Python 3.12, pandas, DuckDB, numpy, pytest, mypy strict.

**Spec:** `docs/superpowers/specs/2026-06-09-phase2-roadmap-design.md` (Phase F section + Q1/Q2 rows).

**Conventions (carried from Phase 1):**
- Run tools via venv: `.venv/bin/pytest`, `.venv/bin/mypy`.
- Commit with `SKIP=gitleaks` (local disk issue) — never `--no-verify`.
- Absolute imports from `src`. mypy `--strict` applies to `src/` and `scripts/` (not `tests/`, `app/`).
- `seed=42` pinned for any sampling.

---

### Task 1: JSON serializer for results dict

**Files:**
- Create: `src/report/results_io.py`
- Test: `tests/test_results_io.py`

The `run()` results dict nests tuples (e.g. `aov["ci"]`) and may hold numpy floats from scipy/bootstrap. `json.dumps` renders tuples as arrays but raises on `np.floating`/`np.integer`; a `default` handler coerces them.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_results_io.py
import json

import numpy as np

from src.report.results_io import results_to_json, write_results_json


def _sample_results() -> dict:
    return {
        "sample_sizes": {"control": 3, "treatment": 3},
        "aov": {
            "control": 103.33,
            "treatment": np.float64(76.66),
            "lift": -26.67,
            "ci": (np.float64(-40.0), np.float64(-13.0)),
            "p": 0.01,
        },
        "simulated_effect": 0.05,
    }


def test_results_to_json_is_valid_json():
    parsed = json.loads(results_to_json(_sample_results()))
    assert parsed["sample_sizes"]["control"] == 3


def test_tuple_ci_becomes_list_and_numpy_coerced():
    parsed = json.loads(results_to_json(_sample_results()))
    assert parsed["aov"]["ci"] == [-40.0, -13.0]
    assert isinstance(parsed["aov"]["treatment"], float)


def test_write_results_json_roundtrips(tmp_path):
    path = tmp_path / "out.json"
    write_results_json(_sample_results(), path)
    parsed = json.loads(path.read_text())
    assert parsed["aov"]["p"] == 0.01
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_results_io.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.report.results_io'`

- [ ] **Step 3: Write minimal implementation**

```python
# src/report/results_io.py
"""Serialize the experiment results dict to JSON. Tuples -> arrays; numpy -> python scalars."""

import json
from pathlib import Path
from typing import Any

import numpy as np


def _default(o: Any) -> Any:
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.integer):
        return int(o)
    raise TypeError(f"not JSON-serializable: {type(o)!r}")


def results_to_json(results: dict[str, Any]) -> str:
    return json.dumps(results, indent=2, default=_default)


def write_results_json(results: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(results_to_json(results))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_results_io.py -v && .venv/bin/mypy src/report/results_io.py --strict`
Expected: PASS (3 passed); mypy `Success`.

- [ ] **Step 5: Commit**

```bash
git add src/report/results_io.py tests/test_results_io.py
SKIP=gitleaks git commit -m "feat: add json serializer for experiment results dict"
```

---

### Task 2: Emit experiment_001.json from the runner

**Files:**
- Modify: `src/experiment/run_experiment.py`
- Test: `tests/test_run_experiment.py` (add cases)

Split output-writing into a testable `write_outputs()` and parametrize `main()` so the JSON path is configurable. `run(base_con)` already works on the existing `base_con` fixture (cohort.sql joins only orders/customers/order_payments), so we can test JSON emission without new fixtures.

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_run_experiment.py
import json

from src.experiment.run_experiment import run, write_outputs


def test_write_outputs_emits_md_and_json(base_con, tmp_path):
    results = run(base_con)
    report_path = tmp_path / "experiment_001.md"
    json_path = tmp_path / "experiment_001.json"
    write_outputs(results, report_path, json_path)
    assert report_path.exists()
    parsed = json.loads(json_path.read_text())
    # ci tuple serialized as a 2-element list
    assert len(parsed["aov"]["ci"]) == 2
    assert "simulated_effect" in parsed
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_run_experiment.py::test_write_outputs_emits_md_and_json -v`
Expected: FAIL with `ImportError: cannot import name 'write_outputs'`

- [ ] **Step 3: Write minimal implementation**

In `src/experiment/run_experiment.py`, add the import, a `JSON_PATH` constant, a `write_outputs()` function, and rewrite `main()` to use them.

Add near the other imports (after `from src.report.experiment_report import generate_report`):

```python
from src.report.results_io import write_results_json
```

Add beside `REPORT_PATH`:

```python
JSON_PATH = Path("reports/experiment_001.json")
```

Replace the existing `main()` with:

```python
def write_outputs(results: dict[str, object], report_path: Path, json_path: Path) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(generate_report(results))
    write_results_json(results, json_path)


def main(
    raw_dir: Path = RAW_DIR,
    report_path: Path = REPORT_PATH,
    json_path: Path = JSON_PATH,
) -> None:
    con = duckdb.connect(":memory:")
    load_olist(con, raw_dir)
    results = run(con)
    write_outputs(results, report_path, json_path)
    print(f"wrote {report_path} and {json_path}")
```

- [ ] **Step 4: Run test + full suite + mypy**

Run: `.venv/bin/pytest tests/ -q && .venv/bin/mypy src/ --strict`
Expected: all pass; mypy `Success`.

- [ ] **Step 5: Regenerate the real artifact and commit**

```bash
.venv/bin/python -m src.experiment.run_experiment   # writes reports/experiment_001.{md,json}
git add src/experiment/run_experiment.py tests/test_run_experiment.py reports/experiment_001.json reports/experiment_001.md
SKIP=gitleaks git commit -m "feat: emit experiment_001.json alongside markdown report"
```

---

### Task 3: Deterministic, join-consistent data sampler

**Files:**
- Create: `scripts/build_sample.py`
- Test: `tests/test_build_sample.py`

Anchor on a deterministic sample of `orders`, then filter customers/payments/items to only referenced ids so every join in `cohort.sql` stays intact. `load_olist` reads 4 files (`orders`, `order_items`, `order_payments`, `customers`); all four must be written even though `order_items` is unused by the experiment.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_build_sample.py
from pathlib import Path

import pandas as pd

from scripts.build_sample import build_sample

TABLES = ["orders", "order_items", "order_payments", "customers"]


def _make_raw(raw: Path) -> None:
    raw.mkdir(parents=True)
    pd.DataFrame(
        {
            "order_id": [f"o{i}" for i in range(20)],
            "customer_id": [f"c{i}" for i in range(20)],
            "order_status": ["delivered"] * 20,
            "order_purchase_timestamp": ["2017-05-01 10:00:00"] * 20,
        }
    ).to_csv(raw / "olist_orders_dataset.csv", index=False)
    pd.DataFrame(
        {"customer_id": [f"c{i}" for i in range(20)],
         "customer_unique_id": [f"u{i}" for i in range(20)],
         "customer_state": ["SP"] * 20}
    ).to_csv(raw / "olist_customers_dataset.csv", index=False)
    pd.DataFrame(
        {"order_id": [f"o{i}" for i in range(20)],
         "payment_sequential": [1] * 20,
         "payment_type": ["credit_card"] * 20,
         "payment_value": [100.0] * 20}
    ).to_csv(raw / "olist_order_payments_dataset.csv", index=False)
    pd.DataFrame(
        {"order_id": [f"o{i}" for i in range(20)],
         "product_id": [f"p{i}" for i in range(20)],
         "price": [50.0] * 20}
    ).to_csv(raw / "olist_order_items_dataset.csv", index=False)


def test_sample_is_join_consistent(tmp_path):
    raw, out = tmp_path / "raw", tmp_path / "sample"
    _make_raw(raw)
    build_sample(raw, out, n_orders=5, seed=42)
    orders = pd.read_csv(out / "olist_orders_dataset.csv")
    assert len(orders) == 5
    ids = set(orders["order_id"])
    cust_ids = set(orders["customer_id"])
    for tbl, key in [("order_payments", "order_id"), ("order_items", "order_id")]:
        child = pd.read_csv(out / f"olist_{tbl}_dataset.csv")
        assert set(child[key]).issubset(ids)
        assert set(child[key]) == ids  # every sampled order is represented
    customers = pd.read_csv(out / "olist_customers_dataset.csv")
    assert set(customers["customer_id"]) == cust_ids


def test_sample_is_deterministic(tmp_path):
    raw, a, b = tmp_path / "raw", tmp_path / "a", tmp_path / "b"
    _make_raw(raw)
    build_sample(raw, a, n_orders=5, seed=42)
    build_sample(raw, b, n_orders=5, seed=42)
    left = pd.read_csv(a / "olist_orders_dataset.csv")["order_id"].tolist()
    right = pd.read_csv(b / "olist_orders_dataset.csv")["order_id"].tolist()
    assert left == right


def test_all_four_files_written(tmp_path):
    raw, out = tmp_path / "raw", tmp_path / "sample"
    _make_raw(raw)
    build_sample(raw, out, n_orders=5, seed=42)
    for t in TABLES:
        assert (out / f"olist_{t}_dataset.csv").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_build_sample.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts.build_sample'`

- [ ] **Step 3: Write minimal implementation**

```python
# scripts/build_sample.py
"""Build a small, join-consistent, labeled Olist sample for CI/demo.

Anchors on a deterministic sample of orders, then filters dependent tables to the
referenced ids so every join in sql/experiment/cohort.sql stays intact.
Full data: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
"""

import sys
from pathlib import Path

import pandas as pd


def build_sample(raw_dir: Path, out_dir: Path, n_orders: int = 8000, seed: int = 42) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    orders = pd.read_csv(raw_dir / "olist_orders_dataset.csv")
    sample = orders.sample(n=min(n_orders, len(orders)), random_state=seed)
    order_ids = set(sample["order_id"])
    customer_ids = set(sample["customer_id"])

    customers = pd.read_csv(raw_dir / "olist_customers_dataset.csv")
    customers = customers[customers["customer_id"].isin(customer_ids)]

    payments = pd.read_csv(raw_dir / "olist_order_payments_dataset.csv")
    payments = payments[payments["order_id"].isin(order_ids)]

    items = pd.read_csv(raw_dir / "olist_order_items_dataset.csv")
    items = items[items["order_id"].isin(order_ids)]

    sample.to_csv(out_dir / "olist_orders_dataset.csv", index=False)
    customers.to_csv(out_dir / "olist_customers_dataset.csv", index=False)
    payments.to_csv(out_dir / "olist_order_payments_dataset.csv", index=False)
    items.to_csv(out_dir / "olist_order_items_dataset.csv", index=False)


if __name__ == "__main__":
    raw = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw/olist")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/sample")
    build_sample(raw, out)
    print(f"wrote sample to {out}")
```

Create an empty `scripts/__init__.py` so `from scripts.build_sample import ...` resolves (pytest `pythonpath=["."]`):

```bash
touch scripts/__init__.py
```

- [ ] **Step 4: Run test + mypy**

Run: `.venv/bin/pytest tests/test_build_sample.py -v && .venv/bin/mypy scripts/build_sample.py --strict`
Expected: PASS (3 passed); mypy `Success`.

- [ ] **Step 5: Commit**

```bash
git add scripts/build_sample.py scripts/__init__.py tests/test_build_sample.py
SKIP=gitleaks git commit -m "feat: add deterministic join-consistent olist sampler"
```

---

### Task 4: Generate and commit the sample data + sample_results.json

**Files:**
- Create (data): `data/sample/olist_*_dataset.csv` (4 files), `data/sample/README.md`
- Create (artifact): `reports/sample_results.json`
- Modify: `.gitignore` (un-ignore `data/sample/`)

`data/raw/**` is gitignored; add a negation so the sample is tracked. This task runs commands against the real local data (`data/raw/olist/` present, 120MB).

- [ ] **Step 1: Un-ignore the sample directory**

Append to `.gitignore`:

```
# committed labeled sample (see data/sample/README.md)
!data/sample/
!data/sample/**
```

- [ ] **Step 2: Build the sample from real data**

Run: `.venv/bin/python scripts/build_sample.py data/raw/olist data/sample`
Expected: `wrote sample to data/sample`. Confirm size is small:
Run: `du -sh data/sample` → expect well under 5 MB.

- [ ] **Step 3: Generate sample_results.json from the sample**

Run:
```bash
.venv/bin/python -c "from pathlib import Path; from src.experiment.run_experiment import main; main(raw_dir=Path('data/sample'), report_path=Path('reports/_sample_report.md'), json_path=Path('reports/sample_results.json'))"
rm -f reports/_sample_report.md
```
Expected: `reports/sample_results.json` exists and parses. (The throwaway sample markdown is removed — only the JSON snapshot is the P3 contract.)

- [ ] **Step 4: Write the sample label**

```markdown
<!-- data/sample/README.md -->
# Olist sample (CI / demo only)

This is a **deterministic ~N-order sample** of the Olist tables the experiment reads
(orders, order_items, order_payments, customers), produced by `scripts/build_sample.py`
(seed 42). It exists so CI and the hosted dashboard can run without the full dataset.

**This is not the full dataset.** Headline results in `reports/experiment_001.md`/`.json`
come from the full data. Download the full dataset:
https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
```

Replace `N` with the actual order count: `wc -l data/sample/olist_orders_dataset.csv`.

- [ ] **Step 5: Verify nothing huge is staged, then commit**

Run: `git add -A && git status --short && du -sh data/sample`
Confirm only `data/sample/` (small), `reports/sample_results.json`, `.gitignore` are staged — **no `data/raw/` files**.

```bash
SKIP=gitleaks git commit -m "data: add labeled olist sample + sample_results.json snapshot"
```

---

### Task 5: Add the dashboard optional-dependency group

**Files:**
- Modify: `pyproject.toml`

P2 needs Streamlit; declare it now as an optional group so Phase F leaves the project install-ready for the dashboard without bloating the core/dev install.

- [ ] **Step 1: Add the group**

In `pyproject.toml`, under `[project.optional-dependencies]`, after the `dev = [...]` block, add:

```toml
dashboard = [
    "streamlit>=1.40.0",
]
```

- [ ] **Step 2: Verify it resolves**

Run: `.venv/bin/pip install -e ".[dashboard]" >/dev/null && .venv/bin/python -c "import streamlit; print(streamlit.__version__)"`
Expected: prints a version ≥ 1.40.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
SKIP=gitleaks git commit -m "build: add [dashboard] optional-deps group (streamlit)"
```

---

## Definition of done (Phase F)

- `reports/experiment_001.json` committed (full-data results; dashboard input for P2).
- `reports/sample_results.json` committed (sample snapshot; regression input for P3).
- `data/sample/` committed, small (<5 MB), join-consistent, labeled; `data/raw/` still ignored.
- `[dashboard]` optional-dep group present.
- Full suite green, mypy `--strict` clean on `src/` + `scripts/`.
