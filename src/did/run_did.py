"""CLI for the gated DiD stages. Stage order is the protocol:
feasibility (blind) -> gate (pre-period only) -> estimate (requires committed GO)."""

import argparse
from dataclasses import asdict
from pathlib import Path

import duckdb

from src.did.catalog import get_event, viable_candidates
from src.did.estimator import fit_twfe
from src.did.gate import evaluate_gate, write_verdict
from src.did.panel import VERDICT_JSON, build_panel
from src.did.report import (
    generate_did_report_md,
    generate_feasibility_md,
    generate_rejection_md,
)
from src.io.loader import load_olist
from src.report.results_io import write_results_json

RAW_DIR = Path("data/raw/olist")
FEASIBILITY_MD = Path("reports/did_feasibility.md")
FEASIBILITY_JSON = Path("reports/did_feasibility.json")
REPORT_MD = Path("reports/experiment_002_did.md")
REPORT_JSON = Path("reports/experiment_002_did.json")
REJECTION_MD = Path("reports/natural_experiment_feasibility.md")


def _connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(":memory:")
    load_olist(con, RAW_DIR)
    return con


def stage_feasibility(
    out_md: Path = FEASIBILITY_MD, out_json: Path = FEASIBILITY_JSON
) -> None:
    con = _connect()
    verdicts = []
    for event in viable_candidates():
        panel_pre = build_panel(con, event)  # blinded: pre-period only
        verdicts.append(evaluate_gate(event, panel_pre))
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(generate_feasibility_md(verdicts))
    write_results_json(verdicts, out_json)
    print(f"wrote {out_md} and {out_json}")


def stage_gate(event_name: str, verdict_path: Path = VERDICT_JSON) -> None:
    con = _connect()
    event = get_event(event_name)
    panel_pre = build_panel(con, event)
    verdict = evaluate_gate(event, panel_pre)
    write_verdict(verdict, verdict_path)
    print(f"{event_name}: {verdict['verdict']} -> {verdict_path}")
    if verdict["verdict"] == "FAIL":
        REJECTION_MD.parent.mkdir(parents=True, exist_ok=True)
        REJECTION_MD.write_text(generate_rejection_md(event, verdict))
        print(f"wrote {REJECTION_MD}")


def stage_estimate(
    event_name: str,
    verdict_path: Path = VERDICT_JSON,
    out_md: Path = REPORT_MD,
    out_json: Path = REPORT_JSON,
) -> None:
    con = _connect()
    event = get_event(event_name)
    panel = build_panel(con, event, unblind_post=True, verdict_path=verdict_path)
    result = fit_twfe(panel, event.outcome)
    pre = panel[~panel["post"]].reset_index(drop=True)
    verdict = evaluate_gate(event, pre)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(generate_did_report_md(event, result, verdict))
    write_results_json(
        {"event": event.name, "result": asdict(result), "gate": verdict}, out_json
    )
    print(f"wrote {out_md} and {out_json}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage", required=True, choices=["feasibility", "gate", "estimate"]
    )
    parser.add_argument("--event", default="truckers_strike_2018")
    args = parser.parse_args()
    if args.stage == "feasibility":
        stage_feasibility()
    elif args.stage == "gate":
        stage_gate(args.event)
    else:
        stage_estimate(args.event)


if __name__ == "__main__":
    main()
