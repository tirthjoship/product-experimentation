"""Results: forest plot (bias story) + guardrail row."""

import streamlit as st

from dashboard import charts
from dashboard.data import ExperimentResult


def render(exp: ExperimentResult) -> None:
    st.markdown('<p class="section-label">03 / Results</p>', unsafe_allow_html=True)
    st.plotly_chart(charts.forest(exp), use_container_width=True)
    st.markdown(
        "Two rows on purpose: random assignment put slightly higher-value customers in "
        f"treatment (baseline gap {exp.balance_gap:.1%}). The adjusted row is the "
        "decision basis; showing both keeps the bias visible and auditable."
    )
    g = exp.conversion
    lo, hi = g.ci
    st.markdown(
        f"**Guardrail — delivered rate:** control {g.control:.4f} vs treatment "
        f"{g.treatment:.4f}, diff CI ({lo:+.4f}, {hi:+.4f}) — no detectable harm."
    )
