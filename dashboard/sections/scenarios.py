"""Interactive: scenario radio → verdict flip + CI plot. All numbers precomputed."""

import streamlit as st

from dashboard import charts, theme
from dashboard.data import ScenarioResult

_LABELS = {
    "adverse": "adverse (injected −5%)",
    "null": "null (injected 0%)",
    "large": "large (injected +5%)",
}


def render(scenarios: list[ScenarioResult]) -> None:
    st.markdown(
        '<p class="section-label">05 / Scenario explorer</p>', unsafe_allow_html=True
    )
    st.markdown(
        "Same pipeline, three injected effects — the decision rule must reject harm and "
        "withhold judgment on null, not just approve the favorable case."
    )
    names = [s.scenario for s in scenarios]
    chosen = st.radio(
        "Injected effect scenario",
        names,
        format_func=lambda n: _LABELS.get(n, n),
        horizontal=True,
    )
    s = next(sc for sc in scenarios if sc.scenario == chosen)
    color = theme.verdict_color(s.verdict)
    st.markdown(
        f'<h2 style="color:{color};font-family:Fraunces,serif">{s.verdict}</h2>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(
        charts.forest(s.result, title=f"AOV lift — scenario: {chosen}"),
        width="stretch",
    )
    raw, adj = s.result.aov.lift, s.result.aov_adjusted.lift
    st.markdown(
        f"Raw lift **{raw:+.2f}** → adjusted **{adj:+.2f}** BRL. "
        "The gap is baseline imbalance the ANCOVA removes — in the null scenario the "
        "raw number alone would overstate the effect."
    )
    if s.verdict == "NEED MORE DATA":
        st.info(
            f"Adjusted CI includes zero and the effect is below the detectable floor "
            f"(MDE ≈ R${s.result.mde_aov:.2f}): the honest call is more data, not a verdict."
        )
