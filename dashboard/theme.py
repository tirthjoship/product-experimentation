"""Visual constants and plotly defaults — 'company feel, not AI wallpaper'.

v3 palette: white paper, Space Grotesk (display), Inter (body),
IBM Plex Mono (numbers/code), oxblood accent (#7A1F2B).
Color carries meaning ONLY: verdict/value colors are semantic; everything else is ink.
"""

from typing import Any

# ---------------------------------------------------------------------------
# Palette — v3 (white paper, oxblood accent)
# ---------------------------------------------------------------------------
PAPER = "#FFFFFF"
CARD_BORDER = "#EAECEF"
INK = "#0D0F12"
SLATE = "#5C6B7A"
GREEN = "#2F7D4F"
RED = "#B3261E"
AMBER = "#B7791F"
ACCENT = "#7A1F2B"  # oxblood

# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------
FONT_BODY = "Inter, sans-serif"
FONT_DISPLAY = "Space Grotesk, sans-serif"
FONT_MONO = "IBM Plex Mono, monospace"

# ---------------------------------------------------------------------------
# Verdict → color (existing API — unchanged callers)
# ---------------------------------------------------------------------------
_VERDICT_COLORS = {"SHIP": GREEN, "DO NOT SHIP": RED, "NEED MORE DATA": AMBER}

# ---------------------------------------------------------------------------
# Value class → color (v3 addition)
# ---------------------------------------------------------------------------
_VALUE_COLORS: dict[str, str] = {
    "good": GREEN,
    "average": AMBER,
    "poor": RED,
    "neutral": INK,
}


def value_color(cls: str) -> str:
    """Map a valuecolor class string to its CSS color."""
    return _VALUE_COLORS.get(cls, INK)


# ---------------------------------------------------------------------------
# CSS — v3 stylesheet (Google Fonts + Streamlit overrides + component classes)
# Tooltip mechanism: ::after reads attr(data-def) on .ci / .term / .pill[data-def]
# Responsive: no horizontal scroll, charts max-width:100%, grids collapse on narrow.
# ---------------------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

/* ---- root variables ---- */
:root {
  --bg: #ffffff; --ink: #0d0f12; --muted: #6b727b; --line: #eaecef;
  --soft: #f6f7f9; --green: #2f7d4f; --red: #b3261e; --amber: #b7791f;
  --slate: #5c6b7a; --accent: #7a1f2b;
  --head: 'Space Grotesk', system-ui, sans-serif;
  --body: 'Inter', system-ui, sans-serif;
  --mono: 'IBM Plex Mono', ui-monospace, monospace;
}

