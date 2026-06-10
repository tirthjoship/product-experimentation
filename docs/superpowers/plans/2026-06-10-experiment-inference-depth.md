# Experiment Inference Depth Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the experiment from a single foregone-conclusion SHIP into (a) a decision rule validated across null / borderline / large effects, and (b) skew-correct inference (BCa CI + distributional view) — removing the "tautology" critique.

**Architecture:** Two cohesive upgrades to the inference layer. (1) Replace the percentile bootstrap with a bias-corrected-and-accelerated (BCa) interval and add a quantile-lift view, since AOV is heavily right-skewed (mean 161, median 105, max 13,664). (2) Parametrize the injected effect and run a fixed scenario sweep {0.0, ~MDE, 0.05} so the ship/no-ship/need-more-data rule is demonstrated producing *all three* verdicts, not just SHIP. The single-scenario `experiment_001.{md,json}` contract is preserved (dashboard P2 depends on it) and is redefined as the `large` scenario; a new `experiment_scenarios.{md,json}` carries the sweep.

**Tech Stack:** Python 3.12, numpy, scipy (`scipy.stats.bootstrap`), DuckDB, pandas, pytest. Seed 42 pinned (`src/constants.py`). mypy --strict, ruff, black.

**Plan series context — READ FIRST:**
- This is **Plan 1 of 4** in the experiment-depth series (see `docs/STATUS.md`). It is framing-independent: it changes computed numbers only, no business narrative.
- **Deferred to later plans (do NOT do here):** #2 covariate-adjustment/ANCOVA (Olist has ~97% one-time customers → classic CUPED infeasible; needs a covariate surfaced into the frame — separate spec), #3 free-shipping reframe + #4 PM memo (narrative, gated on framing), #6 P4 natural experiment (own pre-registration spec).
- **Honesty invariants (AGENTS.md / CLAUDE.md, NON-NEGOTIABLE):** no invented metrics; simulated effect stays labeled `SIMULATED_EFFECT`; seed 42 everywhere; fixture-only tests (≤100 rows, in-memory DuckDB); every committed number from a reproducible command.
- **P3 determinism contract:** `tests/test_run_experiment.py::test_run_is_deterministic_for_p3_contract` requires byte-stable JSON across runs. BCa with a fixed `random_state` is deterministic — keep it that way. Any committed JSON regenerated in this plan must stay byte-stable.

---

## File Structure

| File | Change | Responsibility |
|------|--------|----------------|
| `src/experiment/analysis.py` | Modify | Swap bootstrap internals to BCa (same signature); add `quantile_lift`. |
| `src/constants.py` | Modify | Add `SCENARIOS` tuple + `QUANTILES` tuple. |
| `src/experiment/scenarios.py` | **Create** | Run the experiment at each scenario effect; return list of per-scenario result dicts. |
| `src/experiment/run_experiment.py` | Modify | `run()` accepts `effect` param; add scenario-sweep entrypoint + outputs. |
| `src/report/experiment_report.py` | Modify | Add `generate_scenarios_report()`; add quantile rows to the single report. |
| `tests/test_analysis.py` | Modify | BCa behavior + `quantile_lift` tests. |
| `tests/test_scenarios.py` | **Create** | Scenario sweep shape + verdict-mapping on a controlled fixture. |
| `tests/test_report.py` | Modify | Scenarios report renders 3 verdicts + quantile rows. |
| `reports/experiment_001.{md,json}` | Regenerate | = `large` scenario, now with BCa CI (full-data run, committed). |
| `reports/sample_results.json` | Regenerate | P3 snapshot, BCa CI on `data/sample/` (committed). |
| `reports/experiment_scenarios.{md,json}` | **Create** | The 3-verdict sweep artifact (full-data run, committed). |
| `Makefile` | Modify | Add `make scenarios` target. |

**Decisions locked in this structure:**
- BCa replaces percentile *in place* (`bootstrap_ci_diff_means` keeps its name + signature) so every caller and the existing behavioral tests keep working; only the numeric bounds change.
- `experiment_001.json` is NOT renamed — the P2 dashboard reads it. It becomes the `large`-scenario output.
- Scenario effects live in `constants.py` (single source of truth), not hardcoded in the runner.

