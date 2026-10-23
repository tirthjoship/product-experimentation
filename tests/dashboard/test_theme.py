"""Tests for dashboard theme — verdict colors and plotly layout defaults."""

import pytest

from dashboard import theme


def test_verdict_colors_are_semantic() -> None:
    assert theme.verdict_color("SHIP") == theme.GREEN
    assert theme.verdict_color("DO NOT SHIP") == theme.RED
    assert theme.verdict_color("NEED MORE DATA") == theme.AMBER


def test_unknown_verdict_raises() -> None:
    with pytest.raises(ValueError, match="Unknown verdict"):
        theme.verdict_color("MAYBE")


def test_plotly_layout_merges_overrides() -> None:
    layout = theme.plotly_layout(title="x")
    assert layout["title"] == "x"
    assert layout["showlegend"] is False
    assert layout["paper_bgcolor"] == "white"


# v3 theme tests
def test_value_color_maps_classes() -> None:
    assert theme.value_color("good") == theme.GREEN
    assert theme.value_color("average") == theme.AMBER
    assert theme.value_color("poor") == theme.RED
    assert theme.value_color("neutral") == theme.INK


def test_verdict_color_still_works() -> None:
    assert theme.verdict_color("SHIP") == theme.GREEN


def test_css_imports_new_fonts() -> None:
    assert "Space+Grotesk" in theme.CSS
    assert "Inter" in theme.CSS


def test_author_footer_credit_line() -> None:
    out = theme.author_footer()
    assert "Built by Tirth Joshi" in out
    assert out.count('target="_blank" rel="noopener"') == 2
    assert "https://github.com/tirthjoship/product-experimentation" in out
    assert "https://linkedin.com/in/tirthjoshi" in out
