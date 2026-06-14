# Plan 5 — Results Dashboard (Streamlit) — Design Spec

**Date:** 2026-06-12 · **Status:** approved design, pre-implementation
**Depends on:** Plans 1–4 shipped (experiment_001, scenarios, installment motivation, DiD rejection)

## 1. Purpose & audience

Dual-audience, dual-tab dashboard:

- **Story tab (landing):** recruiter/hiring-manager proves product + stats judgment in
  60 seconds. Read-only narrative: decision, motivation, method, results, honest DiD rejection.
- **Interactive tab:** analyst flips between pre-computed scenarios (adverse/null/large) and
  watches the verdict + CI respond. Demonstrates the decision rule handles harm and null,
  not just the favorable case.

Success criterion: a recruiter reaches a live URL (or README screenshot) and grasps the
SHIP decision, the bias-correction story, and the DiD honest rejection without reading code.

## 2. Data source — precomputed reports only

The dashboard **reads committed `reports/*.json` only. No live recompute. No new numbers.**
Verdicts are read verbatim from JSON (computed once by `src/experiment/scenarios.py`), never
re-derived in the dashboard — single source of truth, no drift, "no invented metrics" holds
by construction.

| Loader | File | Returns |
|--------|------|---------|
| `load_experiment()` | `reports/experiment_001.json` | `ExperimentResult` |
| `load_scenarios()` | `reports/experiment_scenarios.json` | `list[ScenarioResult]` (3) |
| `load_motivation()` | `reports/installment_motivation.json` | `MotivationStats` |
| `load_did()` | `reports/did_feasibility.json` | `DidFeasibility` |

Excluded: `sample_results.json` (small-n test fixture, not portfolio content).

Schema facts loaders MUST honor:

- `did_feasibility.json` is a **top-level list** (one event today); loader takes `[0]`.
- `parallel_pretrends.leads` is a dict keyed by **string negatives** (`"-5"`…`"-2"`); the
  pre-trends x-axis derives from these keys, never a hardcoded range.
- `ci` fields are 2-element `[lo, hi]` with `lo <= hi`; loaders validate and raise on violation.

## 3. Architecture

```
dashboard/
  app.py              # st.set_page_config + tab shell (Story | Interactive)
  data.py             # pure loaders: JSON path → frozen dataclass. No streamlit imports
                      #   except @st.cache_data wrappers. Raises ReportSchemaError.
  theme.py            # color constants, plotly layout defaults, fonts, verdict→color map
  charts.py           # pure plotly figure builders: forest(), coef_plot(), bucket_bar()
  sections/
    hero.py           # verdict badge + simulated-experiment disclaimer banner
    motivation.py     # AOV-by-bucket bar
    notes.py          # "how to read this" — 3 bullets + link to readout memo
    results.py        # forest plot + guardrail + MDE & variance-reduction annotations
    did.py            # pre-trends coef plot + 4-condition gate checklist
    scenarios.py      # interactive scenario radio → verdict flip + CI plot
    guardrail.py      # delivered-rate bands across scenarios
```

Layering rule: `data.py`, `charts.py`, `theme.py` are **pure** (testable with fixtures,
no `st.` rendering). `sections/*` are render-only glue: take parsed dataclass, call chart
builder, `st.plotly_chart`. Logic never lives in sections.

- Caching: loaders wrapped `@st.cache_data`; returns are frozen dataclasses of
  primitives/tuples only (no DataFrames/arrays in cached returns).
- Paths: `REPORTS_DIR = Path(__file__).parent.parent / "reports"` — repo-relative.
- Interactive state: `st.radio` indexes the cached scenario list. Pure in-memory; zero compute.

## 4. Content map

| Tab | Section | Source | Visual / beat |
|-----|---------|--------|---------------|
| Story | Hero | experiment_001 | SHIP verdict badge + adjusted lift + CI; sticky amber **simulated-experiment disclaimer** banner |
| Story | Motivation | installment_motivation | AOV-by-bucket bar (1→121, 7+→337); 51.4% multi-installment, 78.4% card share |
| Story | How to read this | static | **3 bullets max** (randomization unit, ANCOVA, decision rule) + link to `reports/experiment_001_readout.md`. No prose wall. |
| Story | Results | experiment_001 | Forest plot: unadjusted vs adjusted AOV CI overlay + zero line. **Annotations: "adjusted CI 13% tighter (ci_width_ratio 0.868 ≈ √(1−r²) optimum)" and "MDE ≥ R$4.32"**. Guardrail delivered-rate row. |
| Story | DiD honest rejection | did_feasibility | Pre-trends lead-coef plot with ±band shading; diverging lead (−2, 3.40 > band 1.93) drawn red. 4-condition gate checklist with pass/fail badges. Framing: "the rejection is the deliverable" (ADR 0009). |
| Interactive | Scenario explorer | experiment_scenarios | Radio adverse/null/large → verdict badge flips (DO NOT SHIP / NEED MORE DATA / SHIP) + CI plot updates. Null scenario surfaces raw 2.06 → adjusted 0.54 bias-correction row + ties NEED-MORE-DATA to MDE (power story). |
| Interactive | Guardrail panel | experiment_scenarios | Delivered-rate point + CI across scenarios. |