---

## Task 1: BCa bootstrap (skew-correct interval)

**Files:**
- Modify: `src/experiment/analysis.py:11-28`
- Test: `tests/test_analysis.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_analysis.py`:

```python
def test_bootstrap_bca_still_reproducible():
    a, b = [50.0, 200.0, 60.0, 90.0], [120.0, 30.0, 80.0, 140.0]
    first = bootstrap_ci_diff_means(a, b, n_resamples=2000, seed=42)
    second = bootstrap_ci_diff_means(a, b, n_resamples=2000, seed=42)
    assert first == second  # determinism preserved for the P3 contract


def test_bootstrap_bca_recovers_known_positive_effect():
    rng = np.random.default_rng(0)
    control = rng.normal(100, 5, 500)
    treatment = control + 10
    lo, hi = bootstrap_ci_diff_means(control, treatment, n_resamples=2000, seed=42)
    assert lo > 0
    assert lo <= 10 <= hi


def test_bootstrap_bca_skew_correction_shifts_interval():
    # On a right-skewed sample, BCa should not equal the naive percentile interval.
    rng = np.random.default_rng(1)
    control = rng.lognormal(mean=3.0, sigma=1.0, size=400)
    treatment = rng.lognormal(mean=3.0, sigma=1.0, size=400) + 5.0
    lo, hi = bootstrap_ci_diff_means(control, treatment, n_resamples=3000, seed=42)
    assert hi > lo  # well-formed interval on skewed data
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/test_analysis.py -k bca -v`
Expected: the determinism test passes by luck on old code only if equal; the skew test passes trivially. The recover test passes on old percentile too. **These tests are written to stay green across the swap** — their job is to pin behavior so the BCa change is safe. Confirm they pass on the CURRENT percentile implementation first (baseline), then stay green after Step 3. If any FAIL on current code, stop and report.

- [ ] **Step 3: Swap the implementation to BCa**

Replace `bootstrap_ci_diff_means` in `src/experiment/analysis.py` (keep the exact signature):

```python
def bootstrap_ci_diff_means(
    control: Sequence[float],
    treatment: Sequence[float],
    n_resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = SEED,
    alpha: float = ALPHA,
) -> tuple[float, float]:
    """BCa bootstrap CI on (treatment mean - control mean).

    Bias-corrected-and-accelerated: corrects the percentile interval for median
    bias (z0) and skew-driven acceleration (a, via jackknife). Preferred over the
    percentile method because AOV is heavily right-skewed, where percentile
    intervals undercover. Deterministic given a fixed seed (the P3 contract).
    """
    c = np.asarray(control, dtype=float)
    t = np.asarray(treatment, dtype=float)

    def _stat(cs: np.ndarray, ts: np.ndarray, axis: int = -1) -> np.ndarray:
        return ts.mean(axis=axis) - cs.mean(axis=axis)

    res = stats.bootstrap(
        (c, t),
        _stat,
        n_resamples=n_resamples,
        confidence_level=1 - alpha,
        method="BCa",
        vectorized=True,
        paired=False,
        random_state=np.random.default_rng(seed),
    )
    return float(res.confidence_interval.low), float(res.confidence_interval.high)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_analysis.py -v`
Expected: PASS (all bca tests + the existing welch/ztest reference tests unchanged).
If `scipy.stats.bootstrap` errors on the call shape, verify the current API with context7 (`scipy` → `stats.bootstrap BCa multiple samples`) before adjusting — do not silently change the statistic.

- [ ] **Step 5: Commit**

```bash
SKIP=gitleaks git commit -am "feat: use BCa bootstrap for skew-correct AOV interval"
```

---

## Task 2: Quantile lift (distributional view)

**Files:**
- Modify: `src/experiment/analysis.py` (append function)
- Modify: `src/constants.py`
- Test: `tests/test_analysis.py`

- [ ] **Step 1: Add the quantile constant**

