"""Pure plotly figure builders. No streamlit imports, no I/O.

Every number plotted comes from a loaded dataclass — charts never compute
statistics, only draw them.
"""

import math
from statistics import NormalDist

import plotly.graph_objects as go

from dashboard import theme
from dashboard.data import ExperimentResult, MotivationStats, PreTrends, ScenarioResult
from src.experiment.power import mde_mean


def bucket_bar(stats: MotivationStats) -> go.Figure:
    """AOV by installment bucket — the affordability gradient."""
    labels = [b.bucket for b in stats.buckets]
    values = [b.aov for b in stats.buckets]
    bar_width = 0.42 if len(labels) <= 2 else 0.6
    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker_color=theme.SLATE,
            width=[bar_width] * len(labels),
            text=[f"R${v:,.2f}" for v in values],
            textposition="outside",
            textfont={"family": theme.FONT_MONO, "size": 11},
            cliponaxis=False,
        )
    )
    fig.update_layout(
        **theme.plotly_layout(
            height=190,
            margin={"l": 56, "r": 16, "t": 26, "b": 34},
            bargap=0.55,
            xaxis={"gridcolor": "#fff"},
            yaxis={"title": "AOV (BRL)", "gridcolor": "#eef0f3"},
        )
    )
    return fig


def _ci_row(
    fig: go.Figure,
    label: str,
    lift: float,
    ci: tuple[float, float],
    color: str,
    thick: float,
) -> None:
    lo, hi = ci
    fig.add_trace(
        go.Scatter(
            x=[lift],
            y=[label],
            mode="markers",
            marker={"color": color, "size": 13},
            error_x={
                "type": "data",
                "symmetric": False,
                "array": [hi - lift],
                "arrayminus": [lift - lo],
                "color": color,
                "thickness": thick,
                "width": 8,
            },
            name=label,
        )
    )


def forest(
    result: ExperimentResult,
    title: str = "AOV lift (BRL) — 95% CI",
    adj_color: str = theme.INK,
) -> go.Figure:
    """Unadjusted vs adjusted CI overlay; the bias story in one plot.

    Pass ``adj_color`` (e.g. ``theme.GREEN``) to colour the adjusted-row marker
    with a verdict signal (SHIP / NEED MORE DATA / DO NOT SHIP).  Omitting it
    keeps the original ``theme.INK`` appearance — no visual change for existing
    callers.
    """
    fig = go.Figure()
    _ci_row(fig, "unadjusted", result.aov.lift, result.aov.ci, theme.SLATE, 1.5)
    _ci_row(
        fig,
        "adjusted (ANCOVA)",
        result.aov_adjusted.lift,
        result.aov_adjusted.ci,
        adj_color,
        3.5,
    )
    fig.add_vline(x=0.0, line_dash="dash", line_color=theme.RED, line_width=1)
    # Mockup keeps the forest clean: the variance-reduction and MDE callouts
    # live in the section captions, not painted over the plot (the inline
    # annotations overlapped the box header at the tight v3 height).
    # Compute x-range with 12% padding over all CI endpoints + 0
    all_x = [
        result.aov.ci[0],
        result.aov.ci[1],
        result.aov.lift,
        result.aov_adjusted.ci[0],
        result.aov_adjusted.ci[1],
        result.aov_adjusted.lift,
        0.0,
    ]
    lo, hi = min(all_x), max(all_x)
    pad = (hi - lo) * 0.12 or 1.0
    fig.update_layout(
        **theme.plotly_layout(
            height=150,
            xaxis={
                "title": "lift (BRL)",
                "range": [lo - pad, hi + pad],
                "zeroline": True,
                "zerolinecolor": "#c9ccd1",
                "gridcolor": "#eef0f3",
            },
            yaxis={"automargin": True, "gridcolor": "#eef0f3"},
        )
    )
    return fig


def coef_plot(pre: PreTrends) -> go.Figure:
    """Lead coefficients vs ±band — visual proof of the honest DiD rejection."""
    leads = sorted(pre.leads)
    values = [pre.leads[k] for k in leads]
    colors = [theme.RED if abs(v) > pre.band else theme.SLATE for v in values]
    fig = go.Figure(
        go.Scatter(
            x=leads,
            y=values,
            mode="markers+lines",
            marker={"color": colors, "size": 13},
            line={"color": theme.SLATE, "width": 1},
        )
    )
    fig.add_hrect(
        y0=-pre.band, y1=pre.band, fillcolor=theme.SLATE, opacity=0.12, line_width=0
    )
    fig.add_hline(y=0.0, line_dash="dash", line_color=theme.INK, line_width=1)
    # Wald-p / max-lead callout lives in the section caption (mockup-faithful);
    # the inline paper annotation overflowed the tight plot top and got clipped.
    fig.update_layout(
        **theme.plotly_layout(
            height=350,
            xaxis={
                "title": "weeks before boundary",
                "gridcolor": "#eef0f3",
                "zeroline": False,
            },
            yaxis={
                "title": "coefficient (delivery days)",
                "gridcolor": "#eef0f3",
                "zeroline": False,
            },
        )
    )
    return fig


