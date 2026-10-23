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
            "Olist: about 99,000 real Brazilian e-commerce orders across 8 related tables. "
            "It is real and messy, yet large enough to power a simulated A/B test. "
            "Fully synthetic data would not show how the method copes with real order patterns."
        ),
    ),
    (
        "Method <b>ANCOVA-adjusted</b>",
        "",
        (
            "ANCOVA covariate adjustment on freight_value (correlation r=0.484 with order "
            "value, about 23% variance reduction: extra precision with no extra sample). "
            "CUPED was rejected because 97% of Olist customers buy only once, "
            "so there is no earlier history to subtract. An item-count covariate was "
            "viable but deferred."
        ),
    ),
    (
        "SIMULATED experiment",
        "sim",
        (
            "Olist has no real A/B-test column, so we simulate one: each customer is "
            "assigned to control or treatment by hashing their id with seed 42, then a "
            "labeled +5% effect is injected into treatment only. The injection is labeled "
            "everywhere, so it cannot be mistaken for a real lift. A null (no-injection) "
            "version is kept as an A/A sanity check."
        ),
    ),
    (
        "Metrics <b>Average order value · Conversion · Repeat purchase</b>",
        "",
        (
            "AOV (average order value) is the primary metric: it is continuous, sensitive "
            "(a change of about 2.45% is detectable), and is what the cap change targets. "
            "Conversion is a guardrail only: it sits near a 97% ceiling, so it is unfit as "
            "a headline. D7 (repeat purchase within 7 days) is exploratory. Rejected: "
            "conversion as primary (ceiling) and co-primary metrics (multiple-comparison cost)."
        ),
    ),
]


def render() -> None:
    """Emit the persistent project header (eyebrow, h1, subtitle, 4 chips).

    Fully static — no data argument needed; all copy is locked in the mockup.
    """
    # Build chip HTML
    chip_parts: list[str] = []
    for label_html, extra_class, data_def in _CHIPS:
        cls = f"pill {extra_class}".strip()
        safe_def = data_def.replace('"', "&quot;")
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
    split credit-card payments into more installments lift average order value
    without hurting conversion or repeat purchase? Includes covariate-adjusted
    inference, a power analysis, and a pre-registered difference-in-differences
    natural-experiment check.
  </p>
  <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:14px">
    {chips_html}
  </div>
</header>
"""
    st.markdown(header_html, unsafe_allow_html=True)