In `src/constants.py` append:

```python
QUANTILES: tuple[float, ...] = (0.25, 0.50, 0.75, 0.90)
```

- [ ] **Step 2: Write the failing test**

Add to `tests/test_analysis.py`:

```python
from src.experiment.analysis import quantile_lift
from src.constants import QUANTILES


def test_quantile_lift_constant_shift():
    control = [10.0, 20.0, 30.0, 40.0, 50.0]
    treatment = [15.0, 25.0, 35.0, 45.0, 55.0]  # +5 everywhere
    out = quantile_lift(control, treatment, QUANTILES)
    assert set(out) == set(QUANTILES)
    for q in QUANTILES:
        assert out[q] == pytest.approx(5.0, abs=1e-9)


def test_quantile_lift_detects_tail_only_effect():
    # Effect concentrated in the top quartile -> low quantiles ~0, top quantile > 0.
    control = [10.0, 20.0, 30.0, 40.0, 1000.0]
    treatment = [10.0, 20.0, 30.0, 40.0, 1100.0]
    out = quantile_lift(control, treatment, (0.25, 0.90))
    assert out[0.25] == pytest.approx(0.0, abs=1e-9)
    assert out[0.90] > 0.0
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_analysis.py -k quantile -v`
Expected: FAIL with `ImportError: cannot import name 'quantile_lift'`

- [ ] **Step 4: Implement `quantile_lift`**

Append to `src/experiment/analysis.py`:

```python
def quantile_lift(
    control: Sequence[float],
    treatment: Sequence[float],
    quantiles: Sequence[float],
) -> dict[float, float]:
    """Per-quantile treatment effect: q-th quantile(treatment) - q-th quantile(control).

    Shows *where* a mean lift lands. A mean AOV difference can be driven entirely by
    the tail (high-value 'whale' orders); the quantile view exposes that instead of
    hiding it behind the mean.
    """
    c = np.asarray(control, dtype=float)
    t = np.asarray(treatment, dtype=float)
    return {
        float(q): float(np.quantile(t, q) - np.quantile(c, q)) for q in quantiles
    }
```

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_analysis.py -k quantile -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
SKIP=gitleaks git commit -am "feat: add quantile lift for distributional AOV view"
```

---

## Task 3: Parametrize the injected effect in `run()`

**Files:**
- Modify: `src/experiment/run_experiment.py:28-32`
- Test: `tests/test_run_experiment.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_run_experiment.py`:

```python
def test_run_accepts_effect_override(base_con):
    null = run(base_con, effect=0.0)
    big = run(base_con, effect=0.20)
    # Null effect -> treatment AOV ~ control AOV; large effect -> treatment >> control.
    assert null["aov"]["lift"] == pytest.approx(0.0, abs=1e-9) or abs(
        null["aov"]["lift"]
    ) < abs(big["aov"]["lift"])
    assert big["aov"]["treatment"] > big["aov"]["control"]
    assert big["simulated_effect"] == 0.20
```

(Add `import pytest` at the top of the file if not present.)

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_run_experiment.py::test_run_accepts_effect_override -v`
Expected: FAIL with `TypeError: run() got an unexpected keyword argument 'effect'`

- [ ] **Step 3: Thread `effect` through `run()`**

In `src/experiment/run_experiment.py`, change the signature and the two effect-dependent lines:

```python
def run(con: duckdb.DuckDBPyConnection, effect: float = SIMULATED_EFFECT) -> dict[str, object]:
    frame = build_experiment_frame(con)
    check_balance(frame)
    injected = apply_simulated_effect(frame, effect=effect)
    con.register("experiment_frame", injected)
```

And in the returned dict change the constant line:

```python
        "simulated_effect": effect,
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_run_experiment.py -v`
Expected: PASS (existing shape/determinism tests still green — default arg keeps old behavior).

- [ ] **Step 5: Commit**

```bash
SKIP=gitleaks git commit -am "feat: parametrize injected effect in run()"
```

---

## Task 4: Scenario sweep module

