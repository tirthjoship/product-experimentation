"""Tab shell. Per-section isolation: one broken section never kills the page.

Loaders are wrapped in st.cache_data HERE (not in data.py) so data.py stays
pure and fixture-testable. Cached returns are frozen dataclasses of plain
primitives — safe for Streamlit's serialized cache.
"""

from collections.abc import Callable

import streamlit as st

from dashboard import data, theme
from dashboard.sections import (
    did,
    guardrail,
    hero,
    motivation,
    notes,
    results,
    scenarios,
)

st.set_page_config(
    page_title="Olist Product Experimentation", page_icon="📋", layout="wide"
)
st.markdown(theme.CSS, unsafe_allow_html=True)

_experiment = st.cache_data(data.load_experiment)
_scenarios = st.cache_data(data.load_scenarios)
_motivation = st.cache_data(data.load_motivation)
_did = st.cache_data(data.load_did)


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


def _headline_verdict() -> str:
    """Hero verdict is READ from the 'large' scenario in scenarios JSON —
    experiment_001.json carries no verdict field and we never recompute one."""
    large = next(s for s in _scenarios() if s.scenario == "large")
    return large.verdict


story_tab, interactive_tab = st.tabs(["Story", "Interactive"])

with story_tab:
    _render("hero", lambda: hero.render(_experiment(), _headline_verdict()))
    st.divider()
    _render("motivation", lambda: motivation.render(_motivation()))
    st.divider()
    _render("notes", notes.render)
    st.divider()
    _render("results", lambda: results.render(_scenarios()))
    st.divider()
    _render("did", lambda: did.render(_did()))

with interactive_tab:
    _render("scenarios", lambda: scenarios.render(_scenarios()))
    st.divider()
    _render("guardrail", lambda: guardrail.render(_scenarios()))
