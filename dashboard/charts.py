"""Pure plotly figure builders. No streamlit imports, no I/O.

Every number plotted comes from a loaded dataclass — charts never compute
statistics, only draw them.
"""

import plotly.graph_objects as go

from dashboard import theme
from dashboard.data import ExperimentResult, MotivationStats, PreTrends, ScenarioResult


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
    result: ExperimentResult, title: str = "AOV lift (BRL) — 95% CI"
) -> go.Figure:
    """Unadjusted vs adjusted CI overlay; the bias story in one plot."""
    fig = go.Figure()
    _ci_row(fig, "unadjusted", result.aov.lift, result.aov.ci, theme.SLATE, 1.5)
    _ci_row(
        fig,
        "adjusted (ANCOVA)",
        result.aov_adjusted.lift,
        result.aov_adjusted.ci,
        theme.INK,
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
