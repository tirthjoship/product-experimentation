"""Experiment results tab — 3 metrics, variance reduction, design integrity.

Sections (top -> bottom):
1. Bottom-line takeaway tile ("YES, and the estimate is solid")
2. Simbar (large scenario callout)
3. PRIMARY OUTCOME — AOV: forest + variance-reduction range plot (2 columns)
4. GUARDRAIL OUTCOMES: conversion lift_forest + D7 dumbbell (2 columns)
5. DESIGN INTEGRITY: sample-size split_bar + baseline-balance diverging_marker (2 columns)

All numbers come directly from the ``large`` ScenarioResult — nothing is recomputed.
"""

import streamlit as st

from dashboard import charts, glossary, theme, valuecolor
from dashboard.data import ScenarioResult
from dashboard.sections import _ui


def render(scenarios: list[ScenarioResult]) -> None:
    """Render the Experiment results tab.

    Parameters
    ----------
    scenarios:
        All committed scenario results.  The ``large`` scenario is used as the
        primary display.  The function is tolerant of extra scenarios in the list.
    """
    # ------------------------------------------------------------------
    # Locate the large scenario
    # ------------------------------------------------------------------
    large = next(s for s in scenarios if s.scenario == "large")
    result = large.result
    verdict = large.verdict

    # ------------------------------------------------------------------
    # 1. Bottom-line takeaway tile (verbatim copy from mockup)
    # ------------------------------------------------------------------
    shrink_pct = round((1.0 - result.aov_adjusted.ci_width_ratio) * 100)
    body_html = (
        "Treated customers spent more per order, while the two safety metrics — "
        "whether people <b>buy at all</b> (conversion) and whether they "
        "<b>come back within 7 days</b> (repeat purchase) — barely moved. "
        "So the gain didn't come at the cost of losing customers. We also corrected "
        "for small pre-existing differences between the two groups, which made our "
        f'estimate <span class="num">about {shrink_pct}% sharper</span> — like '
        "getting a bigger study for free."
    )
    chip_cls = _ui.CHIP_FOR_VALUE[valuecolor.verdict_class(verdict)]
    st.markdown(
        _ui.takeaway(
            kicker="The bottom line",
            question="Did the change help spending without hurting anything else — and can we trust the number?",
            verdict_label="YES, and the estimate is solid",
            verdict_cls=chip_cls,
            body_html=body_html,
        ),
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # Simbar
    # ------------------------------------------------------------------
    st.markdown(
        '<div class="simbar">Showing the <b>large (+5%)</b> scenario as the primary '
        "experiment. Switch scenarios in <b>Scenario explorer</b>.</div>",
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # 2. PRIMARY OUTCOME — AOV
    # ------------------------------------------------------------------
    st.markdown(
        '<p class="section-label">Primary outcome — AOV</p>',
        unsafe_allow_html=True,
    )

    col_aov, col_var = st.columns(2)

    aov_def = glossary.define("AOV")

    with col_aov:
        aov_title_html = (
            f'<h3><span class="term" data-def="{aov_def}">AOV</span> lift — '
            f"unadjusted vs adjusted"
            + _ui.info(
                "How to read: dot = estimated lift, line = 95% CI. "
                "Whole line right of zero → ship. "
                "The adjusted row is colored by verdict (green/amber/red) "
                "and is tighter than the raw row."
            )
            + "</h3>"
        )
        st.markdown(aov_title_html, unsafe_allow_html=True)
        st.plotly_chart(
            charts.forest(result, adj_color=theme.verdict_color(verdict)),
            width="stretch",
            key="results_aov_forest",
        )

    with col_var:
        var_title_html = (
            '<h3><span class="term" data-def="'
            + "Variance reduction from ANCOVA: how much the covariate adjustment shrinks the confidence interval."
            + '">Variance reduction</span> from adjustment'
            + _ui.info(
                "How to read: the two horizontal bars are the 95% CIs before (slate) "
                "and after (accent) adjustment. "
                "The shorter adjusted bar = a more precise estimate from the same data."
            )
            + "</h3>"
        )
        st.markdown(var_title_html, unsafe_allow_html=True)
        st.plotly_chart(
            charts.range_plot(
                [
                    ("unadjusted", result.aov.ci, theme.SLATE),
                    ("adjusted", result.aov_adjusted.ci, theme.ACCENT),
                ]
            ),
            width="stretch",
            key="results_variance_range",
        )

    unadj_width = result.aov.ci[1] - result.aov.ci[0]
    adj_width = result.aov_adjusted.ci[1] - result.aov_adjusted.ci[0]
    st.markdown(
        f'<p class="cap">Adjustment shrinks the CI to '
        f"<b>{result.aov_adjusted.ci_width_ratio * 100:.1f}%</b> of its raw width "
        f"(unadjusted {unadj_width:.2f} BRL → adjusted {adj_width:.2f} BRL) — "
        f"a free precision gain with no extra sample.</p>",
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # 3. GUARDRAIL OUTCOMES
    # ------------------------------------------------------------------
    st.markdown(
        '<p class="section-label">Guardrail outcomes — should NOT move</p>',
        unsafe_allow_html=True,
    )

    col_conv, col_d7 = st.columns(2)

    conv_def = glossary.define("conversion")
    d7_def = glossary.define("D7")
    guardrail_def = glossary.define("guardrail")

    # Conversion: lift in percentage points vs zero
    conv_lift = (result.conversion.treatment - result.conversion.control) * 100
    conv_ci = (result.conversion.ci[0] * 100, result.conversion.ci[1] * 100)

    with col_conv:
        conv_title_html = (
            f'<h3><span class="term" data-def="{conv_def}">Conversion</span>'
            f" — control vs treatment"
            + _ui.info(
                "How to read: the dot is the treatment−control difference in conversion "
                "(percentage points); the line is its 95% CI. "
                "Sitting across the zero line means no detectable change — "
                "exactly what a guardrail should do. "
                "Shown in slate because it's a guardrail, not a ship verdict."
            )
            + "</h3>"
        )
        st.markdown(conv_title_html, unsafe_allow_html=True)
        st.plotly_chart(
            charts.lift_forest(
                label="conv. lift",
                est=conv_lift,
                ci=conv_ci,
                color=theme.SLATE,
            ),
            width="stretch",
            key="results_conv_lift",
        )

    with col_d7:
        d7_title_html = (
            f'<h3><span class="term" data-def="{d7_def}">D7 repeat purchase</span>'
            f" — control vs treatment"
            + _ui.info(
                "How to read: two connected dots — control vs treatment share returning "
                "within 7 days. A short connector = little difference, "
                "so the retention guardrail is unaffected."
            )
            + "</h3>"
        )
        st.markdown(d7_title_html, unsafe_allow_html=True)
        st.plotly_chart(
            charts.dumbbell(
                label="D7 %",
                control=result.d7_control,
                treatment=result.d7_treatment,
                fmt="{:.2%}",
            ),
            width="stretch",
            key="results_d7_dumbbell",
        )

    st.markdown(
        f'<p class="cap">The injected effect targets AOV only — '
        f'<span class="term" data-def="{conv_def}">conversion</span> and '
        f'<span class="term" data-def="{d7_def}">D7</span> stay statistically flat, '
        f'exactly what a clean <span class="term" data-def="{guardrail_def}">guardrail</span> '
        f"should show.</p>",
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # 4. DESIGN INTEGRITY
    # ------------------------------------------------------------------
    st.markdown(
        '<p class="section-label">Design integrity</p>',
        unsafe_allow_html=True,
    )

    col_n, col_bal = st.columns(2)

    with col_n:
        n_title_html = (
            '<h3><span class="term" data-def="'
            "Enrollment: customers assigned to each arm by hashed id (seed 42). "
            "Near-equal sizes indicate a clean split."
            '">Sample sizes</span>'
            + _ui.info(
                "How to read: one bar split into the two arms. "
                "Near-equal halves (≈50/50) confirm the random assignment "
                "produced balanced group sizes."
            )
            + "</h3>"
        )
        st.markdown(n_title_html, unsafe_allow_html=True)
        st.plotly_chart(
            charts.split_bar(
                [
                    ("control", result.n_control, theme.SLATE),
                    ("treatment", result.n_treatment, theme.GREEN),
                ]
            ),
            width="stretch",
            key="results_n_split",
        )

    with col_bal:
        bal_title_html = (
            '<h3><span class="term" data-def="'
            "Baseline balance: pre-experiment gap in order value between arms. "
            "Near zero = comparable groups."
            '">Baseline balance</span>'
            + _ui.info(
                "How to read: the diamond is the pre-experiment order-value gap between arms; "
                "the pink band is the acceptable range. "
                "Inside the band = the groups were comparable before any effect was applied."
            )
            + "</h3>"
        )
        st.markdown(bal_title_html, unsafe_allow_html=True)
        st.plotly_chart(
            charts.diverging_marker(
                value=result.balance_gap,
                band=2.0,
                unit="BRL",
            ),
            width="stretch",
            key="results_balance_diverging",
        )
