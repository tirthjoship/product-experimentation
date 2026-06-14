"""Overview tab — one-screen answer: recommendation + evidence.

Sections (top -> bottom):
1. Bottom-line takeaway tile (static SHIP copy, large-scenario framing)
2. Verdict hero (colored h2 + sub-line)
3. Why-it-matters motivation KPIs (3 colored values with vtags)
4. AOV-by-installment bucket bar + info caption
5. Headline forest (large scenario, adjusted row colored by verdict) + info caption
"""

import streamlit as st

from dashboard import charts, glossary, theme, valuecolor
from dashboard.data import ExperimentResult, MotivationStats, ScenarioResult
from dashboard.sections import _ui


def render(
    experiment: ExperimentResult,
    scenarios: list[ScenarioResult],
    motivation: MotivationStats,
) -> None:
    """Render the Overview tab.

    Parameters
    ----------
    experiment:
        The primary (large-scenario) experiment result used for the hero numbers.
    scenarios:
        All three committed scenario results.  The one with ``.scenario == "large"``
        is used to colour the adjusted forest row via its verdict.
    motivation:
        Descriptive stats for the installment-affordability KPI cards.
    """
    # ------------------------------------------------------------------
    # 1. Bottom-line takeaway tile (verbatim copy from mockup)
    # ------------------------------------------------------------------
    lo, hi = experiment.aov_adjusted.ci
    body_html = (
        f"If the change really lifts spending by about 5%, customers spend on average "
        f'<span class="num">R${experiment.aov_adjusted.lift:.2f} more per order</span>, '
        f"and we're 95% sure the true gain is between "
        f'<span class="num">R${lo:.0f} and R${hi:.0f}</span> — across '
        f"{motivation.n_orders:,} orders that more than pays for the change, so we'd "
        f"roll it out. <b>But that's the optimistic case.</b> If the real effect is "
        f"small or zero, the recommendation flips — see the Scenario explorer for "
        f"exactly when."
    )
    chip_cls = _ui.CHIP_FOR_VALUE[valuecolor.verdict_class("SHIP")]
    st.markdown(
        _ui.takeaway(
            kicker="The bottom line",
            question="Should we raise the installment cap from 6× to 10×?",
            verdict_label="SHIP — in the optimistic case",
            verdict_cls=chip_cls,
            body_html=body_html,
        ),
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # 2. Verdict hero
    # ------------------------------------------------------------------
    large_sc = next(s for s in scenarios if s.scenario == "large")
    verdict = large_sc.verdict
    hero_color = theme.verdict_color(verdict)

    adj_def = glossary.define("adjusted lift")
    ci_def = glossary.define("CI")

    st.markdown('<p class="section-label">Decision</p>', unsafe_allow_html=True)
    st.markdown(
        f'<h2 class="hero" style="color:{hero_color}">{verdict}</h2>'
        f'<p style="font-family:IBM Plex Mono,monospace;font-size:1rem;'
        f'color:{theme.SLATE}">'
        f"AOV +{experiment.aov_adjusted.lift:.2f} BRL · "
        f'<span class="term" data-def="{adj_def}">covariate-adjusted</span> 95% '
        f'<span class="term" data-def="{ci_def}">CI</span> '
        f"({lo:.2f}, {hi:.2f}) · "
        f"n = {experiment.n_control:,} / {experiment.n_treatment:,}"
        f"</p>"
        f'<p class="cap">Plain English: in the optimistic scenario, treated customers '
        f"spent about <b>R${experiment.aov_adjusted.lift:.2f} more</b> per order; "
        f"we're 95% confident the true gain is "
        f"R${lo:.0f}–{hi:.0f} — clear of zero, so we'd ship. "
        f"The other scenarios (below) show how the call changes when the effect is "
        f"smaller.</p>",
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # 3. Why it matters -- installment affordability KPIs
    # ------------------------------------------------------------------
    st.markdown(
        '<p class="section-label">Why it matters — installment affordability</p>',
        unsafe_allow_html=True,
    )

    # All three KPIs are in the "good" tier (strong/ample) per the mockup.
    good_cls = valuecolor.verdict_class("SHIP")  # -> "good"

    kpi_html = (
        '<div class="cards">'
        # KPI 1: share_multi_installment
        '<div class="kpi">'
        '<div class="lab">Orders paid in &gt;1 installment</div>'
        '<div class="num">'
        + _ui.value(
            f"{motivation.share_multi_installment:.1%}",
            good_cls,
            tag="strong",
        )
        + "</div></div>"
        # KPI 2: credit_card_value_share
        '<div class="kpi">'
        '<div class="lab">Credit-card value share</div>'
        '<div class="num">'
        + _ui.value(
            f"{motivation.credit_card_value_share:.1%}",
            good_cls,
            tag="strong",
        )
        + "</div></div>"
        # KPI 3: n_orders (cohort size)
        '<div class="kpi">'
        '<div class="lab">Cohort orders</div>'
        '<div class="num">'
        + _ui.value(
            f"{motivation.n_orders:,}",
            good_cls,
            tag="ample",
        )
        + "</div></div>"
        "</div>"
    )
    st.markdown(kpi_html, unsafe_allow_html=True)

    # ------------------------------------------------------------------
    # 4. Bucket bar + info caption
    # ------------------------------------------------------------------
    bucket_info = _ui.info(
        "How to read: average order value for orders grouped by how many installments "
        "they used. Rising bars show bigger baskets already use more installments "
        "— a correlation that motivates the test, not proof the cap causes more "
        "spend."
    )
    st.markdown(
        f"<h3>AOV by installment bucket "
        f'<span style="font-weight:400;color:{theme.SLATE}">'
        f"(descriptive, not causal)</span>{bucket_info}</h3>",
        unsafe_allow_html=True,
    )
    st.plotly_chart(charts.bucket_bar(motivation), use_container_width=True)
    st.markdown(
        '<p class="cap">Bigger baskets already use more installments — the '
        "mechanism is plausible. The experiment tests whether "
        "<i>raising the cap causes</i> more spend.</p>",
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # 5. Headline forest (large scenario) + info caption
    # ------------------------------------------------------------------
    forest_info = _ui.info(
        "How to read: each dot is the estimated lift in BRL; the horizontal line is "
        "its 95% confidence interval. If the whole line sits to the right of the zero "
        "line, the effect is positive and significant. The adjusted row is colored by "
        "the verdict and is tighter because covariate correction removes noise."
    )
    st.markdown('<p class="section-label">Headline result</p>', unsafe_allow_html=True)
    st.markdown(
        f"<h3>AOV lift — unadjusted vs covariate-adjusted "
        f"(large scenario){forest_info}</h3>",
        unsafe_allow_html=True,
    )
    adj_color = theme.verdict_color(large_sc.verdict)
    fig = charts.forest(
        large_sc.result,
        title="AOV lift (BRL) — 95% CI",
        adj_color=adj_color,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown(
        '<p class="cap">Two estimates of the same effect: the raw difference and the '
        "tighter ANCOVA-adjusted one. Full metric set in <b>Experiment results</b>.</p>",
        unsafe_allow_html=True,
    )
