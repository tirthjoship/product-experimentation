"""Interactive: scenario radio → verdict flip + CI plots. All numbers read from JSON."""

import streamlit as st

from dashboard import charts, theme, valuecolor
from dashboard.data import ScenarioResult
from dashboard.sections._ui import CHIP_FOR_VALUE, info, takeaway, term, value

# ---------------------------------------------------------------------------
# Friendly radio labels (verbatim from mockup)
# ---------------------------------------------------------------------------
_LABELS: dict[str, str] = {
    "adverse": "adverse (−5%)",
    "null": "null (0%)",
    "large": "large (+5%)",
}

# ---------------------------------------------------------------------------
# Pre-written bottom-line tile body HTML (verbatim from mockup, keyed by scenario)
# ---------------------------------------------------------------------------
_TILE_BODY: dict[str, str] = {
    "adverse": (
        "If the change actually <b>reduces</b> spending by around 5%, customers spend about"
        ' <span class="num">R$7.56 less</span> per order (we\'re 95% sure the true loss is'
        " R$5–10). The whole range is below zero, so this isn't noise — the change hurts."
        " <b>Don't ship it.</b>"
    ),
    "null": (
        "If the real effect is near zero, our estimate"
        ' (<span class="num">+R$0.54</span>) could just as easily be slightly negative or'
        " positive — the range straddles zero. We <b>cannot tell</b> whether it helps at"
        " this sample size. The honest move is to <b>collect more data</b>, not approve or"
        " reject."
    ),
    "large": (
        "If the change lifts spending by about 5%, customers spend"
        ' <span class="num">R$8.63 more</span> per order and the entire 95% range (R$6–11)'
        " is comfortably above zero. The two safety metrics didn't move. <b>Ship it.</b>"
    ),
}

# ⓘ tooltip text for each chart (verbatim from mockup)
_INFO_AOV = (
    "How to read: dot = lift, line = 95% CI, zero line marked. "
    "The adjusted dot is colored by this scenario's verdict — "
    "green ship, amber need-more-data, red don't-ship."
)
_INFO_CONV = (
    "How to read: treatment−control difference in conversion with its 95% CI. "
    "Across zero = guardrail unaffected. Slate = guardrail, not a verdict."
)
_INFO_D7 = (
    "How to read: control vs treatment 7-day repeat-purchase share as two connected dots. "
    "Short connector = no meaningful retention change."
)


def render(scenarios: list[ScenarioResult]) -> None:
    """Render the Scenario explorer section.

    Parameters
    ----------
    scenarios:
        The 3 committed ScenarioResult objects (adverse / null / large).
    """
    st.markdown(
        '<p class="section-label">05 / Scenario explorer</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "What this answers: how does the decision change as the true effect gets smaller"
        " — and where exactly does the verdict flip?"
    )

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
        question="How confident can we be — and when does the decision change?",
        verdict_label=verdict,
        verdict_cls=chip_cls,
        body_html=tile_body,
    )
    st.markdown(tile_html, unsafe_allow_html=True)

    # --- Verdict chip + raw metrics row ---
    raw_lift = s.result.aov.lift
    adj_lift = s.result.aov_adjusted.lift
    mde = s.result.mde_aov
    mde_cls = valuecolor.mde_class(adj_lift, mde)

    raw_html = value(f"{raw_lift:+.2f} BRL", vcls)
    adj_html = value(f"{adj_lift:+.2f} BRL", vcls)
    mde_html = value(f"R${mde:.2f}", mde_cls)

    raw_label = term("Raw lift", "raw_lift")
    adj_label = term("Adjusted lift", "adjusted_lift")
    mde_label = term("MDE", "mde")

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

    # --- Three charts in columns ---
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            f"<h3>AOV lift (unadj vs adj){info(_INFO_AOV)}</h3>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            charts.forest(
                s.result,
                title=f"AOV lift — {chosen}",
                adj_color=color,
            ),
            width="stretch",
            key="scenarios_forest",
        )

    with c2:
        diff = s.result.conversion.treatment - s.result.conversion.control
        st.markdown(
            f"<h3>Conversion (c vs t){info(_INFO_CONV)}</h3>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            charts.lift_forest(
                label="conversion diff",
                est=diff,
                ci=s.result.conversion.ci,
                color=theme.SLATE,
            ),
            width="stretch",
            key="scenarios_conv_lift",
        )

    with c3:
        st.markdown(
            f"<h3>D7 repeat (c vs t){info(_INFO_D7)}</h3>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            charts.dumbbell(
                label="D7 repeat",
                control=s.result.d7_control,
                treatment=s.result.d7_treatment,
                fmt="{:.3f}",
            ),
            width="stretch",
            key="scenarios_d7_dumbbell",
        )
