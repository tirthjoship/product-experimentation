"""Power & design tab — analytical calculator.

This section is a CALCULATOR: closed-form power math only.
It never loads data from reports directly — all real-world defaults are
seeded from the ``ExperimentResult`` dataclass that is passed in.

Layout (top → bottom)
---------------------
1. CALCULATOR banner (simbar style) — verbatim from mockup
2. Bottom-line takeaway tile ("Yes — for effects above ~R$X")
3. Sliders: n per arm / α / SD / power (SD default seeded from report)
4. Output row: MDE · CI half-width · power@observed (colored by power_class)
5. Two-column chart row: mde_vs_n + power_vs_effect (each with ⓘ)
6. Footer caption

SD derivation
-------------
``ExperimentResult`` has no ``sd`` field.  SD is back-solved from the
committed ``mde_aov`` via the inverse of ``mde_mean``::

    mde_mean(sd, n, alpha, power) = (z_alpha + z_power) * sd * sqrt(2/n)
    → sd = mde_aov / ((z_alpha + z_power) * sqrt(2/n))

This uses ``n_control`` and ``alpha`` from the same report, at 80% power.
The result (≈ 243 BRL for the large scenario) is the slider's DEFAULT — a
user can drag it anywhere; the calculator label makes clear the number is
analytical, not a new statistic.

Observed effect
---------------
``aov_adjusted.lift`` from the passed experiment (large scenario base,
8.63 BRL) is used as the reference for ``power@observed``.
"""

from __future__ import annotations

import math
from statistics import NormalDist

import streamlit as st

from dashboard import charts, glossary, valuecolor
from dashboard.data import ExperimentResult
from dashboard.sections import _ui
from src.experiment.power import mde_mean

# ---------------------------------------------------------------------------
# Internal helpers (pure — no I/O, no st)
# ---------------------------------------------------------------------------

_ND = NormalDist()


def _ci_half_width(sd: float, n: int, alpha: float) -> float:
    """Half-width of the two-sample 95% CI: z_(alpha/2) * SD * sqrt(2/n)."""
    z = _ND.inv_cdf(1 - alpha / 2)
    return z * sd * math.sqrt(2 / n)


def _seed_sd(result: ExperimentResult) -> float:
    """Back-solve SD from the committed mde_aov.

    mde_mean(sd, n, alpha, power) = (z_a + z_b) * sd * sqrt(2/n)
    → sd = mde_aov / ((z_a + z_b) * sqrt(2/n))

    Uses n_control and alpha from the dataclass; power fixed at 0.80.
    """
    z_a = _ND.inv_cdf(1 - result.alpha / 2)
    z_b = _ND.inv_cdf(0.80)
    return result.mde_aov / ((z_a + z_b) * math.sqrt(2 / result.n_control))


# ---------------------------------------------------------------------------
# Public render function
# ---------------------------------------------------------------------------


