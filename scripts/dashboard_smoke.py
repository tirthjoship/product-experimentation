"""Schema-drift guard: run every dashboard loader against committed reports/.

If a report writer renames a field, this fails in CI before a broken
dashboard reaches the deployed app. Run via `make dashboard-smoke`.
"""

from dashboard.data import load_did, load_experiment, load_motivation, load_scenarios


def main() -> None:
    exp = load_experiment()
    scenarios = load_scenarios()
    motivation = load_motivation()
    did = load_did()

    if len(scenarios) != 3:
        raise SystemExit(f"expected 3 scenarios, got {len(scenarios)}")
    if not any(s.scenario == "large" for s in scenarios):
        raise SystemExit("missing 'large' scenario (hero verdict source)")
    if not did.pretrends.leads:
        raise SystemExit("DiD pre-trends leads empty")

    print(
        "dashboard-smoke OK — "
        f"experiment n={exp.n_control + exp.n_treatment:,}, "
        f"{len(scenarios)} scenarios, "
        f"{len(motivation.buckets)} buckets, "
        f"DiD verdict={did.verdict}"
    )


if __name__ == "__main__":
    main()
