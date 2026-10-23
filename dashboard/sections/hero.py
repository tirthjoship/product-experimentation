"""Hero: verdict badge + simulated-experiment disclaimer. Verdict READ from JSON."""

import streamlit as st

from dashboard import theme
from dashboard.data import ExperimentResult


def render(exp: ExperimentResult, verdict: str) -> None:
    st.markdown('<p class="section-label">00 / Decision</p>', unsafe_allow_html=True)
    st.warning(
        "**Simulated experiment.** Olist has no native A/B test. Variants are assigned "
        "by hashed `customer_unique_id` (seed 42) on historical data; the treatment "
        "effect is a labeled synthetic injection. This is a methodology demo, not a real lift."
    )
    color = theme.verdict_color(verdict)
    lo, hi = exp.aov_adjusted.ci
    st.markdown(
        f'<h1 style="font-family:Fraunces,serif;font-size:3.2rem;margin-bottom:0">'
        f'<span style="color:{color}">{verdict}</span>: installment cap 6× → 10×</h1>'
        f'<p style="font-family:IBM Plex Mono,monospace;font-size:1.1rem;color:{theme.SLATE}">'
        f"Average order value +R${exp.aov_adjusted.lift:.2f} · covariate-adjusted 95% "
        f"confidence interval R${lo:.2f} to R${hi:.2f} · "
        f"{exp.n_control:,} control and {exp.n_treatment:,} treatment customers</p>",
        unsafe_allow_html=True,
    )
