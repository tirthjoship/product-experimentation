"""Visual constants and plotly defaults — 'lab notebook meets financial terminal'.

Color carries meaning ONLY: verdict colors are semantic; everything else is ink.
"""

from typing import Any

PAPER = "#FAF8F3"
CARD_BORDER = "#E5E0D5"
INK = "#1A1A1A"
SLATE = "#5A6B7B"
GREEN = "#2E7D4F"
RED = "#C0392B"
AMBER = "#C99A2E"

FONT_BODY = "Source Sans 3, sans-serif"
FONT_DISPLAY = "Fraunces, serif"
FONT_MONO = "IBM Plex Mono, monospace"

_VERDICT_COLORS = {"SHIP": GREEN, "DO NOT SHIP": RED, "NEED MORE DATA": AMBER}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600&family=Source+Sans+3:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap');
.stApp { background-color: #FAF8F3; }
html, body, p, li, label { font-family: 'Source Sans 3', sans-serif; color: #1A1A1A; }
h1, h2, h3 { font-family: 'Fraunces', serif; color: #1A1A1A; }
code { font-family: 'IBM Plex Mono', monospace; }
.section-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem;
  letter-spacing: 0.12em; color: #5A6B7B; text-transform: uppercase; }
</style>
"""


def verdict_color(verdict: str) -> str:
    """Map a verdict string (read from reports JSON) to its semantic color."""
    try:
        return _VERDICT_COLORS[verdict]
    except KeyError:
        raise ValueError(f"Unknown verdict: {verdict!r}") from None


def plotly_layout(**overrides: Any) -> dict[str, Any]:
    """Base plotly layout: white card, body font, no legend, no clutter."""
    base: dict[str, Any] = {
        "paper_bgcolor": "white",
        "plot_bgcolor": "white",
        "font": {"family": FONT_BODY, "color": INK, "size": 14},
        "margin": {"l": 70, "r": 40, "t": 60, "b": 50},
        "showlegend": False,
    }
    base.update(overrides)
    return base
