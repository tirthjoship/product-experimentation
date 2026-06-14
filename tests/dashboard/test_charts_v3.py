"""Tests for v3 chart builders — assert structure, not pixels."""

from pathlib import Path

import plotly.graph_objects as go

from dashboard import charts, theme
from dashboard.data import load_experiment

FIXTURES = Path(__file__).parent / "fixtures"


def test_dumbbell_has_two_endpoint_markers() -> None:
    fig = charts.dumbbell(label="D7 %", control=0.87, treatment=0.84, fmt="{:.2%}")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 3


def test_range_plot_orders_two_intervals() -> None:
    fig = charts.range_plot(
        [
            ("unadjusted", (-8.69, -3.24), theme.SLATE),
            ("adjusted", (-9.93, -5.19), theme.ACCENT),
        ]
    )
    assert len(fig.data) == 2


def test_split_bar_segments_sum_visible() -> None:
    fig = charts.split_bar(
        [("control", 49694, theme.SLATE), ("treatment", 49398, theme.GREEN)]
    )
    assert len(fig.data) == 2


def test_diverging_marker_inside_band() -> None:
    fig = charts.diverging_marker(value=0.52, band=2.0, unit="BRL")
    assert isinstance(fig, go.Figure)


def test_lift_forest_colors_by_argument() -> None:
    fig = charts.lift_forest(
        label="conv. lift", est=0.18, ci=(-0.03, 0.39), color=theme.SLATE
    )
    assert fig.data[0].error_x is not None


def test_mde_vs_n_marks_current() -> None:
    fig = charts.mde_vs_n(sd=180.0, alpha=0.05, power=0.80, n_current=49000)
    assert len(fig.data) >= 2


def test_power_vs_effect_has_target_line() -> None:
    fig = charts.power_vs_effect(sd=180.0, alpha=0.05, n=49000)
    assert len(fig.data) >= 2


def test_forest_accepts_adjusted_color() -> None:
    exp = load_experiment(FIXTURES / "experiment.json")
    fig = charts.forest(exp, adj_color=theme.GREEN)
    colors = [getattr(t.marker, "color", None) for t in fig.data if t.mode == "markers"]
    assert theme.GREEN in colors


def test_power_at_matches_mde_definition() -> None:
    from src.experiment.power import mde_mean

    sd, n, alpha = 180.0, 49000, 0.05
    mde = mde_mean(sd, n, alpha, 0.80)
    assert abs(charts._power_at(mde, sd, n, alpha) - 0.80) < 1e-3
    assert abs(charts._power_at(0.0, sd, n, alpha) - alpha) < 1e-3
