# Plan 3 — Installment Narrative + PM Decision Memo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reframe the simulated experiment as an installment-expansion test (6x→10x interest-free cap), back it with real Olist installment stats, and ship a PM decision memo whose every number is CI-enforced against committed artifacts.

**Architecture:** New `src/report/installment_motivation.py` + two SQL files produce `reports/installment_motivation.{md,json}` (descriptive stats, deterministic). The memo `reports/experiment_001_readout.md` is hand-written; `tests/test_readout_integrity.py` loads the committed JSONs, formats the key numbers, and asserts each formatted string appears in the memo (drift → red CI). Framing sweep touches README, EXPERIMENT_DESIGN, CONTEXT, scenario/report intro lines, ADR 0008. No changes to assignment, effect, seed, metrics, or inference.

**Tech Stack:** Python 3.12, DuckDB, pandas, pytest (fixtures only), mypy --strict. Spec: `docs/superpowers/specs/2026-06-11-plan3-installment-narrative-design.md`.

**Resolved open decisions (from spec §Open decisions):**
1. Motivation runner = new module `src/report/installment_motivation.py` (single responsibility).
2. Integrity test = artifact-derived substring assertions (load JSON, format with the memo's format strings, assert presence). No HTML markers — simpler, memo stays clean prose, equally drift-proof.
3. Scenarios report intro gets a one-line framing reference; headline report gets one framing line. Simulation disclaimer unchanged.

**Environment:** use `.venv/bin/pytest`, `.venv/bin/mypy`, `.venv/bin/python`. Commit with `SKIP=gitleaks git commit ...` if the gitleaks hook fails on disk (never `--no-verify`).

**Known artifact numbers (verified 2026-06-11, used in memo/tests):** headline (large): unadjusted lift 10.15 CI (7.36, 13.11); adjusted lift 8.63 CI (6.15, 11.15), θ=4.9570, ci_width_ratio 0.8682 → "87%"; verdict SHIP. Null: unadjusted 2.06, adjusted 0.54, adj CI (-1.88, 2.96), NEED MORE DATA. Adverse: adjusted -7.56, adj CI (-9.93, -5.19), DO NOT SHIP. Conversion 0.9700 vs 0.9718, CI (-0.0003, 0.0039). D7 0.0088 vs 0.0084. MDE (AOV) 4.32. n = 49,694 control / 49,398 treatment.

---

### Task 0: Merge spec PR, branch

- [ ] **Step 1:** `gh pr checks 18 --watch` then `gh pr merge 18 --merge --delete-branch` (spec PR → dev).
- [ ] **Step 2:** `git checkout dev && git pull --ff-only && git checkout -b feat/plan3-installment-narrative`

---

### Task 1: Motivation stats — SQL + compute function

**Files:**
- Create: `sql/eda/installments.sql`, `sql/eda/installments_cc.sql`
- Modify: `tests/fixtures/order_payments.csv`
- Create: `tests/test_installment_motivation.py`
- Create: `src/report/installment_motivation.py` (partially — compute function)

- [ ] **Step 1: Replace `tests/fixtures/order_payments.csv`** with (adds `payment_installments`; values chosen so every bucket is hit: o1 max=4 → '4-6', o2/o3/o6 = 1 → '1', o4 = 10 → '7+', o5 = 2 → '2-3'):

```csv
order_id,payment_sequential,payment_type,payment_value,payment_installments
o1,1,credit_card,100.00,4
o1,2,voucher,20.00,1
o2,1,credit_card,50.00,1
o3,1,boleto,30.00,1
o4,1,credit_card,200.00,10
o5,1,credit_card,80.00,2
o6,1,credit_card,60.00,1
```

- [ ] **Step 2: Write failing tests** `tests/test_installment_motivation.py`:

```python
import pytest

from src.report.installment_motivation import compute_motivation_stats


def test_buckets_counts_and_aov(base_con):
    stats = compute_motivation_stats(base_con)
    buckets = {b["bucket"]: b for b in stats["buckets"]}
    assert set(buckets) == {"1", "2-3", "4-6", "7+"}
    assert buckets["1"]["n_orders"] == 3  # o2, o3, o6
    assert buckets["1"]["aov"] == pytest.approx((50 + 30 + 60) / 3)
    assert buckets["2-3"]["n_orders"] == 1  # o5
    assert buckets["4-6"]["n_orders"] == 1  # o1 (max over rows = 4)
    assert buckets["4-6"]["aov"] == pytest.approx(120.0)  # 100 + 20
    assert buckets["7+"]["n_orders"] == 1  # o4


def test_share_multi_installment(base_con):
    stats = compute_motivation_stats(base_con)
    assert stats["share_multi_installment_orders"] == pytest.approx(0.5)  # 3 of 6
    assert stats["n_orders"] == 6


def test_credit_card_value_share(base_con):
    stats = compute_motivation_stats(base_con)
    assert stats["credit_card_value_share"] == pytest.approx(490.0 / 540.0)


def test_stats_are_deterministic(base_con):
    a = compute_motivation_stats(base_con)
    b = compute_motivation_stats(base_con)
    assert a == b
```

- [ ] **Step 3: Run** `.venv/bin/pytest tests/test_installment_motivation.py -v` → FAIL (module missing).

- [ ] **Step 4: Create `sql/eda/installments.sql`:**

```sql
-- Per-order installment buckets over the cohort window: an order's installment level is
-- MAX(payment_installments) across its payment rows; order_value = SUM(payment_value).
-- Descriptive stats only (motivates the installment-expansion hypothesis; NOT an effect estimate).
WITH per_order AS (
    SELECT
        op.order_id,
        SUM(op.payment_value) AS order_value,
        MAX(op.payment_installments) AS max_installments
    FROM order_payments op
    JOIN orders o ON op.order_id = o.order_id
    WHERE o.order_purchase_timestamp >= $start
      AND o.order_purchase_timestamp <  $end
    GROUP BY op.order_id
)
SELECT
    CASE
        WHEN max_installments <= 1 THEN '1'
        WHEN max_installments <= 3 THEN '2-3'
        WHEN max_installments <= 6 THEN '4-6'
        ELSE '7+'
    END AS bucket,
    COUNT(*) AS n_orders,
    AVG(order_value) AS aov
FROM per_order
GROUP BY 1
ORDER BY 1;
```

(`ORDER BY 1` is deterministic: '1' < '2-3' < '4-6' < '7+' lexicographically.)

- [ ] **Step 5: Create `sql/eda/installments_cc.sql`:**

```sql
-- Credit card share of total payment value in the cohort window.
SELECT
    SUM(CASE WHEN op.payment_type = 'credit_card' THEN op.payment_value ELSE 0 END)
        / SUM(op.payment_value) AS credit_card_value_share
FROM order_payments op
JOIN orders o ON op.order_id = o.order_id
WHERE o.order_purchase_timestamp >= $start
  AND o.order_purchase_timestamp <  $end;
```

- [ ] **Step 6: Create `src/report/installment_motivation.py`:**

```python
"""Descriptive installment stats that motivate the installment-expansion framing.

Observational only: shows the affordability mechanism exists in Olist (installment
usage and AOV-by-installment gradient). It does NOT estimate the treatment effect —
that is the simulated experiment's job. See ADR 0008.
"""

from pathlib import Path

import duckdb

from src._sql import load_sql
from src.constants import COHORT_END_EXCLUSIVE, COHORT_START

RAW_DIR = Path("data/raw/olist")
MD_PATH = Path("reports/installment_motivation.md")
JSON_PATH = Path("reports/installment_motivation.json")

_WINDOW = {"start": COHORT_START, "end": COHORT_END_EXCLUSIVE}


def compute_motivation_stats(con: duckdb.DuckDBPyConnection) -> dict[str, object]:
    buckets_df = con.execute(load_sql("eda/installments.sql"), _WINDOW).fetchdf()
    row = con.execute(load_sql("eda/installments_cc.sql"), _WINDOW).fetchone()
    cc_share = float(row[0]) if row is not None else 0.0
    buckets = [
        {
            "bucket": str(r["bucket"]),
            "n_orders": int(r["n_orders"]),
            "aov": float(r["aov"]),
        }
        for r in buckets_df.to_dict("records")
    ]
    n_total = sum(int(b["n_orders"]) for b in buckets)  # type: ignore[call-overload]
    n_single = next((int(b["n_orders"]) for b in buckets if b["bucket"] == "1"), 0)  # type: ignore[call-overload]
    return {
        "cohort_window": [COHORT_START, COHORT_END_EXCLUSIVE],
        "n_orders": n_total,
        "buckets": buckets,
        "share_multi_installment_orders": (n_total - n_single) / n_total,
        "credit_card_value_share": cc_share,
    }
```

(If the `# type: ignore` comments are unnecessary under mypy --strict, remove them; if mypy complains differently, type `buckets` as `list[dict[str, object]]` and extract `n_orders` via an intermediate typed variable. The result must be mypy-strict clean WITHOUT loosening function signatures.)

- [ ] **Step 7: Run** `.venv/bin/pytest tests/test_installment_motivation.py -v` → 4 PASS. `.venv/bin/mypy src/ --strict` → clean. Run full `.venv/bin/pytest tests/ -q` — the fixture gained a column; existing loader/metric tests must still pass (they don't read `payment_installments`).

- [ ] **Step 8: Commit** `git add -A && SKIP=gitleaks git commit -m "feat: installment motivation stats (sql + compute)"`

---

### Task 2: Motivation writers + main + Makefile

**Files:**
- Modify: `src/report/installment_motivation.py` (add md/json writers + main)
- Modify: `tests/test_installment_motivation.py`, `Makefile`

- [ ] **Step 1: Add failing tests** to `tests/test_installment_motivation.py`:

```python
import json
import shutil
from pathlib import Path


def test_generate_md_contains_table_and_disclaimer(base_con):
    from src.report.installment_motivation import (
        compute_motivation_stats,
        generate_motivation_md,
    )

    md = generate_motivation_md(compute_motivation_stats(base_con))
    assert "| Installments | Orders | AOV |" in md
    assert "descriptive" in md.lower()
    assert "not an effect estimate" in md.lower()


def test_main_end_to_end_writes_artifacts(tmp_path):
    from src.report.installment_motivation import main

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    fixtures = Path(__file__).parent / "fixtures"
    for name in ["customers", "orders", "order_payments", "order_items"]:
        shutil.copy(fixtures / f"{name}.csv", raw_dir / f"olist_{name}_dataset.csv")
    md_path = tmp_path / "installment_motivation.md"
    json_path = tmp_path / "installment_motivation.json"
    main(raw_dir=raw_dir, md_path=md_path, json_path=json_path)
    parsed = json.loads(json_path.read_text())
    assert parsed["share_multi_installment_orders"] == pytest.approx(0.5)
    assert "| Installments | Orders | AOV |" in md_path.read_text()
```

- [ ] **Step 2: Run** → FAIL (functions missing).

- [ ] **Step 3: Append to `src/report/installment_motivation.py`:**

```python
from typing import Any

from src.io.loader import load_olist
from src.report.results_io import results_to_json


def generate_motivation_md(stats: dict[str, Any]) -> str:
    lines = [
        "# Installment Usage — Motivation Stats (Descriptive)",
        "",
        "> **Descriptive / observational.** These numbers show the affordability mechanism",
        "> exists in Olist (installment usage is common and AOV rises with installment count).",
        "> They are **not an effect estimate** — the simulated experiment estimates the effect.",
        "",
        f"Cohort window: {stats['cohort_window'][0]} → {stats['cohort_window'][1]} "
        f"({stats['n_orders']} orders).",
        "",
        "| Installments | Orders | AOV |",
        "|---|---|---|",
    ]
    for b in stats["buckets"]:
        lines.append(f"| {b['bucket']} | {b['n_orders']} | {b['aov']:.2f} |")
    lines += [
        "",
        f"- Orders paid in >1 installment: **{stats['share_multi_installment_orders']:.1%}**",
        f"- Credit card share of payment value: **{stats['credit_card_value_share']:.1%}**",
        "",
    ]
    return "\n".join(lines)


def write_motivation_outputs(
    stats: dict[str, Any], md_path: Path, json_path: Path
) -> None:
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(generate_motivation_md(stats))
    json_path.write_text(results_to_json(stats) + "\n")


def main(
    raw_dir: Path = RAW_DIR,
    md_path: Path = MD_PATH,
    json_path: Path = JSON_PATH,
) -> None:
    con = duckdb.connect(":memory:")
    load_olist(con, raw_dir)
    write_motivation_outputs(compute_motivation_stats(con), md_path, json_path)
    print(f"wrote {md_path} and {json_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Add Makefile target** (after the `scenarios:` target, matching its style):

```make
motivation:
	python -m src.report.installment_motivation
```

Also add `motivation` to the `.PHONY` line.

- [ ] **Step 5: Run** `.venv/bin/pytest tests/ -q` → all pass; `.venv/bin/mypy src/ --strict` → clean.

- [ ] **Step 6: Commit** `git add -A && SKIP=gitleaks git commit -m "feat: installment motivation md/json writers + make motivation"`

---

### Task 3: Generate real motivation artifacts + determinism

- [ ] **Step 1:** `.venv/bin/python -m src.report.installment_motivation` → writes `reports/installment_motivation.{md,json}`.
- [ ] **Step 2: Determinism:** `cp reports/installment_motivation.json /tmp/m.json && cp reports/installment_motivation.md /tmp/m.md`, rerun the command, then `diff /tmp/m.json reports/installment_motivation.json && diff /tmp/m.md reports/installment_motivation.md` → no output (identical).
- [ ] **Step 3: Record the real numbers** (needed for Task 4's memo): `.venv/bin/python -c "import json; m=json.load(open('reports/installment_motivation.json')); print(f\"{m['share_multi_installment_orders']:.1%}\", f\"{m['credit_card_value_share']:.1%}\", m['n_orders']); [print(b['bucket'], b['n_orders'], f\"{b['aov']:.2f}\") for b in m['buckets']]"` — expect share ≈ 49–51%, cc share ≈ 73–80% (full-data, cohort-windowed; exact values may differ from the spec's full-table 49.4%/73.9%).
- [ ] **Step 4: Commit** `git add reports/installment_motivation.* && SKIP=gitleaks git commit -m "feat: commit installment motivation artifacts"`

---

### Task 4: PM decision memo + integrity test

**Files:**
- Create: `reports/experiment_001_readout.md`
- Create: `tests/test_readout_integrity.py`

- [ ] **Step 1: Write failing integrity test** `tests/test_readout_integrity.py`:

```python
"""Enforce rule 1 (no invented metrics) on the PM memo: every headline number quoted in
reports/experiment_001_readout.md must match the committed JSON artifacts, using the
same format strings the memo uses."""

import json
from pathlib import Path

MEMO_PATH = Path("reports/experiment_001_readout.md")
EXPERIMENT_JSON = Path("reports/experiment_001.json")
SCENARIOS_JSON = Path("reports/experiment_scenarios.json")
MOTIVATION_JSON = Path("reports/installment_motivation.json")


def _memo() -> str:
    return MEMO_PATH.read_text()


def test_headline_numbers_match_experiment_json():
    e = json.loads(EXPERIMENT_JSON.read_text())
    adj = e["aov_adjusted"]
    memo = _memo()
    assert f"{adj['lift']:.2f}" in memo
    assert f"({adj['ci'][0]:.2f}, {adj['ci'][1]:.2f})" in memo
    assert f"{e['aov']['lift']:.2f}" in memo
    assert f"({e['aov']['ci'][0]:.2f}, {e['aov']['ci'][1]:.2f})" in memo
    assert f"{adj['ci_width_ratio']:.0%}" in memo
    assert f"{e['sample_sizes']['control']:,}" in memo
    assert f"{e['sample_sizes']['treatment']:,}" in memo
    assert f"{e['mde']['aov']:.2f}" in memo


def test_guardrail_numbers_match_experiment_json():
    e = json.loads(EXPERIMENT_JSON.read_text())
    memo = _memo()
    assert f"{e['conversion']['control']:.4f}" in memo
    assert f"{e['conversion']['treatment']:.4f}" in memo


def test_scenario_numbers_and_verdicts_match_scenarios_json():
    scenarios = {s["scenario"]: s for s in json.loads(SCENARIOS_JSON.read_text())}
    memo = _memo()
    null = scenarios["null"]
    assert f"{null['aov']['lift']:.2f}" in memo
    assert f"{null['aov_adjusted']['lift']:.2f}" in memo
    for s in scenarios.values():
        assert str(s["verdict"]) in memo


def test_motivation_numbers_match_motivation_json():
    m = json.loads(MOTIVATION_JSON.read_text())
    memo = _memo()
    assert f"{m['share_multi_installment_orders']:.1%}" in memo
    assert f"{m['credit_card_value_share']:.1%}" in memo


def test_simulation_disclaimer_prominent():
    memo = _memo()
    assert "simulated" in memo[:600].lower()  # top
    assert memo.lower().count("simulated") >= 2  # top and bottom
```

- [ ] **Step 2: Run** `.venv/bin/pytest tests/test_readout_integrity.py -v` → FAIL (memo missing).

- [ ] **Step 3: Write `reports/experiment_001_readout.md`.** Use this exact text; replace ONLY the three `«...»` tokens with the values printed in Task 3 Step 3 (using those exact format strings — the integrity test re-derives them):

```markdown
# Experiment 001 Readout — Installment-Expansion Test

> **Simulated experiment.** Olist has no native A/B test. Variants are assigned by hashed
> `customer_unique_id` (seed 42) on historical data; the treatment effect is a labeled synthetic
> injection. This memo demonstrates experiment methodology and decision writing — not a real lift.

## TL;DR

**SHIP** (in the headline scenario). Raising the interest-free installment cap from 6x to 10x
lifted AOV by **8.63 BRL** (covariate-adjusted 95% CI **(6.15, 11.15)**, excludes zero) with no
detectable damage to the delivered-rate guardrail. Recommendation: roll out, with the
post-launch monitoring plan below — the guardrail, not the lift, carries the real risk.

## Context & motivation (real Olist numbers)

Brazilian e-commerce is installment-driven. In our cohort window:

- **«share_multi»** of orders are paid in more than one installment.
- Credit cards carry **«cc_share»** of payment value.
- AOV rises steeply with installment count (see `reports/installment_motivation.md` — orders
  paid in 7+ installments average several times the basket of single-payment orders).

These are **descriptive** numbers: they show the affordability mechanism exists, not what the
cap change causes. Estimating the causal effect is the experiment's job.

## Hypothesis & change

Checkout today caps interest-free installments at **6x**. Treatment raises the cap to **10x**.
The binding constraint on basket size is the *monthly* payment, not the sticker price; lowering
per-month cost lets customers build bigger baskets.

- **Primary:** AOV ↑ (order_value per order).
- **Guardrail:** delivered-rate — more credit stretched over a longer horizon means more payment
  failures and cancellations, which surface as non-delivered orders.
- **Exploratory:** D7 repeat purchase (Olist is ~97% one-time buyers, so this can only be
  directional).

## Design

- **Randomization:** by `customer_unique_id` hash (seed 42) — a customer must always see the
  same cap, so customer-level assignment is the only correct unit. n = **49,694** control /
  **49,398** treatment.
- **Cohort:** orders 2017-01 → 2018-08 (stable-volume window; pre-registered in
  `docs/EXPERIMENT_DESIGN.md`).
- **Inference:** BCa bootstrap CI on the AOV difference, plus ANCOVA adjustment on pre-treatment
  `freight_value` (a basket-size proxy, estimated pooled pre-injection). Adjustment removes
  baseline arm imbalance and shrinks the CI to **87%** of its unadjusted width.
- **Power:** MDE on AOV ≈ **4.32** BRL at α=0.05 — the observed lift clears it.

## Results

| Metric | Control | Treatment | Lift | 95% CI | Read |
|---|---|---|---|---|---|
| AOV (unadjusted) | — | — | 10.15 | (7.36, 13.11) | biased up by baseline imbalance |
| **AOV (covariate-adjusted)** | — | — | **8.63** | **(6.15, 11.15)** | **decision basis** |
| Delivered-rate (guardrail) | 0.9700 | 0.9718 | +0.0018 | (-0.0003, 0.0039) | no detectable harm |

Why two AOV rows: random assignment happened to put slightly higher-value customers in
treatment. The null scenario (zero injected effect) still shows a **2.06** raw "lift"; after
adjustment it shrinks to **0.54**. Reporting both rows keeps the bias visible and auditable.

### Decision-rule stress test (scenario sweep)

The same pipeline was run with a harmful, zero, and large injected effect — the decision rule
must produce all three verdicts, not just SHIP:

| Scenario | Meaning | Verdict |
|---|---|---|
| adverse | the offer backfires (cancellations, remorse) | DO NOT SHIP |
| null | the cap change does nothing | NEED MORE DATA |
| large | affordability mechanism works | SHIP |

## Caveats (read before acting)

1. **This is a simulated experiment** — the lift is injected; the methodology is the product.
2. CI-width reduction from adjustment was 13% (87% ratio) vs a ≥15% target — disclosed, not
   tuned (ADR 0007).
3. ~97% one-time buyers: repeat-purchase effects are out of reach for this dataset.
4. Delivered-rate is a proxy guardrail; a real rollout would track payment-failure and
   chargeback rates directly.

## Recommendation & monitoring plan

Roll out to 100% **with a kill switch**, monitoring weekly:

- Delivered-rate by installment bucket (1 / 2-3 / 4-6 / 7+): a drop concentrated in 7+ is the
  credit-risk signature; **rollback trigger: guardrail CI excludes zero on the downside.**
- Basket-mix shift: AOV lift should come from bigger baskets, not from fewer small orders.
- Payment-failure proxy (orders canceled before shipment) by arm during any holdback period.
```

- [ ] **Step 4: Run** `.venv/bin/pytest tests/test_readout_integrity.py -v` → 5 PASS. (If a substring assertion fails, the memo number is wrong — fix the MEMO to match the artifact, never the test.)
- [ ] **Step 5: Commit** `git add reports/experiment_001_readout.md tests/test_readout_integrity.py && SKIP=gitleaks git commit -m "feat: pm decision memo + memo-artifact integrity tests"`

---

### Task 5: Framing sweep — report lines, README, design docs, ADR 0008

**Files:**
- Modify: `src/report/experiment_report.py`, `tests/test_report.py`
- Modify: `README.md`, `docs/EXPERIMENT_DESIGN.md`, `CONTEXT.md`, `docs/adr/README.md`
- Create: `docs/adr/0008-installment-framing-over-free-shipping.md`
- Regenerate: `reports/experiment_001.md`, `reports/experiment_scenarios.md` (+ json, sample)

- [ ] **Step 1: Write failing tests** in `tests/test_report.py` (style: extend existing results-dict fixtures):

```python
def test_report_mentions_installment_framing():
    # use the same results dict as test_report_includes_adjusted_row
    md = generate_report(results)
    assert "installment-expansion test" in md
    assert "experiment_001_readout.md" in md


def test_scenarios_report_mentions_installment_framing():
    # use the same scenarios list as test_scenarios_report_has_adjusted_columns
    md = generate_scenarios_report(scenarios)
    assert "installment-expansion test" in md
```

- [ ] **Step 2: Run** → FAIL.

- [ ] **Step 3: Implement in `src/report/experiment_report.py`.** In `generate_report`, directly after the `DISCLAIMER` line append:

```python
        "",
        "Framing: installment-expansion test (6x → 10x interest-free cap) — full decision "
        "memo in `reports/experiment_001_readout.md`.",
```

In `generate_scenarios_report`, append to the intro paragraph list (after the existing
"...the pipeline handles the hard cases." line):

```python
        "Framing: installment-expansion test (6x → 10x interest-free cap).",
```

- [ ] **Step 4: Run** `.venv/bin/pytest tests/ -q` → all pass; mypy clean.

- [ ] **Step 5: README.** Under `## Results — Experiment 001 (simulated)` (line ~38), insert at the top of the section:

```markdown
**Framing:** installment-expansion test — would raising the interest-free installment cap
(6x → 10x) grow basket sizes? Motivated by real Olist payment behavior
([motivation stats](reports/installment_motivation.md)); effect itself is simulated and labeled.
**→ Read the [PM decision memo](reports/experiment_001_readout.md)** — the headline artifact:
verdict, guardrail readout, caveats, rollout + monitoring plan.
```

Keep all existing tables/numbers in the section unchanged.

- [ ] **Step 6: `docs/EXPERIMENT_DESIGN.md`.** Insert a new section between the header intro and `## Cohort`:

```markdown
## Business framing (Plan 3): installment-expansion test

The simulated change: checkout caps interest-free installments at 6x; treatment raises the cap
to 10x. Mechanism: in Brazilian e-commerce the binding constraint is the monthly payment —
lowering per-month cost lets customers build bigger baskets (AOV ↑, primary). Risk: more credit
over a longer horizon → payment failures/cancellations surface as non-delivered orders
(delivered-rate, guardrail). Customer-level hash assignment matches how a cap change would
actually roll out (same customer always sees the same cap). Motivation stats (descriptive,
real data): `reports/installment_motivation.md`. Decision memo:
`reports/experiment_001_readout.md`. Rationale and rejected framings: ADR 0008.
```

- [ ] **Step 7: `CONTEXT.md` §2 Locked decisions** — append one bullet:

```markdown
- **Business framing (Plan 3):** installment-expansion test (6x→10x interest-free cap).
  Free-shipping framing rejected for portfolio separation from supply-chain-ml (ADR 0008).
```

- [ ] **Step 8: Write `docs/adr/0008-installment-framing-over-free-shipping.md`** (follow 0007's format):

```markdown
# 0008 — Installment-expansion framing over free-shipping threshold

**Status:** accepted (2026-06-11)

## Context

The pipeline was statistically credible but had no product story: a generic "simulated AOV
lift" with no hypothesis a PM would recognize. Plan 3 adds the narrative layer (decision memo).
That requires picking the fictional product change the experiment simulates. The earlier
default — a free-shipping-threshold change — was questioned by the user: it overlaps the
freight/logistics domain owned by the sibling `supply-chain-optimization-ml` project.

## Options

1. **Free-shipping threshold change** — fits AOV mechanics and the freight covariate, but
   collides with the supply-chain project's domain; portfolio reads as two freight projects.
2. **Installment-expansion test (chosen)** — raise the interest-free installment cap 6x→10x.
   Dataset-native: `order_payments.payment_installments` is real; measured in the cohort
   window, ~half of orders use >1 installment and credit cards carry ~3/4 of payment value
   (exact committed numbers: `reports/installment_motivation.json`). The delivered-rate
   guardrail becomes load-bearing (credit risk → cancellations). Customer-level assignment
   matches an offer rollout. Zero overlap with any sibling repo.
3. **Cross-sell bundle module** — recsys-adjacent; collides with the stock-recommender's
   "recommendation" identity.
4. **Tiered minimum-spend coupon** — discount confounds revenue vs AOV; weakens the guardrail
   logic.

## Decision

Option 2. The injected effect, assignment, seed, cohort, metrics, and inference are unchanged —
the framing is narrative + docs + one descriptive artifact. Portfolio separation is recorded on
both sides (supply-chain repo: `docs/FUTURE_ENHANCEMENTS.md` bans causal/uplift work there;
this repo stays out of freight/logistics).

## Consequences

- `freight_value` remains the ANCOVA covariate but is a statistical detail, not the story.
- The memo (`reports/experiment_001_readout.md`) quotes only committed-artifact numbers,
  enforced by `tests/test_readout_integrity.py`.
- Motivation stats are descriptive and must never be presented as effect estimates.
- D7 repeat stays exploratory (~3% ever-repeat).
```

- [ ] **Step 9: Add ADR index row** in `docs/adr/README.md` after the 0007 row:

```markdown
| [0008](0008-installment-framing-over-free-shipping.md) | Installment-expansion framing over free-shipping | accepted |
```

- [ ] **Step 10: Regenerate artifacts** (report code changed): `.venv/bin/python -m src.experiment.run_experiment --scenarios` then regenerate the sample exactly as `tests/test_build_sample.py`/Makefile does (Plan 2 used `main(raw_dir=Path('data/sample'), json_path=Path('reports/sample_results.json'))` — check and rerun the same way). Determinism: run twice, `git status` stable between runs.
- [ ] **Step 11: Run** `.venv/bin/pytest tests/ -q` → all pass (integrity tests still green — the framing lines didn't change any numbers). `.venv/bin/mypy src/ --strict` clean.
- [ ] **Step 12: Commit** `git add -A && SKIP=gitleaks git commit -m "docs: installment framing sweep + adr 0008; regenerate reports"`

---

### Task 6: Gates, STATUS, PR

- [ ] **Step 1: Full gate:** `.venv/bin/pytest tests/ --cov=src --cov-report=term -q` → all pass, coverage ≥ 90% (new module is fully tested; if below, the uncovered lines will be in `installment_motivation.py` `main`/`__main__` — `test_main_end_to_end_writes_artifacts` covers `main`, so only the `__main__` guard may be uncovered, which is fine). `.venv/bin/mypy src/ --strict` clean. `pre-commit run --all-files` (gitleaks may fail on disk → note it; CI covers it).
- [ ] **Step 2: README badges** — update test count badge to the actual new total from Step 1 output.
- [ ] **Step 3: Overwrite `docs/STATUS.md`** (keep header style + Caveats section as-is, ~40 lines): Plan 3 done on `feat/plan3-installment-narrative` (framing locked = installments, memo + integrity tests + motivation artifacts shipped, ADR 0008); next = merge PR → dev → main, then Plan 4 (DiD natural experiment, own spec) and earlier roadmap (P2 dashboard, P3 repro CI gate).
- [ ] **Step 4: Commit** `git add -A && SKIP=gitleaks git commit -m "docs: status sync — plan 3 complete"`
- [ ] **Step 5: Push + PR:** `git push -u origin feat/plan3-installment-narrative` then `gh pr create --base dev --title "feat: Plan 3 installment narrative + PM decision memo" --body-file <body>` where the body summarizes: framing locked (ADR 0008), motivation artifacts (real numbers), memo, integrity tests, framing sweep; test count + coverage; determinism verified.
```
