"""Plan 4 DiD: the honest rejection — gate checklist + pre-trends plot."""

from __future__ import annotations

import streamlit as st

from dashboard import charts, theme
from dashboard.data import DidFeasibility
from dashboard.sections._ui import CHIP_FOR_VALUE, info, takeaway, term

# ---------------------------------------------------------------------------
# Gate condition display helpers
# ---------------------------------------------------------------------------
_PASS_MARKER = '<span style="color:{green};font-weight:700">✓ PASS</span>'.format(
    green=theme.GREEN
)
_FAIL_MARKER = '<span style="color:{red};font-weight:700">✗ FAIL</span>'.format(
    red=theme.RED
)


def _marker(passed: bool) -> str:
    return _PASS_MARKER if passed else _FAIL_MARKER


def _gate_row(title: str, passed: bool, detail: str) -> str:
    marker = _marker(passed)
    return (
        f'<div style="display:flex;gap:12px;align-items:baseline;'
        f'padding:6px 0;border-bottom:1px solid #eaecef;font-size:13.5px">'
        f'<span style="min-width:200px;font-weight:500">{title}</span>'
        f"{marker}"
        f'<span style="color:#3a4047;margin-left:8px">{detail}</span>'
        f"</div>"
    )


# ---------------------------------------------------------------------------
# Public render
# ---------------------------------------------------------------------------


def render(did: DidFeasibility) -> None:
    """Render the Natural experiment (DiD) tab — honest rejection story."""
    st.markdown(
        '<p class="section-label">04 / Natural experiment — honest rejection</p>',
        unsafe_allow_html=True,
    )

    # --- Bottom-line takeaway tile -------------------------------------------
    st.markdown(
        takeaway(
            kicker="The bottom line",
            question="Can we use the 2018 truckers' strike as a natural experiment?",
            verdict_label="No — we reject this test honestly",
            verdict_cls=CHIP_FOR_VALUE["poor"],
            body_html=(
                "Pre-registered "
                + term("DiD", "pre-trends")
                + " on the <b>2018 truckers’ strike</b> (outcome: delivery days). "
                "It <b>failed its own gate</b> — reporting the rejection is the honest deliverable."
            ),
        ),
        unsafe_allow_html=True,
    )

    # --- Gate checklist ------------------------------------------------------
    st.markdown(
        "<div style='font-family:IBM Plex Mono,monospace;font-size:11px;"
        "letter-spacing:.14em;text-transform:uppercase;color:#7A1F2B;"
        "margin:18px 0 6px'>Feasibility gate — 2 of 4 conditions failed</div>",
        unsafe_allow_html=True,
    )

    gate_html = (
        '<div style="border:1px solid #eaecef;border-radius:8px;'
        'padding:8px 14px;margin-bottom:16px">'
        + _gate_row(
            "Dated boundary",
            did.dated_boundary_passed,
            did.boundary_date,
        )
        + _gate_row(
            "Exogenous assignment",
            did.exogenous_passed,
            "strike hit north/NE, not chosen by us",
        )
        + _gate_row(
            "Parallel pre-trends",
            did.pretrends.passed,
            f"Wald p={did.pretrends.wald_p:.3f}; a lead breaks the band",
        )
        + _gate_row(
            "Adequate n",
            did.adequate_n.passed,
            f"only {did.adequate_n.treated_orders:,} treated orders",
        )
        + "</div>"
    )
    st.markdown(gate_html, unsafe_allow_html=True)

    # --- Pre-trends chart ----------------------------------------------------
    pre_info = info(
        "How to read: each point is the treated−control gap in a week before the "
        "event; the shaded band is the allowed range for a valid DiD. A point breaking "
        "the band (red) means the groups were already diverging — the "
        "parallel-trends assumption fails."
    )
    st.markdown(
        f"<h3 style='font-size:14px;margin:12px 0 4px'>"
        f"{term('Pre-trends', 'pre-trends')} — leads must stay in band"
        f"{pre_info}</h3>",
        unsafe_allow_html=True,
    )
    st.plotly_chart(charts.coef_plot(did.pretrends), width="stretch")

    # --- Sample adequacy dumbbell --------------------------------------------
    adequacy_info = info(
        "How to read: two connected dots showing orders available on each side. "
        f"The treated side is far smaller ({did.adequate_n.treated_orders:,}) "
        "— too few to power a trustworthy estimate."
    )
    st.markdown(
        f"<h3 style='font-size:14px;margin:16px 0 4px'>"
        f"Sample adequacy — treated vs control orders"
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
    )

    # --- Geography split bar -------------------------------------------------
    geo_info = info(
        "How to read: share of states in each role. Excluded states are those with "
        "mixed exposure — neither cleanly treated nor cleanly control."
    )
    st.markdown(
        f"<h3 style='font-size:14px;margin:16px 0 4px'>"
        f"Geography — state allocation"
        f"{geo_info}</h3>",
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
    )

    # --- Closing note --------------------------------------------------------
    st.markdown(
        f"The −2 week lead ({did.pretrends.max_lead_abs:.2f}) breaks the "
        f"±{did.pretrends.band:.2f} band and the Wald test rejects parallel "
        f"pre-trends (p={did.pretrends.wald_p:.3f}) — so the strike is "
        f"<b>not</b> a clean natural experiment for this question. Combined with only "
        f"{n.treated_orders:,} treated orders ({n.week_cell_share_ge_20:.1%} of "
        f"week-cells had ≥20 orders; gate needs 80%), we reject the DiD design "
        f"rather than report a number we don’t trust. "
        f"<b>No post-period estimate was computed</b> — the event catalog was "
        f"committed before any data query (git-verifiable). "
        f"The rejection is the deliverable: it shows the gate has teeth. "
        f"Full record: ADR 0009.",
        unsafe_allow_html=True,
    )
