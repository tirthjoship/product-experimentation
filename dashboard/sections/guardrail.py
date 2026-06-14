"""Interactive: delivered-rate guardrail across all scenarios."""

import streamlit as st

from dashboard import charts
from dashboard.data import ScenarioResult


def render(scenarios: list[ScenarioResult]) -> None:
    st.markdown(
        '<p class="section-label">06 / Guardrail panel</p>', unsafe_allow_html=True
    )
    st.plotly_chart(
        charts.guardrail_plot(scenarios), width="stretch", key="guardrail_delivered"
    )
    st.caption(
        "Delivered-rate difference is statistically indistinguishable from zero in every "
        "scenario — the injected effect targets AOV only, and the guardrail correctly "
        "stays quiet."
    )
