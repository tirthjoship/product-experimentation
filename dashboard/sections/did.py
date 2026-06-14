"""Plan 4 DiD: the honest rejection — gate checklist + pre-trends plot."""

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
            verdict_label="No — we reject this test honestly",
            verdict_cls=CHIP_FOR_VALUE["poor"],
            body_html=(
                "We hoped the 2018 truckers' strike could act as a natural experiment. "
                "It failed two of four trust checks: the two regions were "
                "<b>already drifting apart before</b> the strike (only a "
                f'<span class="num">{did.pretrends.wald_p:.1%} chance</span> '
                "that's coincidence), and just "
                f'<span class="num">{did.adequate_n.treated_orders:,} orders</span> '
                "were affected — too few to be reliable. Reporting “we couldn’t trust "
                "this, so we won’t claim a number” <b>is</b> the deliverable — a "
                "credible analyst says no when the evidence isn’t there."
            ),
        ),
        unsafe_allow_html=True,
    )

    # --- Simbar — verbatim from mockup ---------------------------------------
    did_term = term("DiD", "pre-trends")
    st.markdown(
        f'<div class="simbar">Pre-registered {did_term} on the '
        f"<b>2018 truckers' strike</b> (outcome: delivery days). It "
        f"<b>failed its own gate</b> — reporting the rejection is the honest deliverable.</div>",
        unsafe_allow_html=True,
    )

    # --- .kicker + .checks gate cards (verbatim from mockup) -----------------
    st.markdown(
        '<div class="kicker">Feasibility gate — 2 of 4 conditions failed</div>',
        unsafe_allow_html=True,
    )

    checks_html = (
        '<div class="checks">'
        + _check_card("Dated boundary", did.dated_boundary_passed, did.boundary_date)
        + _check_card(
            "Exogenous assignment",
            did.exogenous_passed,
            "strike hit north/NE, not chosen by us",
        )
        + _check_card(
            "Parallel pre-trends",
            did.pretrends.passed,
            f"Wald p={did.pretrends.wald_p:.3f}; a lead breaks the band",
        )
        + _check_card(
            "Adequate n",
            did.adequate_n.passed,
            f"only {did.adequate_n.treated_orders:,} treated orders",
        )
        + "</div>"
    )
    st.markdown(checks_html, unsafe_allow_html=True)

    # --- .kicker "Why it failed" + 2 bordered chart cards --------------------
    st.markdown('<div class="kicker">Why it failed</div>', unsafe_allow_html=True)

    col_pre, col_n = st.columns(2)

    pre_info = info(
        "How to read: each point is the treated−control gap in a week before the "
        "event; the shaded band is the allowed range for a valid DiD. A point breaking "
        "the band (red) means the groups were already diverging — the "
        "parallel-trends assumption fails."
    )
    adequacy_info = info(
        "How to read: two connected dots showing orders available on each side. "
        f"The treated side is far smaller ({did.adequate_n.treated_orders:,}) "
        "— too few to power a trustworthy estimate."
    )

    with col_pre:
        with st.container(border=True):
            st.markdown(
                f"<h3>{term('Pre-trends', 'pre-trends')} — leads must stay in band"
                f"{pre_info}</h3>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                charts.coef_plot(did.pretrends), width="stretch", key="did_pretrends"
            )

    with col_n:
        with st.container(border=True):
            st.markdown(
                f"<h3>{term('Sample adequacy', 'pre-trends')} — treated vs control orders"
                f"{adequacy_info}</h3>",
                unsafe_allow_html=True,
            )
            n = did.adequate_n
            st.plotly_chart(
                charts.dumbbell(
                    label="orders",
                    control=float(n.control_orders),
                    treatment=float(n.treated_orders),
                    fmt="{:,.0f}",
                ),
                width="stretch",
                key="did_adequacy_dumbbell",
            )

    st.markdown(
        f'<p class="cap">The −2 week lead ({did.pretrends.max_lead_abs:.2f}) breaks the '
        f"±{did.pretrends.band:.2f} band and the Wald test rejects parallel "
        f"pre-trends (p={did.pretrends.wald_p:.3f}) — so the strike is "
        f"<b>not</b> a clean natural experiment for this question. Combined with only "
        f"{n.treated_orders:,} treated orders, we reject the DiD design "
        f"rather than report a number we don't trust.</p>",
        unsafe_allow_html=True,
    )

    # --- .kicker "Geography" + bordered chart card ---------------------------
    st.markdown(
        '<div class="kicker">Geography of the natural experiment</div>',
        unsafe_allow_html=True,
    )

    geo_info = info(
        "How to read: one bar split by strike exposure — treated (north/NE), "
        "control (south/SE), excluded (ambiguous). Shows the geographic basis of "
        "the natural experiment and how lopsided it is."
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
