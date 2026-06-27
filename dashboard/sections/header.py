"""Persistent project header: eyebrow, title, subtitle, and 5 context chips.

Render-only — coverage omitted (no unit tests per project convention for
sections).  All copy is verbatim from docs/mockups/dashboard-v3/index.html
(the LOCKED source of truth).  No live data argument needed: every chip label
and tooltip is static text drawn from the mockup.
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Chip definitions — verbatim from mockup <header class="proj"> chips block.
# Each tuple: (label_html, extra_css_class, data_def_text)
# extra_css_class is "" | "sim" | "go" — matches .pill variants in theme.py CSS.
# ---------------------------------------------------------------------------
_CHIPS: list[tuple[str, str, str]] = [
    (
        "Dataset <b>Olist · 99,092 orders</b>",
        "",
        (
            "Olist — ~99k real Brazilian e-commerce orders across 8 relational tables. "
            "Chosen over DataCo (weak semantics, already used in a sibling repo) and "
            "fully-synthetic data (not credible for a portfolio). Real and messy, yet big "
            "enough to power a simulated A/B."
        ),
    ),
    (
        "Method <b>ANCOVA-adjusted</b>",
        "",
        (
            "ANCOVA covariate adjustment on freight_value (correlation r=0.484 with order "
            "value → ~23% variance reduction — free precision, no extra sample). Chosen "
            "over CUPED, which we rejected because 97% of Olist customers buy only once, "
            "so there is no pre-period history to subtract. An item-count covariate was "
            "viable but deferred."
        ),
    ),
    (
        "SIMULATED experiment",
        "sim",
        (
            "Olist has no real A/B-test column, so we simulate one: assign each customer "
            "to control/treatment by hashing their id with seed 42, then inject a labeled "
            "+5% effect into treatment only. Honest by construction — a reader can never "
            "mistake it for a real lift. A null (no-injection) version is kept as an A/A "
            "sanity check."
        ),
    ),
    (
        "Metrics <b>AOV · Conversion · D7</b>",
        "",
        (
            "AOV (average order value) is the primary metric — continuous, sensitive "
            "(detectable at ~2.45%), and exactly what the cap change targets. Conversion "
            "is a guardrail only: it sits near a 97% ceiling, so it is unfit as a "
            "headline. D7 repeat-purchase is exploratory. Rejected: conversion-primary "
            "(ceiling) and co-primary (multiple-comparison cost)."
        ),
    ),
    (
        "Plans 1–4 shipped",
        "go",
        (
            "Plans 1–4 are merged to main: inference depth, covariate adjustment, the "
            "installment product narrative + PM memo, and the DiD natural-experiment "
            "honest rejection. This dashboard (Plan 5) reads only their committed report "
            "outputs — it never recomputes."
        ),
    ),
]


def render() -> None:
    """Emit the persistent project header (eyebrow, h1, subtitle, 5 chips).

    Fully static — no data argument needed; all copy is locked in the mockup.
    """
    # Build chip HTML
    chip_parts: list[str] = []
    for label_html, extra_class, data_def in _CHIPS:
        cls = f"pill {extra_class}".strip()
        # Escape single quotes in data-def for safe HTML attribute embedding
        safe_def = data_def.replace("'", "&#39;")
        chip_parts.append(
            f'<span class="{cls}" data-def="{safe_def}">{label_html}</span>'
        )
    chips_html = "\n    ".join(chip_parts)

    header_html = f"""
<header style="padding:26px 0 18px;border-bottom:1px solid #eaecef;margin-bottom:4px">
  <div class="section-label" style="border-top:none;padding-top:0;margin-top:0;margin-bottom:6px">
    Product Experimentation · Olist E-Commerce
  </div>
  <h1 style="font-family:'Space Grotesk',system-ui,sans-serif;font-size:2.1rem;
             font-weight:700;letter-spacing:-0.02em;margin:6px 0 6px;color:#0d0f12">
    Should we raise the installment cap from 6× to 10×?
  </h1>
  <p style="color:#6b727b;font-size:14.5px;max-width:760px;margin:0">
    A simulated A/B test on Brazilian e-commerce orders: does letting customers
    split credit-card payments into more installments lift average order value —
    without hurting conversion or repeat purchase? With covariate-adjusted
    inference, a power analysis, and a pre-registered difference-in-differences
    natural-experiment check.
  </p>
  <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:14px">
    {chips_html}
  </div>
</header>
"""
    st.markdown(header_html, unsafe_allow_html=True)
