"""Interactive: scenario radio → verdict flip + CI plots. All numbers read from JSON."""

import streamlit as st

from dashboard import charts, theme, valuecolor
from dashboard.data import ScenarioResult
from dashboard.sections._ui import CHIP_FOR_VALUE, info, takeaway, term, value

# ---------------------------------------------------------------------------
# Friendly radio labels (verbatim from mockup)
# ---------------------------------------------------------------------------
_LABELS: dict[str, str] = {
    "adverse": "Adverse (-5%)",
    "null": "Null (0%)",
    "large": "Large (+5%)",
}

# ---------------------------------------------------------------------------
# Pre-written bottom-line tile body HTML (verbatim from mockup, keyed by scenario)
# ---------------------------------------------------------------------------
_TILE_BODY: dict[str, str] = {
    "adverse": (
        "If the change actually <b>reduces</b> spending by around 5%, customers spend about"
        ' <span class="num">R$7.56 less</span> per order (we are 95% sure the true loss is'
        " between R$5 and R$10). The whole range is below zero, so this is not noise: the"
        " change hurts. <b>Do not ship it.</b>"
    ),
    "null": (
        "If the real effect is near zero, our estimate"
        ' (<span class="num">+R$0.54</span>) could just as easily be slightly negative or'
        " positive, because the range straddles zero. We <b>cannot tell</b> whether it"
        " helps at this sample size. The right move is to <b>collect more data</b>, not"
        " approve or reject."
    ),
    "large": (
        "If the change lifts spending by about 5%, customers spend"
        ' <span class="num">R$8.63 more</span> per order and the entire 95% range'
        " (R$6.15 to R$11.15) is above zero. The two safety metrics did not move."
        " <b>Ship it.</b>"
    ),
}

# ⓘ tooltip text for each chart (verbatim from mockup)
_INFO_AOV = (
    "How to read: dot = lift, line = 95% confidence interval, "
    "zero line marked. The adjusted dot is colored by the verdict of this scenario: "
    "green ship, amber need more data, red do not ship."
)
_INFO_CONV = (
    "How to read: treatment minus control difference in conversion, in percentage "
    "points, with its 95% confidence interval. A line crossing zero means the "
    "guardrail is unaffected. Slate means guardrail, not a verdict."
)
_INFO_D7 = (
    "How to read: the share of control and treatment customers who bought again "
    "within 7 days (D7), as two connected dots. The axis starts at zero, and the gap "
    "between the dots is not meaningful: retention did not change."
)


def _signed_reais(v: float) -> str:
    """Format a signed amount as +R$8.63 / -R$7.56."""
    return f"{'+' if v >= 0 else '-'}R${abs(v):.2f}"


def render(scenarios: list[ScenarioResult]) -> None:
    """Render the Scenario explorer section.

    Parameters
    ----------
    scenarios:
        The 3 committed ScenarioResult objects (adverse / null / large).
    """
    # --- Bottom-line tile (live variant, keyed by selected scenario) ---
    # Show the null tile by default; update below once selection is known.
    # (radio default matches the mockup's "null" checked state)

    # --- Radio ---
    names = [s.scenario for s in scenarios]
    chosen = st.radio(
        "Injected effect scenario",
        names,
        format_func=lambda n: _LABELS.get(n, n),
        horizontal=True,
        index=names.index("null") if "null" in names else 0,
        key="scenarios_radio_scenario",
    )
    s = next(sc for sc in scenarios if sc.scenario == chosen)
    verdict = s.verdict
    color = theme.verdict_color(verdict)
    vcls = valuecolor.verdict_class(verdict)
    chip_cls = CHIP_FOR_VALUE[vcls]

    # --- Bottom-line takeaway tile ---
    tile_body = _TILE_BODY.get(s.scenario, "")
    tile_html = takeaway(
        kicker="The bottom line",
        question="How confident can we be, and when does the decision change?",
        verdict_label=verdict,
        verdict_cls=chip_cls,
        body_html=tile_body,
    )
    st.markdown(tile_html, unsafe_allow_html=True)

    # --- .kicker label (verbatim from mockup) ---
    st.markdown(
        '<div class="kicker">The three committed scenarios</div>',
        unsafe_allow_html=True,
    )

    # --- Verdict chip + raw metrics row ---
    raw_lift = s.result.aov.lift
    adj_lift = s.result.aov_adjusted.lift
    mde = s.result.mde_aov
    mde_cls = valuecolor.mde_class(adj_lift, mde)

    raw_html = value(f"{_signed_reais(raw_lift)}", vcls)
    adj_html = value(f"{_signed_reais(adj_lift)}", vcls)
    mde_html = value(f"R${mde:.2f}", mde_cls)

    raw_label = term("Raw lift", "raw_lift")
    adj_label = term("Adjusted lift", "adjusted_lift")
    mde_label = term("Smallest detectable effect (MDE)", "mde")

    st.markdown(
        f"""
<div class="means">
  <div><div class="lab">{raw_label}</div><div class="num">{raw_html}</div></div>
  <div><div class="lab">{adj_label}</div><div class="num">{adj_html}</div></div>
  <div><div class="lab">{mde_label}</div><div class="num">{mde_html}</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

    # --- Three charts in bordered .box cards ---
    c1, c2, c3 = st.columns(3)

    with c1:
        with st.container(border=True):
            st.markdown(
                f"<h3>Average order value lift: unadjusted vs adjusted{info(_INFO_AOV)}</h3>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                charts.forest(
                    s.result,
                    title=f"Average order value lift ({chosen} scenario)",
                    adj_color=color,
                ),
                width="stretch",
                key="scenarios_forest",
            )

    with c2:
        diff = (s.result.conversion.treatment - s.result.conversion.control) * 100
        conv_ci = (s.result.conversion.ci[0] * 100, s.result.conversion.ci[1] * 100)
        with st.container(border=True):
            st.markdown(
                f"<h3>Conversion: control vs treatment{info(_INFO_CONV)}</h3>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                charts.lift_forest(
                    label="Conversion",
                    est=diff,
                    ci=conv_ci,
                    color=theme.SLATE,
                    x_title="Change in conversion (points)",
                ),
                width="stretch",
                key="scenarios_conv_lift",
            )

    with c3:
        with st.container(border=True):
            st.markdown(
                f"<h3>Repeat purchase within 7 days: control vs treatment{info(_INFO_D7)}</h3>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(
                charts.dumbbell(
                    label="Repeat within 7 days",
                    control=s.result.d7_control,
                    treatment=s.result.d7_treatment,
                    fmt="{:.2%}",
                    x_range=(0.0, 0.02),
                    x_title="Bought again within 7 days",
                    tickformat=".1%",
                ),
                width="stretch",
                key="scenarios_d7_dumbbell",
            )