/* ---- base ---- */
*, *::before, *::after { box-sizing: border-box; }
.stApp { background-color: #ffffff; overflow-x: hidden; }
html, body, p, li, label, div {
  font-family: 'Inter', system-ui, sans-serif;
  color: #0d0f12;
}

/* ---- headings ---- */
h1, h2, h3, h4 {
  font-family: 'Space Grotesk', system-ui, sans-serif;
  letter-spacing: -0.02em;
  color: #0d0f12;
}

/* ---- monospace: numbers + code ---- */
code, pre, .stCode { font-family: 'IBM Plex Mono', ui-monospace, monospace; }

/* ---- section label (kicker style) ---- */
.section-label {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.75rem;
  letter-spacing: 0.14em;
  color: #7a1f2b;           /* oxblood — v3 replaces slate */
  text-transform: uppercase;
  border-top: 1px solid #eaecef;
  padding-top: 14px;
  margin: 22px 0 10px;
}
.section-label:first-of-type { border-top: none; padding-top: 0; margin-top: 4px; }

/* ---- takeaway (bottom-line tile) ---- */
.takeaway {
  border: 1px solid #eaecef;
  border-left: 4px solid #7a1f2b;
  background: linear-gradient(180deg, #fcf8f8, #fff);
  border-radius: 10px;
  padding: 16px 20px;
  margin: 4px 0 14px;
}
.takeaway .lab {
  font: 600 11px 'IBM Plex Mono', monospace;
  letter-spacing: .16em;
  text-transform: uppercase;
  color: #7a1f2b;
}
.takeaway .q {
  font: 600 17px/1.3 'Space Grotesk', system-ui, sans-serif;
  margin: 6px 0 8px;
}
.takeaway .verdline {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 8px; flex-wrap: wrap;
}
.takeaway .verdline .answer { font-weight: 600; }
.takeaway p { margin: 0; font-size: 13.5px; color: #3a4047; max-width: 840px; }
.takeaway .num { font-weight: 600; color: #0d0f12; }

/* ---- value color classes ---- */
.v-good  { color: #2f7d4f !important; }
.v-average { color: #b7791f !important; }
.v-avg   { color: #b7791f !important; }
.v-poor  { color: #b3261e !important; }
.v-bad   { color: #b3261e !important; }
.v-neutral { color: #0d0f12 !important; }
.v-neu   { color: #0d0f12 !important; }

/* ---- vtag (inline verdict badge) ---- */
.vtag {
  font: 600 10px 'IBM Plex Mono', monospace;
  letter-spacing: .08em;
  text-transform: uppercase;
  padding: 1px 7px;
  border-radius: 10px;
  margin-left: 7px;
  vertical-align: middle;
}
.vtag.good { background: #e3f3e9; color: #2f7d4f; }
.vtag.avg, .vtag.average { background: #f8edd6; color: #b7791f; }
.vtag.bad, .vtag.poor { background: #f9e2e0; color: #b3261e; }

/* ---- pill (context chip with optional tooltip) ---- */
.pill {
  font: 500 12px 'IBM Plex Mono', monospace;
  background: #f6f7f9;
  border: 1px solid #eaecef;
  border-radius: 20px;
  padding: 4px 11px;
  color: #48505a;
  position: relative;
  display: inline-block;
}
.pill b { color: #0d0f12; }
.pill.sim { background: #f6f6cf; border-color: #e3e0a0; color: #5b5b2c; }
.pill.go  { background: #e3f3e9; border-color: #bfe3cd; color: #2f7d4f; }
.pill[data-def] { cursor: help; }
.pill[data-def]::before { content: 'ⓘ'; margin-right: 5px; opacity: .5; font-size: 10px; }
.pill[data-def]:hover::after {
  content: attr(data-def);
  position: absolute; left: 0; top: 2em; z-index: 30;
  background: #111; color: #fff;
  font: 400 12px/1.5 'Inter', system-ui, sans-serif;
  width: 320px; padding: 11px 13px; border-radius: 9px;
  white-space: normal; box-shadow: 0 8px 26px rgba(0,0,0,.3);
  text-transform: none; letter-spacing: 0;
}

/* ---- chip (verdict badge) ---- */
.chip {
  display: inline-block;
  padding: 4px 13px;
  border-radius: 20px;
  font-weight: 700;
  font-size: 14px;
}
.chip.ship { background: #e3f3e9; color: #2f7d4f; }
.chip.no   { background: #f9e2e0; color: #b3261e; }
.chip.more { background: #f8edd6; color: #b7791f; }

/* ---- ci (chart-info ⓘ icon with hover tooltip) ---- */
.ci {
  display: inline-flex;
  align-items: center; justify-content: center;
  width: 15px; height: 15px;
  border-radius: 50%;
  border: 1px solid #c2c7cd;
  color: #8b919a;
  font: 600 10px 'Inter', system-ui, sans-serif;
  font-style: normal;
  cursor: help;
  position: relative;
  margin-left: 5px;
  vertical-align: middle;
}
.ci:hover { border-color: #7a1f2b; color: #7a1f2b; }
.ci:hover::after {
  content: attr(data-def);
  position: absolute; left: 0; top: 1.7em; z-index: 30;
  background: #111; color: #fff;
  font: 400 12px/1.5 'Inter', system-ui, sans-serif;
  width: 280px; padding: 10px 12px; border-radius: 9px;
  white-space: normal; box-shadow: 0 8px 24px rgba(0,0,0,.3);
}

/* ---- term (glossary hover span) ---- */
.term {
  border-bottom: 1px dotted currentColor;
  cursor: help;
  position: relative;
}
.term:hover::after {
  content: attr(data-def);
  position: absolute; left: 0; top: 1.5em; z-index: 20;
  background: #111; color: #fff;
  font: 400 12px/1.4 'Inter', system-ui, sans-serif;
  width: 260px; padding: 8px 11px; border-radius: 8px;
  white-space: normal; box-shadow: 0 6px 20px rgba(0,0,0,.28);
}

/* ---- responsive: no horizontal scroll ---- */
.js-plotly-plot, .plot-container { max-width: 100% !important; }
.stPlotlyChart { min-width: 0; overflow: hidden; }
.stColumns > div, [data-testid="column"] { min-width: 0; overflow: hidden; }

@media (max-width: 720px) {
  .stColumns { flex-direction: column !important; }
  .stColumns > div { min-width: 100% !important; }
}
@media (max-width: 600px) {
  .stApp { padding: 0 8px; }
  h1 { font-size: 24px !important; }
  h2 { font-size: 20px !important; }
}
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
        "margin": {"l": 60, "r": 30, "t": 50, "b": 44},
        "showlegend": False,
    }
    base.update(overrides)
    return base
