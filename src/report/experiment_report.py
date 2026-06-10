"""Render the experiment results to markdown. No number is hand-entered upstream."""

from typing import Any

DISCLAIMER = (
    "> **Simulated experiment.** Olist has no native A/B test. Variants are assigned by "
    "hashed `customer_unique_id` (seed 42) on historical data, and the treatment effect is "
    "a synthetic `SIMULATED_EFFECT` injected for methodology demonstration. Not a real lift."
)


def _recommend(ci: tuple[float, float]) -> str:
    lo, hi = ci
    if lo > 0:
        return "SHIP"
    if hi < 0:
        return "DO NOT SHIP"
    return "NEED MORE DATA"


def generate_report(results: dict[str, Any]) -> str:
    ss = results["sample_sizes"]
    aov = results["aov"]
    conv = results["conversion"]
    d7 = results["d7"]
    mde = results["mde"]
    rec = _recommend(aov["ci"])
    lines = [
        "# Experiment 001 — Simulated AOV Lift",
        "",
        DISCLAIMER,
        "",
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
        f"| Conversion (guardrail) | {conv['control']:.4f} | {conv['treatment']:.4f} | "
        f"{conv['treatment'] - conv['control']:.4f} | "
        f"({conv['ci'][0]:.4f}, {conv['ci'][1]:.4f}) | {conv['p']:.4f} |",
        f"| D7 repeat (exploratory) | {d7['control']:.4f} | {d7['treatment']:.4f} | — | — | — |",
        "",
        "## Power",
        f"- AOV MDE: {mde['aov']:.2f}",
        f"- Conversion MDE: {mde['conversion']:.4f}",
        "",
        "## Recommendation",
        f"**{rec}** — based on the AOV 95% bootstrap CI "
        f"({aov['ci'][0]:.2f}, {aov['ci'][1]:.2f}).",
        "",
    ]
    return "\n".join(lines)
