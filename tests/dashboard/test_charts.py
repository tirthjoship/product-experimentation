"""Chart builder tests — presence-level only (no trace-geometry internals)."""

from pathlib import Path

import plotly.graph_objects as go

from dashboard import charts
from dashboard.data import load_did, load_experiment, load_motivation, load_scenarios

FIXTURES = Path(__file__).parent / "fixtures"


def test_bucket_bar_returns_figure_with_all_buckets() -> None:
    stats = load_motivation(FIXTURES / "motivation.json")
    fig = charts.bucket_bar(stats)
    assert isinstance(fig, go.Figure)
    assert list(fig.data[0].x) == ["1", "2-3", "4-6", "7+"]


def test_forest_has_two_rows_zero_line_and_annotations() -> None:
    exp = load_experiment(FIXTURES / "experiment.json")
    fig = charts.forest(exp)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2  # unadjusted + adjusted
    assert len(fig.layout.shapes) >= 1  # zero line
    texts = " ".join(a.text for a in fig.layout.annotations)
    assert "tighter" in texts  # variance-reduction callout
    assert "MDE" in texts  # power callout


def test_coef_plot_has_band_and_flags_violating_lead() -> None:
    did = load_did(FIXTURES / "did.json")
    fig = charts.coef_plot(did.pretrends)
    assert isinstance(fig, go.Figure)
    assert len(fig.layout.shapes) >= 2  # band rect + zero line
    colors = list(fig.data[0].marker.color)
    # fixture leads: {-5: -2.48, -4: -1.32, -3: -0.83, -2: 3.4}, band=1.93
    # TWO leads exceed the band: -5 (abs=2.48) and -2 (abs=3.4)
    assert colors.count("#C0392B") == 2  # both -5 and -2 break band 1.93


def test_guardrail_plot_one_row_per_scenario() -> None:
    scenarios = load_scenarios(FIXTURES / "scenarios.json")
    fig = charts.guardrail_plot(scenarios)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 3