## 5. Visual direction

Concept: **"lab notebook meets financial terminal."** Editorial restraint; numbers are the hero.

- Background warm off-white `#FAF8F3`; cards white with `1px #E5E0D5` rule borders; ink `#1A1A1A`.
- **Color = signal only:** SHIP green `#2E7D4F`, DO-NOT-SHIP red `#C0392B`, NEED-MORE-DATA
  amber `#C99A2E`; neutral data ink slate `#5A6B7B`. Nothing decorative is colored.
- Type: Fraunces (display) · Source Sans 3 (body) · IBM Plex Mono (numbers/CIs — tabular alignment).
- Section labels in mono: `01 / MOTIVATION` (lab-notebook tell).
- Charts: no gridline clutter; annotations over legends; zero-line dashed on forest plot;
  band shading grey on pre-trends with the violating lead in red.

## 6. Dependencies & tooling changes

- Add `plotly` to `[project.optional-dependencies].dashboard` (alongside existing
  `streamlit>=1.40.0`). **Currently undeclared — blocker found in design review.**
- mypy: add `plotly.*` to the existing ignore-missing-imports override module list;
  `dashboard/` is **strict-checked** (not excluded) with targeted `# type: ignore` only where
  Streamlit stubs fail. The stale `app/` entry in `exclude` stays untouched.
- Coverage: omit by precise path — `dashboard/sections/*`, `dashboard/app.py` — in
  `[tool.coverage.run] omit`. `data.py`, `charts.py`, `theme.py` carry the 90% gate.

## 7. Error handling — fail loud, never fake

- Missing report file → loader raises `FileNotFoundError` → section renders
  `st.error("Missing reports/X.json — run `make <target>`")`. Other sections still render.
- Missing/mistyped field → `ReportSchemaError(path, field)` → `st.error` naming the field.
  **No `dict.get(k, default)` masking** — a missing `ci` must error, never become `[0, 0]`.
- Malformed CI (len ≠ 2, lo > hi) → raises at parse; degenerate bars never render.
- Per-section isolation: each `sections/*.render()` wrapped try/except at tab level; one
  broken section shows an inline error card, the rest survive.
- No `except: pass`, no default zeros, no "N/A" masking parse failures anywhere.

## 8. Testing

Fixtures only (`tests/dashboard/fixtures/*.json`, tiny hand-built) — never full Olist,
never live `reports/`.

| Target | Tests |
|--------|-------|
| `data.load_*` | valid fixture → correct fields; missing `ci` → `ReportSchemaError`; malformed CI → raises; DiD **list** shape + string-negative lead keys parsed; verdicts read verbatim |
| `charts.*` | returns `go.Figure`; required traces present (adjusted overlay, zero line, band) — presence only, **no trace-internal geometry assertions** (brittle, version-coupled) |
| `theme.verdict_color()` | SHIP→green, DO NOT SHIP→red, NEED MORE DATA→amber, unknown→raises |
| Property (Hypothesis) | on the **data transform**, not rendered output: for any valid `(lo, hi)` input, chart input data keeps `lo ≤ point ≤ hi`, no NaN; motivation buckets preserve given order |

**Schema-drift guard:** `make dashboard-smoke` — imports all loaders, runs them against the
real committed `reports/*.json`, asserts no exception. Wired as a job in the **existing
`.github/workflows/ci.yml`** (CI already exists: ci/lint/security), runs on PRs. This is the
guard against report-writer field renames silently breaking the deployed app.

## 9. Deployment — a deliverable, not an afterthought

1. Deploy to **Streamlit Community Cloud** from `main` (`dashboard/app.py` entrypoint);
   deploy env installs the `dashboard` extra (document exact manifest in README).
2. Commit **2–3 PNG screenshots** to `docs/img/` and embed in README **above** the live
   link — covers Community Cloud cold-start/sleep (30–60 s spinner) and app removal.
3. README gets a "Live dashboard ↗" link + screenshots near the top.

Without a reachable URL + screenshot fallback the dashboard fails its primary purpose.

## 10. Out of scope (YAGNI)

- Live recompute / sliders over the experiment engine (possible later; needs sample-data
  caching design and a drift story).
- `sample_results.json` surface, EDA-gate page, PM-memo full text (linked, not embedded).
- Multi-event DiD support beyond rendering the single committed event.
- Auth, theming toggle, mobile-specific layout work beyond Streamlit defaults.

## 11. Risks (from design review)

1. ~~Plotly undeclared~~ → resolved by §6.
2. Schema drift breaking deployed app → resolved by §8 smoke job in CI.
3. Dashboard adds nothing over markdown reports → mitigated by the three differentiators:
   interactive scenario-flip, forest-plot bias story with variance-reduction annotation,
   pre-trends visual proof of honest rejection. If these land thin at review, cut scope and
   polish the readout memo instead.
