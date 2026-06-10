from src.constants import SCENARIOS
from src.experiment.scenarios import run_scenarios


def test_run_scenarios_returns_one_result_per_scenario(base_con):
    results = run_scenarios(base_con)
    assert [r["scenario"] for r in results] == [name for name, _ in SCENARIOS]
    for r in results:
        assert "aov" in r and "ci" in r["aov"]
        assert "verdict" in r


def test_run_scenarios_null_is_not_ship(base_con):
    results = run_scenarios(base_con)
    null = next(r for r in results if r["scenario"] == "null")
    assert null["verdict"] != "SHIP"
