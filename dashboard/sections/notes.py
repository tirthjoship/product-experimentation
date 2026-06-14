"""How to read this — 3 bullets, link out for depth. No prose wall."""

import streamlit as st


def render() -> None:
    st.markdown(
        '<p class="section-label">02 / How to read this</p>', unsafe_allow_html=True
    )
    st.markdown(
        "- **Randomization:** by `customer_unique_id` hash (seed 42) — customer-level, "
        "since a customer must always see the same cap.\n"
        "- **Inference:** BCa bootstrap CI on the AOV difference + ANCOVA adjustment on "
        "pre-treatment `freight_value` (removes baseline arm imbalance, tightens the CI).\n"
        "- **Decision rule:** ship only if the *adjusted* CI excludes zero and the "
        "delivered-rate guardrail shows no harm.\n\n"
        "Full memo: [`reports/experiment_001_readout.md`]"
        "(https://github.com/tirthjoship/product-experimentation-analytics/blob/main/"
        "reports/experiment_001_readout.md)"
    )
