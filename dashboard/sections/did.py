"""Plan 4 DiD: the honest rejection — gate checklist + pre-trends plot."""

import streamlit as st

from dashboard import charts
from dashboard.data import DidFeasibility

_CHECK = {True: "✅ PASS", False: "❌ FAIL"}


def render(did: DidFeasibility) -> None:
    st.markdown(
        '<p class="section-label">04 / Natural experiment — honest rejection</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"**Event:** {did.event} (boundary {did.boundary_date}) · "
        f"**outcome:** {did.outcome} · **verdict: {did.verdict}**"
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Dated boundary", _CHECK[did.dated_boundary_passed])
    c2.metric("Exogenous assignment", _CHECK[did.exogenous_passed])
    c3.metric("Parallel pre-trends", _CHECK[did.pretrends.passed])
    c4.metric("Adequate n", _CHECK[did.adequate_n.passed])
    st.plotly_chart(charts.coef_plot(did.pretrends), use_container_width=True)
    n = did.adequate_n
    st.markdown(
        f"Density also failed: {n.week_cell_share_ge_20:.1%} of week-cells had ≥20 orders "
        f"(gate needs 80%) — treated {n.treated_orders:,} orders across "
        f"{n.treated_states} states vs control {n.control_orders:,} across "
        f"{n.control_states}."
    )
    st.markdown(
        "Per the pre-registered protocol, **no post-period estimate was computed** — the "
        "event catalog was committed before any data query (git-verifiable). "
        "The rejection is the deliverable: it shows the gate has teeth. "
        "Full record: ADR 0009."
    )