def guardrail_plot(scenarios: list[ScenarioResult]) -> go.Figure:
    """Delivered-rate difference + CI per scenario, colored by verdict."""
    fig = go.Figure()
    for s in scenarios:
        g = s.result.conversion
        diff = g.treatment - g.control
        _ci_row(fig, s.scenario, diff, g.ci, theme.verdict_color(s.verdict), 2.0)
    fig.add_vline(x=0.0, line_dash="dash", line_color=theme.INK, line_width=1)
    fig.update_layout(
        **theme.plotly_layout(
            height=300,
            xaxis={
                "title": "treatment − control (delivered rate)",
                "gridcolor": "#eef0f3",
                "zeroline": False,
            },
            yaxis={"gridcolor": "#eef0f3", "zeroline": False},
        )
    )
    return fig


# ---------------------------------------------------------------------------
# v3 diversified builders
# ---------------------------------------------------------------------------


def dumbbell(label: str, control: float, treatment: float, fmt: str) -> go.Figure:
    """Single-row dumbbell: connector line + two endpoint markers with text labels."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[control, treatment],
            y=[label, label],
            mode="lines",
            line={"color": "#cdd2d8", "width": 3},
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[control],
            y=[label],
            mode="markers+text",
            marker={"size": 14, "color": theme.SLATE},
            text=["control"],
            textposition="top center",
            textfont={"family": theme.FONT_MONO, "size": 10, "color": theme.SLATE},
            cliponaxis=False,
            hovertemplate="control " + fmt.format(control) + "<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[treatment],
            y=[label],
            mode="markers+text",
            marker={"size": 14, "color": theme.GREEN},
            text=["treatment"],
            textposition="bottom center",
            textfont={"family": theme.FONT_MONO, "size": 10, "color": theme.GREEN},
            cliponaxis=False,
            hovertemplate="treatment " + fmt.format(treatment) + "<extra></extra>",
        )
    )
    # Pad the x-range so the endpoint dots sit INWARD — otherwise plotly fits the
    # range tightly to [control, treatment] and the centered "control"/"treatment"
    # labels overflow the plot edge and get clipped (esp. when the two values are
    # far apart). Combined with cliponaxis=False this keeps both labels inside.
    lo, hi = min(control, treatment), max(control, treatment)
    pad = (hi - lo) * 0.45 or (abs(hi) * 0.1 or 1.0)
    fig.update_layout(
        **theme.plotly_layout(
            height=130,
            showlegend=False,
            margin={"l": 56, "r": 56, "t": 16, "b": 30},
            xaxis={"range": [lo - pad, hi + pad], "gridcolor": "#eef0f3"},
            yaxis={"automargin": True, "gridcolor": "#fff"},
        )
    )
    return fig


def range_plot(rows: list[tuple[str, tuple[float, float], str]]) -> go.Figure:
    """Thick horizontal CI lines — one per row, coloured by caller."""
    fig = go.Figure()
    for label, ci, color in rows:
        fig.add_trace(
            go.Scatter(
                x=list(ci),
                y=[label, label],
                mode="lines",
                line={"color": color, "width": 6},
                hovertemplate=(
                    f"{label}: [{ci[0]:.2f}, {ci[1]:.2f}]"
                    f" width {ci[1] - ci[0]:.2f}<extra></extra>"
                ),
            )
        )
    # x-range with 10% padding over all CI endpoints
    all_x = [v for _, ci, _ in rows for v in ci]
    lo, hi = min(all_x), max(all_x)
    pad = (hi - lo) * 0.1
    fig.update_layout(
        **theme.plotly_layout(
            height=130,
            margin={"l": 86, "r": 20, "t": 12, "b": 32},
            xaxis={
                "title": "lift (BRL)",
                "range": [lo - pad, hi + pad],
                "gridcolor": "#eef0f3",
                "zeroline": True,
                "zerolinecolor": "#c9ccd1",
            },
            yaxis={"automargin": True, "gridcolor": "#fff"},
        )
    )
    return fig


def split_bar(parts: list[tuple[str, float, str]]) -> go.Figure:
    """100%-stacked horizontal bar decomposed into named segments."""
    total = sum(v for _, v, _ in parts)
    fig = go.Figure()
    for name, val, color in parts:
        fig.add_trace(
            go.Bar(
                x=[val],
                y=[""],
                name=name,
                orientation="h",
                marker_color=color,
                text=[
                    f"{name} {val:,.0f} ({(100 * val / total if total else 0.0):.1f}%)"
                ],
                textposition="inside",
                insidetextanchor="middle",
                textfont={"color": "white", "family": theme.FONT_MONO},
            )
        )
    fig.update_layout(
        **theme.plotly_layout(
            height=86,
            showlegend=False,
            barmode="stack",
            margin={"l": 10, "r": 10, "t": 8, "b": 18},
            xaxis={"visible": False},
            yaxis={"visible": False},
        )
    )
    return fig


def diverging_marker(value: float, band: float, unit: str) -> go.Figure:
    """Diamond marker on a symmetric band — shows how far a gap sits from zero."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[-band, band],
            y=["", ""],
            mode="lines",
            line={"color": "#e0c9cc", "width": 14},
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[value],
            y=[""],
            mode="markers+text",
            marker={"size": 16, "color": theme.ACCENT, "symbol": "diamond"},
            text=[f"{value:.3f} {unit}"],
            textposition="top center",
            textfont={"family": theme.FONT_MONO, "size": 11},
            cliponaxis=False,
            hovertemplate=f"gap {value:.3f}<extra></extra>",
        )
    )
    # Range spans the band and the marker, padded so the centered value label
    # (which may sit at/beyond the band edge) never clips the plot edge.
    span = max(band, abs(value))
    pad = span * 0.35 or 1.0
    fig.update_layout(
        **theme.plotly_layout(
            height=96,
            showlegend=False,
            margin={"l": 24, "r": 24, "t": 24, "b": 24},
            xaxis={
                "range": [-span - pad, span + pad],
                "zeroline": True,
                "zerolinecolor": "#9aa0a8",
                "zerolinewidth": 1.5,
                "gridcolor": "#f2f3f5",
            },
            yaxis={"visible": False},
        )
    )
    return fig