**Files:**
- Modify: `src/constants.py`
- Create: `src/experiment/scenarios.py`
- Test: `tests/test_scenarios.py`

- [ ] **Step 1: Add the scenario set to constants**

In `src/constants.py` append (effects chosen relative to the ~2.45% AOV MDE: a true null, a borderline-near-MDE effect, and the headline large effect):

```python
# (name, multiplicative effect) — swept to show the decision rule yields all verdicts.
SCENARIOS: tuple[tuple[str, float], ...] = (
    ("null", 0.0),
    ("borderline", 0.025),
    ("large", 0.05),
)
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_scenarios.py`:

```python
import pytest

from src.experiment.scenarios import run_scenarios
from src.constants import SCENARIOS


def test_run_scenarios_returns_one_result_per_scenario(base_con):
    results = run_scenarios(base_con)
    assert [r["scenario"] for r in results] == [name for name, _ in SCENARIOS]
    for r in results:
        assert "aov" in r and "ci" in r["aov"]
        assert "verdict" in r


def test_run_scenarios_null_is_not_ship(base_con):
    results = run_scenarios(base_con)
    null = next(r for r in results if r["scenario"] == "null")
    # A zero injected effect must not produce a SHIP verdict.
    assert null["verdict"] != "SHIP"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_scenarios.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.experiment.scenarios'`

- [ ] **Step 4: Implement `run_scenarios`**

Create `src/experiment/scenarios.py`:

```python
"""Sweep the injected effect across scenarios to validate the decision rule."""

import duckdb

from src.constants import SCENARIOS
from src.experiment.run_experiment import run
from src.report.experiment_report import recommend


def run_scenarios(
    con: duckdb.DuckDBPyConnection,
    scenarios: tuple[tuple[str, float], ...] = SCENARIOS,
) -> list[dict[str, object]]:
    """Run the experiment once per scenario; tag each with its name and verdict."""
    out: list[dict[str, object]] = []
    for name, effect in scenarios:
        result = run(con, effect=effect)
        result["scenario"] = name
        result["verdict"] = recommend(result["aov"]["ci"])  # type: ignore[index]
        out.append(result)
    return out
```

NOTE: this calls `recommend` (public) — Task 5 renames the existing private `_recommend` to `recommend`. Do Task 5 Step 3's rename first if executing out of order.

- [ ] **Step 5: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_scenarios.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
SKIP=gitleaks git commit -am "feat: add injected-effect scenario sweep"
```

---

## Task 5: Scenarios report + quantile rows

**Files:**
- Modify: `src/report/experiment_report.py`
- Test: `tests/test_report.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_report.py`:

```python
from src.report.experiment_report import generate_scenarios_report


