"""Motivation: real Olist descriptive numbers — the affordability mechanism."""

import streamlit as st

from dashboard import charts
from dashboard.data import MotivationStats


def render(stats: MotivationStats) -> None:
    st.markdown('<p class="section-label">01 / Motivation</p>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Orders paid in >1 installment", f"{stats.share_multi_installment:.1%}")
    c2.metric(
        "Credit-card share of payment value", f"{stats.credit_card_value_share:.1%}"
    )
    c3.metric("Cohort orders", f"{stats.n_orders:,}")
    st.plotly_chart(charts.bucket_bar(stats), use_container_width=True)
    st.caption(
        "Descriptive, not causal: the gradient shows the affordability mechanism exists. "
        "Estimating what the cap change *causes* is the experiment's job."
    )
