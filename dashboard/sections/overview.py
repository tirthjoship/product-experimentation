"""Overview tab — one-screen answer: recommendation + evidence.

Sections (top -> bottom):
1. Bottom-line takeaway tile (static SHIP copy, large-scenario framing)
2. Verdict hero (.kicker "Decision" + colored verdict word + "— installment cap 6× → 10×" suffix)
3. Why-it-matters motivation KPIs (.kicker + 3 colored values with vtags)
4. AOV-by-installment bucket bar in bordered .box card + info caption
5. Headline forest in bordered .box card + info caption
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
        f'<span class="num">R${experiment.aov_adjusted.lift:.2f} more per order</span>. '
        f"We are 95% sure the true gain is between "
        f'<span class="num">R${lo:.2f} and R${hi:.2f}</span>. Across '
        f"{motivation.n_orders:,} orders, that more than pays for the change, so we would "
        f"roll it out. <b>That is the optimistic case.</b> If the real effect is "
        f"small or zero, the recommendation changes. The Scenario explorer shows "
        f"exactly when."
    )
    chip_cls = _ui.CHIP_FOR_VALUE[valuecolor.verdict_class("SHIP")]
    st.markdown(
        _ui.takeaway(
            kicker="The bottom line",
            question="Should we raise the installment cap from 6× to 10×?",
            verdict_label="SHIP, in the optimistic case",
            verdict_cls=chip_cls,
            body_html=body_html,
        ),
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # 2. Verdict hero — .kicker + colored verdict word + suffix (verbatim from mockup)
    # ------------------------------------------------------------------
    large_sc = next(s for s in scenarios if s.scenario == "large")
    verdict = large_sc.verdict
    hero_color = theme.verdict_color(verdict)

    aov_def = glossary.define("AOV")
    adj_def = glossary.define("adjusted lift")
    ci_def = glossary.define("CI")

    st.markdown('<div class="kicker">Decision</div>', unsafe_allow_html=True)
    st.markdown(
        f'<h2 class="hero"><span style="color:{hero_color}">{verdict}</span>'
        f": installment cap 6× → 10×</h2>"
        f'<div class="sub">'
        f'<span class="term" data-def="{aov_def}">Average order value</span> '
        f"+R${experiment.aov_adjusted.lift:.2f} · "
        f'<span class="term" data-def="{adj_def}">covariate-adjusted</span> 95% '
        f'<span class="term" data-def="{ci_def}">confidence interval</span> '
        f"R${lo:.2f} to R${hi:.2f} · "
        f"{experiment.n_control:,} control and {experiment.n_treatment:,} treatment customers"
        f"</div>"
        f'<p class="cap">In the optimistic scenario, treated customers '
        f"spent about <b>R${experiment.aov_adjusted.lift:.2f} more</b> per order. "
        f"The true gain is between R${lo:.2f} and R${hi:.2f} with 95% confidence, "
        f"clear of zero, so we would ship. "
        f"The other scenarios show how the call changes when the effect is "
        f"smaller.</p>",
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # 3. Why it matters -- installment affordability KPIs
    # ------------------------------------------------------------------
    st.markdown(
        '<div class="kicker">Why it matters: installment affordability</div>',
        unsafe_allow_html=True,
    )

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
        )
        + "</div></div>"
        # KPI 2: credit_card_value_share
        '<div class="kpi">'
        '<div class="lab">Credit-card value share</div>'
        '<div class="num">'
        + _ui.value(
            f"{motivation.credit_card_value_share:.1%}",
            good_cls,
        )
        + "</div></div>"
        # KPI 3: n_orders (cohort size)
        '<div class="kpi">'
        '<div class="lab">Cohort orders</div>'
        '<div class="num">'
        + _ui.value(
            f"{motivation.n_orders:,}",
            good_cls,
        )
        + "</div></div>"
        "</div>"
    )
    st.markdown(kpi_html, unsafe_allow_html=True)
    st.markdown(
        '<p class="cap">These are descriptive counts from the real Olist orders, '
        "not experiment results.</p>",
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # 4. Bucket bar in bordered .box card + info caption
    # ------------------------------------------------------------------
    bucket_info = _ui.info(
        "How to read: average order value for orders grouped by how many installments "
        "they used. Rising bars show that bigger baskets already use more installments. "
        "This is a correlation that motivates the test, not proof that the cap causes "
        "more spend."
    )
    with st.container(border=True):
        st.markdown(
            f"<h3>Average order value (AOV) by installment bucket "
            f'<span class="term" data-def="Descriptive only: shows the affordability '
            f"pattern exists; it does not prove the cap change causes more spend."
            f'">(descriptive, not causal)</span>{bucket_info}</h3>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            charts.bucket_bar(motivation), width="stretch", key="overview_bucket"
        )
    st.markdown(
        '<p class="cap">Bigger baskets already use more installments, so the '
        "mechanism is plausible. The experiment tests whether "
        "<i>raising the cap causes</i> more spend.</p>",
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # 5. Headline forest in bordered .box card + info caption
    # ------------------------------------------------------------------
    forest_info = _ui.info(
        "How to read: each dot is the estimated lift; the horizontal "
        "line is its 95% confidence interval. If the whole line sits to the right of the "
        "zero line, the effect is positive and statistically significant. The adjusted row "
        "is colored by the verdict and is tighter because covariate correction removes noise."
    )
    st.markdown('<div class="kicker">Headline result</div>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(
            f"<h3>Average order value lift: unadjusted vs covariate-adjusted "
            f"(large scenario){forest_info}</h3>",
            unsafe_allow_html=True,
        )
        adj_color = theme.verdict_color(large_sc.verdict)
        fig = charts.forest(
            large_sc.result,
            title="Average order value lift (R$), 95% confidence interval",
            adj_color=adj_color,
        )
        st.plotly_chart(fig, width="stretch", key="overview_forest")
    st.markdown(
        '<p class="cap">Two estimates of the same effect: the raw difference and the '
        "tighter adjusted one. The full metric set is in <b>Experiment results</b>.</p>",
        unsafe_allow_html=True,
    )