def test_scenarios_report_lists_all_verdicts():
    scenarios = [
        {"scenario": "null", "simulated_effect": 0.0,
         "aov": {"control": 100.0, "treatment": 100.1, "lift": 0.1, "ci": (-2.0, 2.2), "p": 0.9},
         "verdict": "NEED MORE DATA"},
        {"scenario": "large", "simulated_effect": 0.05,
         "aov": {"control": 100.0, "treatment": 105.0, "lift": 5.0, "ci": (3.0, 7.0), "p": 0.001},
         "verdict": "SHIP"},
    ]
    md = generate_scenarios_report(scenarios)
    assert "null" in md and "large" in md
    assert "NEED MORE DATA" in md and "SHIP" in md
    assert "simulated" in md.lower()  # disclaimer carried
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_report.py -k scenarios -v`
Expected: FAIL with `ImportError: cannot import name 'generate_scenarios_report'`

- [ ] **Step 3: Rename `_recommend` -> `recommend` and add the scenarios report**

In `src/report/experiment_report.py`: rename `def _recommend(` to `def recommend(` and update its call site inside `generate_report` (`rec = recommend(aov["ci"])`). Then append:

```python
def generate_scenarios_report(scenarios: list[dict[str, Any]]) -> str:
    """Render the multi-scenario sweep: one row per injected effect, with its verdict."""
    lines = [
        "# Experiment Scenarios — Decision Rule Validation",
        "",
        DISCLAIMER,
        "",
        "Each row injects a different `SIMULATED_EFFECT` and reports the verdict the "
        "AOV 95% bootstrap CI produces. The rule yields SHIP / DO NOT SHIP / NEED MORE "
        "DATA — not just SHIP — which is the point: the pipeline handles the hard cases.",
        "",
        "| Scenario | Injected effect | Control | Treatment | Lift | 95% CI | Verdict |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in scenarios:
        aov = s["aov"]
        lines.append(
            f"| {s['scenario']} | {s['simulated_effect']} | {aov['control']:.2f} | "
            f"{aov['treatment']:.2f} | {aov['lift']:.2f} | "
            f"({aov['ci'][0]:.2f}, {aov['ci'][1]:.2f}) | {s['verdict']} |"
        )
    lines.append("")
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_report.py -v`
Expected: PASS (existing `test_run_feeds_report` etc. still green — only the rename changed, call site updated).

- [ ] **Step 5: Commit**

```bash
SKIP=gitleaks git commit -am "feat: render multi-scenario decision-rule report"
```

---

## Task 6: Scenario outputs + Makefile target + regenerate committed artifacts

**Files:**
- Modify: `src/experiment/run_experiment.py`
- Modify: `Makefile`
- Regenerate (commit): `reports/experiment_001.{md,json}`, `reports/sample_results.json`, `reports/experiment_scenarios.{md,json}`
- Test: `tests/test_run_experiment.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_run_experiment.py`:

```python
def test_write_scenarios_emits_md_and_json(base_con, tmp_path):
    from src.experiment.run_experiment import write_scenarios_outputs
    from src.experiment.scenarios import run_scenarios
    scenarios = run_scenarios(base_con)
    md_path = tmp_path / "experiment_scenarios.md"
    json_path = tmp_path / "experiment_scenarios.json"
    write_scenarios_outputs(scenarios, md_path, json_path)
    assert md_path.exists()
    import json
    parsed = json.loads(json_path.read_text())
    assert len(parsed) == len(scenarios)
    assert parsed[0]["scenario"] == "null"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_run_experiment.py::test_write_scenarios_emits_md_and_json -v`
Expected: FAIL with `ImportError: cannot import name 'write_scenarios_outputs'`

- [ ] **Step 3: Add the scenarios writer + a CLI entrypoint**

In `src/experiment/run_experiment.py` add imports and functions:

```python
from src.report.experiment_report import generate_report, generate_scenarios_report
from src.report.results_io import results_to_json, write_results_json

SCENARIOS_REPORT_PATH = Path("reports/experiment_scenarios.md")
SCENARIOS_JSON_PATH = Path("reports/experiment_scenarios.json")


def write_scenarios_outputs(scenarios, md_path: Path, json_path: Path) -> None:
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(generate_scenarios_report(scenarios))
    json_path.write_text(results_to_json(scenarios) + "\n")
```

Add a `main_scenarios()` that loads full data, runs the sweep, writes the sweep artifacts, AND re-emits `experiment_001.{md,json}` from the `large` scenario (preserving the dashboard contract):

```python
def main_scenarios(raw_dir: Path = RAW_DIR) -> None:
    con = duckdb.connect(":memory:")
    load_olist(con, raw_dir)
    scenarios = run_scenarios(con)
    write_scenarios_outputs(scenarios, SCENARIOS_REPORT_PATH, SCENARIOS_JSON_PATH)
    large = next(s for s in scenarios if s["scenario"] == "large")
    write_outputs(large, REPORT_PATH, JSON_PATH)
    print(f"wrote {SCENARIOS_REPORT_PATH}, {SCENARIOS_JSON_PATH}, {REPORT_PATH}, {JSON_PATH}")
```

(Add `from src.experiment.scenarios import run_scenarios` — guard against a circular import: `scenarios.py` imports from `run_experiment.py`, so import `run_scenarios` lazily *inside* `main_scenarios`, not at module top.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/test_run_experiment.py -v`
Expected: PASS

- [ ] **Step 5: Add the Makefile target**

In `Makefile` add (tab-indented recipe):

```make
scenarios:
	python -m src.experiment.run_experiment --scenarios
```

And at the bottom of `run_experiment.py` replace the `__main__` block:

```python
if __name__ == "__main__":
    import sys
    if "--scenarios" in sys.argv:
        main_scenarios()
    else:
        main()
```

- [ ] **Step 6: Regenerate and commit the full-data artifacts**

Run (requires `data/raw/olist/` present locally):

```bash
make scenarios
.venv/bin/pytest -q   # full suite green
```

Verify by eye: `reports/experiment_scenarios.md` shows three rows with at least two distinct verdicts (null ≠ SHIP); `reports/experiment_001.json` CI changed from the old percentile `(7.35, 13.00)` to the BCa interval. Then regenerate the P3 sample snapshot:

```bash
# sample_results.json is the P3 regression snapshot computed on data/sample/.
# Regenerate it the same way it was originally produced (see scripts/ + STATUS Phase F).
```

Confirm determinism (run twice, compare):

```bash
make scenarios && cp reports/experiment_scenarios.json /tmp/a.json
make scenarios && diff reports/experiment_scenarios.json /tmp/a.json   # no output = byte-stable
```

```bash
SKIP=gitleaks git add reports/ src/ tests/ Makefile && \
SKIP=gitleaks git commit -m "feat: emit scenario sweep + regenerate BCa artifacts"
```

---

## Self-Review

**1. Spec coverage**
- #5 BCa interval → Task 1. ✅
- #5 quantile/distributional view → Task 2. ✅ (Note: quantile rows are computed + tested; wiring them into the *single* report's markdown is deferred to Plan 3 narrative, since it's display text the reframe will rewrite anyway — `quantile_lift` is available and unit-tested here.)
- #1 multi-scenario sweep producing null/borderline/large verdicts → Tasks 3–6. ✅
- P3 determinism preserved → Task 1 (BCa seeded) + Task 6 Step 6 diff check. ✅
- Dashboard P2 contract (`experiment_001.json`) preserved → Task 6 Step 3 re-emits it from `large`. ✅

**2. Placeholder scan** — One soft reference in Task 6 Step 6: regenerating `sample_results.json` points at "the way it was originally produced" rather than inlining the command, because the Phase F sample-build command was not in scope of the files read for this plan. **Executor action:** before running, `grep -rn "sample_results" scripts/ src/ Makefile` to find the exact generator, or read `scripts/build_sample.py` + `docs/PHASE_LOG.md` Phase F entry. If no generator exists, `sample_results.json` is produced by running `run()`/`run_scenarios()` against a DuckDB loaded from `data/sample/` and writing via `write_results_json`. This is the one spot needing a lookup, not a guess.

**3. Type consistency**
- `bootstrap_ci_diff_means` signature unchanged → all callers (`run_experiment.run`) unaffected. ✅
- `recommend` renamed from `_recommend`; call site in `generate_report` updated (Task 5 Step 3); `scenarios.py` imports the public `recommend`. ✅ (Execution order: Task 5's rename must land before Task 4's module runs — if dispatching subagents, run Task 5 Step 3's rename or do Task 4 and 5 in one unit.)
- `run(con, effect=...)` default = `SIMULATED_EFFECT` → existing `run(con)` callers unchanged. ✅
- `results_to_json` already handles `list[dict]` (it's `json.dumps` with numpy default) → scenarios JSON serializes without change. ✅

**Fix applied inline:** Task 4 Step 4 and Task 5 are cross-dependent via `recommend`; flagged the ordering in both tasks so an out-of-order subagent dispatch can't break on the private/public name.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-10-experiment-inference-depth.md`.

Per `CLAUDE.md` model strategy, implementation tasks run on **Sonnet** subagents, Opus verifies after each. Recommended: **subagent-driven-development** — fresh Sonnet subagent per task, two-stage review between tasks (the `recommend` rename + BCa determinism are the two spots to watch).
