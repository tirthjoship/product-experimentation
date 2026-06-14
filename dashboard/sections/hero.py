"""Hero: verdict badge + simulated-experiment disclaimer. Verdict READ from JSON."""

import streamlit as st

from dashboard import theme
from dashboard.data import ExperimentResult


def render(exp: ExperimentResult, verdict: str) -> None:
    st.markdown('<p class="section-label">00 / Decision</p>', unsafe_allow_html=True)
    st.warning(
        "**Simulated experiment.** Olist has no native A/B test. Variants are assigned "
        "by hashed `customer_unique_id` (seed 42) on historical data; the treatment "
        "effect is a labeled synthetic injection. Methodology demo — not a real lift."
    )
    color = theme.verdict_color(verdict)
    lo, hi = exp.aov_adjusted.ci
    st.markdown(
        f'<h1 style="font-family:Fraunces,serif;font-size:3.2rem;margin-bottom:0">'
        f'<span style="color:{color}">{verdict}</span> — installment cap 6x → 10x</h1>'
        f'<p style="font-family:IBM Plex Mono,monospace;font-size:1.1rem;color:{theme.SLATE}">'
        f"AOV +{exp.aov_adjusted.lift:.2f} BRL · covariate-adjusted 95% CI "
        f"({lo:.2f}, {hi:.2f}) · n = {exp.n_control:,} / {exp.n_treatment:,}</p>",
        unsafe_allow_html=True,
    )
