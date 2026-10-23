"""Experiment results tab — 3 metrics, variance reduction, design integrity.

Sections (top -> bottom):
1. Bottom-line takeaway tile ("YES, and the estimate is solid")
2. Simbar (large scenario callout) — verbatim from mockup
3. PRIMARY OUTCOME — AOV: forest + variance-reduction range plot (2 bordered .box cards)
4. GUARDRAIL OUTCOMES: conversion lift_forest + D7 dumbbell (2 bordered .box cards)
5. DESIGN INTEGRITY: sample-size split_bar + baseline-balance diverging_marker (2 bordered .box cards)

All numbers come directly from the ``large`` ScenarioResult — nothing is recomputed.
"""

import streamlit as st

from dashboard import charts, glossary, theme, valuecolor
from dashboard.data import ScenarioResult
from dashboard.sections import _ui

# Zero to 2% keeps the two repeat-purchase dots visually close together.
_D7_RANGE = (0.0, 0.02)


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
        "Treated customers spent more per order, while the two safety metrics "
        "(whether people <b>buy at all</b> and whether they "
        "<b>come back within 7 days</b>) barely moved. "
        "So the gain did not come at the cost of losing customers. We also corrected "
        "for small pre-existing differences between the two groups, which made the "
        f'estimate <span class="num">about {shrink_pct}% sharper</span>, as if '
        "the study were larger."
    )
    chip_cls = _ui.CHIP_FOR_VALUE[valuecolor.verdict_class(verdict)]
    st.markdown(
        _ui.takeaway(
            kicker="The bottom line",
            question="Did the change help spending without hurting anything else, and can we trust the number?",
            verdict_label="Yes",
            verdict_cls=chip_cls,
            body_html=body_html,
        ),
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # 2. Simbar — verbatim from mockup
    # ------------------------------------------------------------------
    st.markdown(
        '<div class="simbar">Showing the <b>large (+5%)</b> scenario as the primary '
        "experiment. Switch scenarios in <b>Scenario explorer</b>.</div>",
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # 3. PRIMARY OUTCOME — AOV (.kicker + 2 bordered .box cards)
    # ------------------------------------------------------------------
    st.markdown(
        '<div class="kicker">Primary outcome: average order value (AOV)</div>',
        unsafe_allow_html=True,
    )

    col_aov, col_var = st.columns(2)

    aov_def = glossary.define("AOV")

    with col_aov:
        with st.container(border=True):
            aov_title_html = (
                f'<h3><span class="term" data-def="{aov_def}">Average order value</span> '
                f"lift: unadjusted vs adjusted"
                + _ui.info(
                    "How to read: dot = estimated lift, "
                    "line = 95% confidence interval. "
                    "Whole line right of zero means ship. "
                    "The adjusted row is colored by verdict (green, amber or red) "
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
        with st.container(border=True):
            var_title_html = (
                '<h3><span class="term" data-def="'
                + "Variance reduction from ANCOVA: how much the covariate adjustment shrinks the confidence interval."
                + '">Variance reduction</span> from adjustment'
                + _ui.info(
                    "How to read: the two horizontal bars are the 95% confidence intervals "
                    "before (slate) and after (accent) adjustment. "
                    "A shorter adjusted bar means a more precise estimate from the same data."
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
        f'<p class="cap">Adjustment shrinks the confidence interval to '
        f"<b>{result.aov_adjusted.ci_width_ratio * 100:.1f}%</b> of its raw width "
        f"(R${unadj_width:.2f} unadjusted, R${adj_width:.2f} adjusted), "
        f"with no extra sample.</p>",
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # 4. GUARDRAIL OUTCOMES (.kicker + 2 bordered .box cards)
    # ------------------------------------------------------------------
    st.markdown(
        '<div class="kicker">Guardrail outcomes: these should not move</div>',
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
        with st.container(border=True):
            conv_title_html = (
                f'<h3><span class="term" data-def="{conv_def}">Conversion</span>'
                f": control vs treatment"
                + _ui.info(
                    "How to read: the dot is the treatment minus control difference in "
                    "conversion, in percentage points; the line is its 95% confidence "
                    "interval. A line crossing zero means no detectable change, which is "
                    "what a guardrail should show. "
                    "Shown in slate because it is a guardrail, not a ship verdict."
                )
                + "</h3>"
            )
            st.markdown(conv_title_html, unsafe_allow_html=True)
            st.plotly_chart(
                charts.lift_forest(
                    label="Conversion",
                    est=conv_lift,
                    ci=conv_ci,
                    color=theme.SLATE,
                    x_title="Difference in conversion (percentage points)",
                ),
                width="stretch",
                key="results_conv_lift",
            )

    with col_d7:
        with st.container(border=True):
            d7_title_html = (
                f'<h3><span class="term" data-def="{d7_def}">Repeat purchase within 7 days</span>'
                f": control vs treatment"
                + _ui.info(
                    "How to read: two connected dots show the share of control and "
                    "treatment customers who bought again within 7 days (D7). The values "
                    "are well under 1%, and the gap between them is not meaningful, so "
                    "the retention guardrail is unaffected. The axis starts at zero so "
                    "the dots are not stretched apart."
                )
                + "</h3>"
            )
            st.markdown(d7_title_html, unsafe_allow_html=True)
            st.plotly_chart(
                charts.dumbbell(
                    label="Repeat within 7 days",
                    control=result.d7_control,
                    treatment=result.d7_treatment,
                    fmt="{:.2%}",
                    x_range=_D7_RANGE,
                    x_title="Customers who bought again within 7 days",
                    tickformat=".1%",
                ),
                width="stretch",
                key="results_d7_dumbbell",
            )

    st.markdown(
        f'<p class="cap">The injected effect targets average order value only. '
        f'<span class="term" data-def="{conv_def}">Conversion</span> and '
        f'<span class="term" data-def="{d7_def}">repeat purchase</span> stay flat, '
        f'as a clean <span class="term" data-def="{guardrail_def}">guardrail</span> '
        f"should. The two repeat-purchase rates are {result.d7_control:.2%} and "
        f"{result.d7_treatment:.2%}: the difference is not meaningful.</p>",
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # 5. DESIGN INTEGRITY (.kicker + 2 bordered .box cards)
    # ------------------------------------------------------------------
    st.markdown(
        '<div class="kicker">Design integrity</div>',
        unsafe_allow_html=True,
    )

    col_n, col_bal = st.columns(2)

    with col_n:
        with st.container(border=True):
            n_title_html = (
                '<h3><span class="term" data-def="'
                "Enrollment: customers assigned to each group by hashed id (seed 42). "
                "Near-equal sizes indicate a clean split."
                '">Sample sizes</span>'
                + _ui.info(
                    "How to read: one bar split into the two groups. "
                    "Near-equal halves (about 50/50) confirm the random assignment "
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
        with st.container(border=True):
            bal_title_html = (
                '<h3><span class="term" data-def="'
                "Baseline balance: pre-experiment gap in order value between groups. "
                "Near zero = comparable groups."
                '">Baseline balance</span>'
                + _ui.info(
                    "How to read: the diamond is the pre-experiment order-value gap between groups,; "
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
                    unit="R$",
                ),
                width="stretch",
                key="results_balance_diverging",
            )
