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
    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker_color=theme.SLATE,
            text=[f"R${v:,.2f}" for v in values],
            textposition="outside",
            textfont={"family": theme.FONT_MONO, "size": 13},
        )
    )
    fig.update_layout(
        **theme.plotly_layout(
            title="AOV by installment bucket (descriptive, not causal)",
            xaxis_title="installments per order",
            yaxis_title="AOV (BRL)",
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
    shrink = round((1.0 - result.aov_adjusted.ci_width_ratio) * 100)
    fig.add_annotation(
        text=f"adjusted CI {shrink}% tighter (ratio {result.aov_adjusted.ci_width_ratio:.3f}"
        " ≈ √(1−r²) optimum)",
        xref="paper",
        yref="paper",
        x=0.99,
        y=1.12,
        showarrow=False,
        font={"family": theme.FONT_MONO, "size": 12, "color": theme.SLATE},
    )
    fig.add_annotation(
        text=f"MDE ≥ R${result.mde_aov:.2f} at α={result.alpha}",
        xref="paper",
        yref="paper",
        x=0.99,
        y=1.04,
        showarrow=False,
        font={"family": theme.FONT_MONO, "size": 12, "color": theme.SLATE},
    )
    fig.update_layout(
        **theme.plotly_layout(title=title, xaxis_title="lift (BRL)", height=300)
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
    fig.add_annotation(
        text=f"Wald p = {pre.wald_p:.3f} (gate needs > 0.10) · max |lead| = "
        f"{pre.max_lead_abs:.2f} > band {pre.band:.2f}",
        xref="paper",
        yref="paper",
        x=0.99,
        y=1.08,
        showarrow=False,
        font={"family": theme.FONT_MONO, "size": 12, "color": theme.RED},
    )
    fig.update_layout(
        **theme.plotly_layout(
            title="Pre-trends: lead coefficients (treated − control)",
            xaxis_title="weeks before boundary",
            yaxis_title="coefficient (delivery days)",
            height=350,
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
            title="Guardrail: delivered-rate difference — 95% CI",
            xaxis_title="treatment − control (delivered rate)",
            height=300,
        )
    )
    return fig


# ---------------------------------------------------------------------------
# v3 diversified builders
# ---------------------------------------------------------------------------


def dumbbell(label: str, control: float, treatment: float, fmt: str) -> go.Figure:
    """Single-row dumbbell: connector line + two endpoint markers."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[control, treatment],
            y=[label, label],
            mode="lines",
            line={"color": "#CDD2D8", "width": 3},
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[control],
            y=[label],
            mode="markers",
            marker={"size": 14, "color": theme.SLATE},
            hovertemplate="control " + fmt.format(control) + "<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[treatment],
            y=[label],
            mode="markers",
            marker={"size": 14, "color": theme.GREEN},
            hovertemplate="treatment " + fmt.format(treatment) + "<extra></extra>",
        )
    )
    fig.update_layout(**theme.plotly_layout(height=130, showlegend=False))
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
    fig.update_layout(**theme.plotly_layout(height=130, xaxis_title="lift (BRL)"))
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
                text=[f"{name} {val:,.0f} ({100 * val / total:.1f}%)"],
                textposition="inside",
                insidetextanchor="middle",
                textfont={"color": "white", "family": theme.FONT_MONO},
            )
        )
    fig.update_layout(
        barmode="stack", **theme.plotly_layout(height=86, showlegend=False)
    )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def diverging_marker(value: float, band: float, unit: str) -> go.Figure:
    """Diamond marker on a symmetric band — shows how far a gap sits from zero."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[-band, band],
            y=["", ""],
            mode="lines",
            line={"color": "#E0C9CC", "width": 14},
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
            hovertemplate=f"gap {value:.3f}<extra></extra>",
        )
    )
    fig.update_layout(**theme.plotly_layout(height=96, showlegend=False))
    fig.update_yaxes(visible=False)
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
    fig.update_layout(**theme.plotly_layout(height=150, xaxis_title="lift"))
    fig.update_xaxes(zeroline=True)
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
            height=220, xaxis_title="n per arm", yaxis_title="MDE (BRL)"
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
            height=220, xaxis_title="true effect (BRL)", yaxis_title="power"
        )
    )
    return fig
