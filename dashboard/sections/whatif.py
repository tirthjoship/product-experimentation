"""What-if grid slider: snap to precomputed grid point → verdict + charts.

All numbers (verdict, lift, CI) are READ from the precomputed ScenarioResult.
Nothing is recomputed in the browser or here — the slider only selects a point.
"""

from __future__ import annotations

import streamlit as st

from dashboard import charts, theme, valuecolor
from dashboard.data import ScenarioResult
from dashboard.sections._ui import info

# ⓘ tooltip text (verbatim from mockup)
_INFO_AOV = (
    "How to read: the dot is the adjusted lift at the effect "
    "size on the slider; the line is its 95% confidence interval. Color shows the "
    "verdict: green if the whole line clears zero (ship), red if it is all below zero "
    "(do not ship), amber if it straddles zero (need more data)."
)
_INFO_CONV = (
    "How to read: treatment minus control difference in conversion, in percentage "
    "points, with its 95% confidence interval. A line crossing zero means the "
    "guardrail is unaffected. Slate means guardrail, not a verdict."
)

# Verbatim SIMULATED banner text from mockup (HTML — <b> not markdown **)
_SIMULATED_BANNER_HTML = (
    "<b>SIMULATED</b>: synthetic injection, same method as the committed scenarios. "
    "The slider snaps to precomputed grid points, so no number is generated in the browser."
)


def render(grid: list[ScenarioResult]) -> None:
    """Render the What-if grid slider section.

    Parameters
    ----------
    grid:
        All precomputed grid ScenarioResult objects, one per injected-effect level.
        Sorted ascending by ``result.simulated_effect`` before display.
    """
    st.markdown(
        '<div class="kicker">What-if: find where the decision flips</div>',
        unsafe_allow_html=True,
    )

    # --- SIMULATED banner (verbatim mockup text, HTML bold) ---
    st.markdown(
        f'<div class="simbar">{_SIMULATED_BANNER_HTML}</div>',
        unsafe_allow_html=True,
    )

    # Sort grid ascending by simulated_effect so slider goes left→right
    sorted_grid = sorted(grid, key=lambda s: s.result.simulated_effect)

    # Build slider values from the grid (already precomputed — never generate new numbers)
    effect_values = [s.result.simulated_effect for s in sorted_grid]

    # st.select_slider requires hashable options; format as percentage strings for display
    def _fmt(v: float) -> str:
        pct = round(v * 100)
        return f"{pct:+d}%"

    # Default to the midpoint (index nearest 0)
    mid_idx = min(range(len(effect_values)), key=lambda i: abs(effect_values[i]))

    chosen_label = st.select_slider(
        "Injected effect (change in order value)",
        options=[_fmt(v) for v in effect_values],
        value=_fmt(effect_values[mid_idx]),
        label_visibility="visible",
        key="whatif_select_slider_effect",
    )

    # Snap: map chosen label back to index, then to grid point
    chosen_idx = [_fmt(v) for v in effect_values].index(chosen_label)
    pt = sorted_grid[chosen_idx]

    verdict = pt.verdict
    color = theme.verdict_color(verdict)
    vcls = valuecolor.verdict_class(verdict)
    adj_lift = pt.result.aov_adjusted.lift

    # --- Verdict chip + adjusted lift ---
    chip_css = {"good": "ship", "average": "more", "poor": "no"}.get(vcls, "more")
    adj_colored = f'<span class="v-{vcls}">{"+" if adj_lift >= 0 else "-"}R${abs(adj_lift):.2f}</span>'
    st.markdown(
        f'<div style="display:flex;gap:24px;align-items:center;margin:10px 0">'
        f'Verdict: <span class="chip {chip_css}">{verdict}</span>'
        f"&nbsp;&nbsp; adjusted lift {adj_colored}"
        f"</div>",
        unsafe_allow_html=True,
    )

    # --- AOV forest chart in bordered .box card ---
    with st.container(border=True):
        st.markdown(
            f"<h3>Average order value lift at the injected effect{info(_INFO_AOV)}</h3>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            charts.forest(
                pt.result,
                title=f"Average order value lift (injected {chosen_label})",
                adj_color=color,
            ),
            width="stretch",
            key="whatif_forest",
        )

    # --- Conversion lift_forest chart in bordered .box card ---
    diff = (pt.result.conversion.treatment - pt.result.conversion.control) * 100
    conv_ci = (pt.result.conversion.ci[0] * 100, pt.result.conversion.ci[1] * 100)
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
            key="whatif_lift",
        )

    st.markdown(
        '<p class="cap">Drag the slider: the verdict moves from DO NOT SHIP to NEED MORE DATA to SHIP'
        " as the injected effect grows.</p>",
        unsafe_allow_html=True,
    )
