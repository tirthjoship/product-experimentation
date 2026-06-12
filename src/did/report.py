"""Markdown writers for the DiD natural experiment. Numbers always come from the same
dicts/dataclasses that produce the committed JSON (rule 1: no invented metrics)."""

from typing import Any

from src.did.catalog import EventDefinition
from src.did.estimator import DidResult


def _gate_table(verdict: dict[str, Any]) -> list[str]:
    lines = ["| Condition | Passed | Evidence |", "|---|---|---|"]
    for name, c in verdict["conditions"].items():
        evidence = {k: v for k, v in c.items() if k != "passed"}
        mark = "✅" if c["passed"] else "❌"
        lines.append(f"| {name} | {mark} | `{evidence}` |")
    return lines


def generate_feasibility_md(verdicts: list[dict[str, Any]]) -> str:
    lines = [
        "# DiD Feasibility — Phase B (outcome-blind)",
        "",
        "> Pre-period cell counts ONLY. No outcome × event-window data was inspected;",
        "> post-period rows are code-blinded until a committed GO verdict exists.",
        "",
    ]
    for v in verdicts:
        n = v["conditions"]["adequate_n"]
        lines += [
            f"## {v['event']}",
            "",
            f"- treated orders (pre): **{n['treated_orders']:,}**",
            f"- control orders (pre): **{n['control_orders']:,}**",
            f"- week-cells ≥ 20 orders: **{n['week_cell_share_ge_20']:.1%}**",
            f"- states per arm: {n['treated_states']} / {n['control_states']}",
            "",
        ]
    return "\n".join(lines)


def generate_did_report_md(
    event: EventDefinition, result: DidResult, verdict: dict[str, Any]
) -> str:
    lines = [
        f"# Experiment 002 — Natural Experiment (DiD): {event.name}",
        "",
        "> **Observational natural experiment** on real Olist data (no synthetic effect).",
        "> Identification rests on the pre-registered gate below, not on randomization.",
        "",
        event.description,
        "",
        f"**DiD estimate ({result.outcome}):** **{result.beta:.2f}** "
        f"(95% CI ({result.ci[0]:.2f}, {result.ci[1]:.2f}), p={result.p:.4f}, "
        f"SE {result.se:.2f}, clusters={result.n_clusters}, n={result.n_obs})",
        "",
        "## Pre-registered gate (decided before unblinding)",
        "",
        *_gate_table(verdict),
        "",
        "## Threats to validity",
        "",
        "- Spillovers: control states also faced the national shock → estimate is a",
        "  *differential*-exposure effect, biased toward zero if controls were hit too.",
        "- Composition: order mix may shift at the boundary (purchase-week assignment).",
        "- SUTVA: marketplace-level seller congestion can couple arms.",
        "- Delivery-cell selection: cells with zero delivered orders yield a NULL",
        "  outcome and are dropped before estimation; a freight shock that suppresses",
        "  delivery itself thins treated-post cells, a selection channel that can bias",
        "  the delivery-time estimate. A volume outcome (log_orders) avoids this.",
        "",
    ]
    return "\n".join(lines)


def generate_rejection_md(event: EventDefinition, verdict: dict[str, Any]) -> str:
    broken = [k for k, c in verdict["conditions"].items() if not c["passed"]]
    lines = [
        "# Natural Experiment Feasibility — REJECTED",
        "",
        f"Candidate: **{event.name}** — gate verdict **{verdict['verdict']}**.",
        "",
        f"Broken condition(s): **{', '.join(broken)}**.",
        "",
        "Per the pre-registered protocol (spec §9), no estimate is computed or",
        "reported. This rejection is the deliverable: the identification assumptions",
        "required for a causal claim do not hold, and we do not manufacture one.",
        "",
        "## Gate evidence",
        "",
        *_gate_table(verdict),
        "",
    ]
    return "\n".join(lines)