def lift_forest(
    label: str, est: float, ci: tuple[float, float], color: str
) -> go.Figure:
    """Single-row forest plot with asymmetric error bar and zeroline."""
    fig = go.Figure(
        go.Scatter(
            x=[est],
            y=[label],
            mode="markers",
            marker={"size": 11, "color": color},
            error_x={
                "type": "data",
                "symmetric": False,
                "array": [ci[1] - est],
                "arrayminus": [est - ci[0]],
                "color": color,
                "thickness": 2,
                "width": 7,
            },
            hovertemplate=(
                f"{label}: %{{x:.2f}}<br>CI [{ci[0]:.2f}, {ci[1]:.2f}]<extra></extra>"
            ),
        )
    )
    lo = min(ci[0], est, 0.0)
    hi = max(ci[1], est, 0.0)
    pad = (hi - lo) * 0.12 or 1.0
    fig.update_layout(
        **theme.plotly_layout(
            height=150,
            xaxis={
                "title": "lift",
                "range": [lo - pad, hi + pad],
                "zeroline": True,
                "zerolinecolor": "#c9ccd1",
                "gridcolor": "#eef0f3",
            },
            yaxis={"automargin": True, "gridcolor": "#eef0f3"},
        )
    )
    return fig


def _power_at(effect: float, sd: float, n: int, alpha: float) -> float:
    """Compute power for a two-sided z-test."""
    z = NormalDist().inv_cdf(1 - alpha / 2)
    se = sd * math.sqrt(2 / n)
    nd = NormalDist()
    return 1 - nd.cdf(z - abs(effect) / se) + nd.cdf(-z - abs(effect) / se)


def mde_vs_n(sd: float, alpha: float, power: float, n_current: int) -> go.Figure:
    """MDE curve vs sample size with a marker at the current n."""
    ns = list(range(4000, 80001, 4000))
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=ns,
            y=[mde_mean(sd, n, alpha, power) for n in ns],
            mode="lines",
            line={"color": theme.SLATE, "width": 2},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[n_current],
            y=[mde_mean(sd, n_current, alpha, power)],
            mode="markers",
            marker={"size": 11, "color": theme.ACCENT},
        )
    )
    fig.update_layout(
        **theme.plotly_layout(
            height=220,
            xaxis={"title": "n per arm", "gridcolor": "#eef0f3", "zeroline": False},
            yaxis={"title": "MDE (BRL)", "gridcolor": "#eef0f3", "zeroline": False},
        )
    )
    return fig


def power_vs_effect(sd: float, alpha: float, n: int) -> go.Figure:
    """Power curve vs true effect size with an 80% target reference line."""
    effs = [e / 2 for e in range(0, 31)]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=effs,
            y=[_power_at(e, sd, n, alpha) for e in effs],
            mode="lines",
            line={"color": theme.ACCENT, "width": 2},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[0, 15],
            y=[0.8, 0.8],
            mode="lines",
            line={"color": "#C9CCD1", "width": 1, "dash": "dot"},
            hoverinfo="skip",
        )
    )
    fig.update_layout(
        **theme.plotly_layout(
            height=220,
            xaxis={
                "title": "true effect (BRL)",
                "gridcolor": "#eef0f3",
                "zeroline": False,
            },
            yaxis={"title": "power", "gridcolor": "#eef0f3", "zeroline": False},
        )
    )
    return fig
