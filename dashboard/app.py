"""Tab shell. Per-section isolation: one broken section never kills the page.

Loaders are wrapped in st.cache_data HERE (not in data.py) so data.py stays
pure and fixture-testable. Cached returns are frozen dataclasses of plain
primitives — safe for Streamlit's serialized cache.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

# Streamlit (incl. Community Cloud) prepends the *script* directory
# (dashboard/) to sys.path — not the repo root. Absolute imports like
# `from dashboard import …` / `from src…` therefore fail unless the root
# is on the path. Local `pip install -e .` masks this; Cloud does not.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import streamlit as st  # noqa: E402

from dashboard import data, theme  # noqa: E402
from dashboard.sections import (  # noqa: E402
    calculator,
    did,
    header,
    overview,
    results,
    scenarios,
    whatif,
)

st.set_page_config(
    page_title="Olist Product Experimentation", page_icon="📋", layout="wide"
)
st.markdown(theme.CSS, unsafe_allow_html=True)

_experiment = st.cache_data(data.load_experiment)
_scenarios = st.cache_data(data.load_scenarios)
_motivation = st.cache_data(data.load_motivation)
_did = st.cache_data(data.load_did)
_grid = st.cache_data(data.load_grid)


def _render(name: str, fn: Callable[[], None]) -> None:
    """Fail loud per section; siblings survive."""
    try:
        fn()
    except FileNotFoundError as exc:
        st.error(
            f"Section '{name}': {exc} — regenerate the report "
            "(`make experiment` / `scenarios` / `motivation` / `did-feasibility`)."
        )
    except (data.ReportSchemaError, ValueError) as exc:
        st.error(f"Section '{name}': schema error — {exc}")


_render("header", header.render)

overview_t, results_t, scenarios_t, power_t, did_t = st.tabs(
    [
        "Overview",
        "Experiment results",
        "Scenario explorer",
        "Power & design",
        "Natural experiment",
    ]
)

with overview_t:
    _render(
        "overview", lambda: overview.render(_experiment(), _scenarios(), _motivation())
    )

with results_t:
    _render("results", lambda: results.render(_scenarios()))

with scenarios_t:
    _render("scenarios", lambda: scenarios.render(_scenarios()))
    _render("whatif", lambda: whatif.render(_grid()))

with power_t:
    _render("calculator", lambda: calculator.render(_experiment()))

with did_t:
    _render("did", lambda: did.render(_did()))
