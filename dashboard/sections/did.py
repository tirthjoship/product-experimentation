"""Gated DiD natural experiment: honest rejection — gate checklist + pre-trends plot."""

from __future__ import annotations

import streamlit as st

from dashboard import charts, theme
from dashboard.data import DidFeasibility
from dashboard.sections._ui import CHIP_FOR_VALUE, info, takeaway, term

# ---------------------------------------------------------------------------
# Gate condition display helpers — emit .check cards (mockup .checks/.check)
# ---------------------------------------------------------------------------


def _check_card(title: str, passed: bool, detail: str) -> str:
    """Return a single .check card matching the mockup HTML structure."""
    if passed:
        status_html = '<div class="ok">✓ PASS</div>'
    else:
        status_html = '<div class="bad">✗ FAIL</div>'
    return (
        f'<div class="check">'
        f'<div class="t">{title}</div>'
        f"{status_html}"
        f'<div class="d">{detail}</div>'
        f"</div>"
    )


# ---------------------------------------------------------------------------
# Public render
# ---------------------------------------------------------------------------


def render(did: DidFeasibility) -> None:
    """Render the Natural experiment (DiD) tab — honest rejection story."""

    # --- Bottom-line takeaway tile -------------------------------------------
    st.markdown(
        takeaway(
            kicker="The bottom line",
            question="Can a real-world event prove the change actually caused the lift?",
            verdict_label="No, we reject this test",
            verdict_cls=CHIP_FOR_VALUE["poor"],
            body_html=(
                "We hoped the 2018 truckers' strike could act as a natural experiment. "
                "It failed two of four trust checks. The two regions were "
                "<b>already drifting apart before</b> the strike (a gap this large would "
                "be unlikely, "
                f'<span class="num">p = {did.pretrends.wald_p:.3f}</span>, if the regions '
                "had been moving together), and just "
                f'<span class="num">{did.adequate_n.treated_orders:,} orders</span> '
                "were affected, too few to be reliable. We could not trust this "
                "test, so we do not report a number from it."
            ),
        ),
        unsafe_allow_html=True,
    )

    # --- Simbar — verbatim from mockup ---------------------------------------
    did_term = term("difference-in-differences", "pre-trends")
    st.markdown(
        f'<div class="simbar">Pre-registered {did_term} test on the '
        f"<b>2018 truckers' strike</b> (outcome: delivery days). It "
        f"<b>failed its own feasibility gate</b>.</div>",
        unsafe_allow_html=True,
    )

    # --- .kicker + .checks gate cards (verbatim from mockup) -----------------
    st.markdown(
        '<div class="kicker">Feasibility gate: 2 of 4 conditions failed</div>',
        unsafe_allow_html=True,
    )

    checks_html = (
        '<div class="checks">'
        + _check_card("Dated boundary", did.dated_boundary_passed, did.boundary_date)
        + _check_card(
            "Outside our control",
            did.exogenous_passed,
            "an exogenous event: the strike hit the north and northeast regions, not chosen by us",
        )
        + _check_card(
            "Parallel pre-trends",
            did.pretrends.passed,
            f"p-value {did.pretrends.wald_p:.3f}; one gap breaks the band",
        )
        + _check_card(
            "Enough orders",
            did.adequate_n.passed,
            f"only {did.adequate_n.treated_orders:,} treated orders (too few)",
        )
        + "</div>"
    )
    st.markdown(checks_html, unsafe_allow_html=True)

    # --- .kicker "Why it failed" + 2 bordered chart cards --------------------
    st.markdown('<div class="kicker">Why it failed</div>', unsafe_allow_html=True)

    col_pre, col_n = st.columns(2)

    pre_info = info(
        "How to read: each point is the treated minus control gap, in delivery days, "
        "in a week before the event. The shaded band is the allowed range for a valid "
        "difference-in-differences (DiD) test. A point outside the band (red) means "
        "the groups were already diverging, so the parallel-trends assumption fails."
    )
    adequacy_info = info(
        "How to read: two connected dots showing orders available on each side. "
        f"The treated side is far smaller ({did.adequate_n.treated_orders:,}), "
        "too few for a trustworthy estimate."
    )

    with col_pre:
        with st.container(border=True):
            st.markdown(
                f"<h3>{term('Pre-trends', 'pre-trends')}: gaps must stay inside the band"
                f"{pre_info}</h3>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                charts.coef_plot(did.pretrends), width="stretch", key="did_pretrends"
            )

    with col_n:
        with st.container(border=True):
            st.markdown(
                f"<h3>{term('Enough orders?', 'pre-trends')}: treated vs control orders"
                f"{adequacy_info}</h3>",
                unsafe_allow_html=True,
            )
            n = did.adequate_n
            st.plotly_chart(
                charts.dumbbell(
                    label="Orders",
                    control=float(n.control_orders),
                    treatment=float(n.treated_orders),
                    fmt="{:,.0f}",
                ),
                width="stretch",
                key="did_adequacy_dumbbell",
            )

    st.markdown(
        f'<p class="cap">The largest pre-strike gap '
        f"({did.pretrends.max_lead_abs:.2f} days) is outside the "
        f"±{did.pretrends.band:.2f} band"
        + info(
            "The Wald test checks all pre-strike gaps together and rejects parallel "
            f"pre-trends (p-value {did.pretrends.wald_p:.3f}). A small p-value means "
            "the groups were already moving differently."
        )
        + f", so the strike is "
        f"<b>not</b> a clean natural experiment for this question. With only "
        f"{n.treated_orders:,} treated orders as well, we reject the design "
        f"rather than report a number we do not trust.</p>",
        unsafe_allow_html=True,
    )

    # --- .kicker "Geography" + bordered chart card ---------------------------
    st.markdown(
        '<div class="kicker">Geography of the natural experiment</div>',
        unsafe_allow_html=True,
    )

    geo_info = info(
        "How to read: one bar split by strike exposure: treated (north and northeast), "
        "control (south and southeast), excluded (ambiguous). It shows the geographic "
        "basis of the natural experiment and how lopsided it is."
    )
    with st.container(border=True):
        st.markdown(
            f"<h3>{term('State assignment', 'pre-trends')}{geo_info}</h3>",
            unsafe_allow_html=True,
        )
        n_treated = len(did.treated_state_codes)
        n_control = len(did.control_state_codes)
        n_excluded = len(did.excluded_state_codes)
        st.plotly_chart(
            charts.split_bar(
                [
                    ("treated", float(n_treated), theme.RED),
                    ("control", float(n_control), theme.SLATE),
                    ("excluded", float(n_excluded), theme.AMBER),
                ]
            ),
            width="stretch",
            key="did_geography_split",
        )
