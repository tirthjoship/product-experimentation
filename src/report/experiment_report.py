"""Render the experiment results to markdown. No number is hand-entered upstream."""

from typing import Any

DISCLAIMER = (
    "> **Simulated experiment.** Olist has no native A/B test. Variants are assigned by "
    "hashed `customer_unique_id` (seed 42) on historical data, and the treatment effect is "
    "a synthetic `SIMULATED_EFFECT` injected for methodology demonstration. Not a real lift."
)


def recommend(ci: tuple[float, float]) -> str:
    lo, hi = ci
    if lo > 0:
        return "SHIP"
    if hi < 0:
        return "DO NOT SHIP"
    return "NEED MORE DATA"


def generate_report(results: dict[str, Any]) -> str:
    ss = results["sample_sizes"]
    aov = results["aov"]
    adj = results["aov_adjusted"]
    conv = results["conversion"]
    d7 = results["d7"]
    mde = results["mde"]
    rec = recommend(adj["ci"])
    lines = [
        "# Experiment 001 — Simulated AOV Lift",
        "",
        DISCLAIMER,
        "",
        "Framing: installment-expansion test (6x → 10x interest-free cap) — full decision "
        "memo in `reports/experiment_001_readout.md`.",
        f"Injected `SIMULATED_EFFECT` = {results['simulated_effect']}",
        "",
        "## Sample sizes",
        f"- control: {ss['control']}",
        f"- treatment: {ss['treatment']}",
        "",
        "## Metrics",
        "",
        "| Metric | Control | Treatment | Lift | 95% CI | p |",
        "|---|---|---|---|---|---|",
        f"| AOV (primary) | {aov['control']:.2f} | {aov['treatment']:.2f} | "
        f"{aov['lift']:.2f} | ({aov['ci'][0]:.2f}, {aov['ci'][1]:.2f}) | {aov['p']:.4f} |",
        f"| AOV (covariate-adjusted) | {adj['control']:.2f} | {adj['treatment']:.2f} | "
        f"{adj['lift']:.2f} | ({adj['ci'][0]:.2f}, {adj['ci'][1]:.2f}) | — |",
        f"| Conversion (guardrail) | {conv['control']:.4f} | {conv['treatment']:.4f} | "
        f"{conv['treatment'] - conv['control']:.4f} | "
        f"({conv['ci'][0]:.4f}, {conv['ci'][1]:.4f}) | {conv['p']:.4f} |",
        f"| D7 repeat (exploratory) | {d7['control']:.4f} | {d7['treatment']:.4f} | — | — | — |",
        "",
        f"Covariate adjustment (ANCOVA on pre-treatment `freight_value`, θ={adj['theta']:.4f}, "
        f"estimated pooled pre-injection): CI width is {adj['ci_width_ratio']:.0%} of the "
        "unadjusted width. Both rows shown for auditability. The adjusted row uses lower variance "
        "by removing freight_value correlation, yielding narrower confidence intervals.",
        "",
        "## Power",
        f"- AOV MDE: {mde['aov']:.2f}",
        f"- Conversion MDE: {mde['conversion']:.4f}",
        "",
        "## Recommendation",
        f"**{rec}** — based on the **covariate-adjusted** AOV 95% bootstrap CI "
        f"({adj['ci'][0]:.2f}, {adj['ci'][1]:.2f}).",
        "",
    ]
    return "\n".join(lines)


def generate_scenarios_report(scenarios: list[dict[str, Any]]) -> str:
    """Render the multi-scenario sweep: one row per injected effect, with its verdict."""
    lines = [
        "# Experiment Scenarios — Decision Rule Validation",
        "",
        DISCLAIMER,
        "",
        "Each row injects a different `SIMULATED_EFFECT` and reports the verdict the "
        "covariate-adjusted AOV 95% bootstrap CI produces. The rule yields SHIP / DO NOT SHIP / "
        "NEED MORE DATA — not just SHIP — which is the point: the pipeline handles the hard cases.",
        "Framing: installment-expansion test (6x → 10x interest-free cap).",
        "",
        "| Scenario | Injected effect | Lift | 95% CI | Adj. lift | Adj. 95% CI | Verdict |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in scenarios:
        aov = s["aov"]
        adj = s["aov_adjusted"]
        lines.append(
            f"| {s['scenario']} | {s['simulated_effect']} | {aov['lift']:.2f} | "
            f"({aov['ci'][0]:.2f}, {aov['ci'][1]:.2f}) | {adj['lift']:.2f} | "
            f"({adj['ci'][0]:.2f}, {adj['ci'][1]:.2f}) | {s['verdict']} |"
        )
    lines.append("")
    return "\n".join(lines)