def render(experiment: ExperimentResult) -> None:
    """Render the Power & design tab.

    Parameters
    ----------
    experiment:
        The base experiment result (``load_experiment()`` — the large scenario
        base file).  Used ONLY to seed the slider defaults; no numbers from
        it are plotted directly.
    """
    # ------------------------------------------------------------------
    # Seed defaults from the committed report (not hard-coded literals)
    # ------------------------------------------------------------------
    observed_n: int = experiment.n_control  # 49,694
    observed_sd: float = _seed_sd(experiment)  # ≈ 243 BRL — from mde_aov
    observed_effect: float = abs(experiment.aov_adjusted.lift)  # 8.63 BRL

    # Bottom-line MDE at the observed design point
    bottom_mde = mde_mean(observed_sd, observed_n, experiment.alpha, 0.80)

    # ------------------------------------------------------------------
    # 1. CALCULATOR banner — verbatim copy from mockup
    # ------------------------------------------------------------------
    mde_def = glossary.define("MDE")
    st.markdown(
        '<div class="simbar">'
        "<b>CALCULATOR</b> — analytical, not experiment output. "
        "Closed-form from the same "
        f'<span class="term" data-def="{mde_def}">mde_mean</span>'
        " formula the pipeline uses."
        "</div>",
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # 2. Bottom-line takeaway tile — verbatim from mockup
    # ------------------------------------------------------------------
    body_html = (
        f"With about {observed_n:,} customers in each group, our study could "
        f"reliably spot a true lift of roughly "
        f'<span class="num">R${bottom_mde:.2f} or more</span> '
        f"(an 80% chance of catching it if it's real). "
        "Anything smaller than that can slip through looking “inconclusive.” "
        "That’s the key reason a near-zero result means "
        "<b>“we couldn’t tell”</b> — not "
        "<b>“there’s no effect.”</b> "
        "Drag the sliders to see how a smaller study would only catch bigger effects."
    )
    st.markdown(
        _ui.takeaway(
            kicker="The bottom line",
            question="Was our study even big enough to catch a real effect?",
            verdict_label=f"Yes — for effects above ~R${bottom_mde:.2f}",
            verdict_cls="ship",
            body_html=body_html,
        ),
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # 3. Sliders
    # ------------------------------------------------------------------
    # SD default seeded from back-solved report value (rounded to nearest 10)
    sd_default = int(round(observed_sd / 10) * 10)

    col_n, col_a, col_sd, col_pw = st.columns(4)

    with col_n:
        n_per_arm = st.slider(
            label="n per arm",
            min_value=2_000,
            max_value=80_000,
            step=1_000,
            value=observed_n,
            help="Customers per arm. More n → narrower CI → smaller detectable effect.",
        )

    with col_a:
        alpha = st.slider(
            label="α (significance level)",
            min_value=0.01,
            max_value=0.10,
            step=0.01,
            value=0.05,
            format="%.2f",
            help="Significance level: tolerated false-positive rate.",
        )

    with col_sd:
        sd = st.slider(
            label="baseline SD (BRL)",
            min_value=80,
            max_value=320,
            step=10,
            value=sd_default,
            help=(
                "Spread of order value (BRL). Noisier outcomes need more n. "
                f"Default back-solved from committed mde_aov={experiment.mde_aov:.2f} "
                f"at n={observed_n:,}, α={experiment.alpha}."
            ),
        )

    with col_pw:
        power_target = st.slider(
            label="power (target)",
            min_value=0.70,
            max_value=0.95,
            step=0.05,
            value=0.80,
            format="%.2f",
            help="Probability of detecting a true effect of the target size.",
        )

    # ------------------------------------------------------------------
    # 4. Output row — MDE / CI half-width / power@observed
    # ------------------------------------------------------------------
    computed_mde = mde_mean(float(sd), n_per_arm, alpha, power_target)
    computed_hw = _ci_half_width(float(sd), n_per_arm, alpha)
    computed_power = charts._power_at(observed_effect, float(sd), n_per_arm, alpha)
    pw_cls = valuecolor.power_class(computed_power)

    mde_html = (
        '<div class="kpi">'
        '<div class="lab">' + _ui.term("MDE (BRL)", "MDE") + "</div>"
        '<div class="num">' + _ui.value(f"R${computed_mde:.2f}", "neutral") + "</div>"
        "</div>"
    )
    hw_html = (
        '<div class="kpi">'
        '<div class="lab">' + _ui.term("CI half-width", "CI") + "</div>"
        '<div class="num">' + _ui.value(f"±R${computed_hw:.2f}", "neutral") + "</div>"
        "</div>"
    )
    pow_html = (
        f'<div class="kpi">'
        f'<div class="lab">'
        f"power @ R${observed_effect:.2f} (observed lift)"
        f"</div>"
        f'<div class="num">' + _ui.value(f"{computed_power:.2f}", pw_cls) + "</div>"
        "</div>"
    )
    st.markdown(
        f'<div class="cards">{mde_html}{hw_html}{pow_html}</div>',
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # 5. Charts — two columns
    # ------------------------------------------------------------------
    col_curve, col_pow = st.columns(2)

    with col_curve:
        curve_title_html = (
            "<h3>MDE vs sample size"
            + _ui.info(
                "How to read: each point is the smallest effect detectable at that "
                "sample size. The curve falls as n grows — bigger studies catch smaller "
                "effects. The accent dot marks your current slider setting."
            )
            + "</h3>"
        )
        st.markdown(curve_title_html, unsafe_allow_html=True)
        st.plotly_chart(
            charts.mde_vs_n(
                sd=float(sd),
                alpha=alpha,
                power=power_target,
                n_current=n_per_arm,
            ),
            width="stretch",
        )

    with col_pow:
        pow_title_html = (
            "<h3>Power vs true effect size"
            + _ui.info(
                "How to read: for each possible true effect (x-axis), the chance the "
                "study would detect it (y-axis). The dotted line is the 80% target; "
                "effects right of where the curve crosses it are reliably detectable."
            )
            + "</h3>"
        )
        st.markdown(pow_title_html, unsafe_allow_html=True)
        st.plotly_chart(
            charts.power_vs_effect(
                sd=float(sd),
                alpha=alpha,
                n=n_per_arm,
            ),
            width="stretch",
        )

    # ------------------------------------------------------------------
    # 6. Footer caption
    # ------------------------------------------------------------------
    st.markdown(
        '<p class="cap">Slide n down: MDE rises — a smaller study only catches bigger '
        "effects. This is why the null scenario reads “need more data,” not "
        "“no effect.”</p>",
        unsafe_allow_html=True,
    )
