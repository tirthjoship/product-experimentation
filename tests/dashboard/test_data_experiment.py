"""Loader tests — experiment_001 shape, fail-loud schema errors."""

import json
from pathlib import Path

import pytest

from dashboard.data import ReportSchemaError, load_experiment

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_experiment_parses_fields() -> None:
    exp = load_experiment(FIXTURES / "experiment.json")
    assert exp.n_control == 100
    assert exp.n_treatment == 98
    assert exp.aov.lift == pytest.approx(10.15)
    assert exp.aov.ci == (7.36, 13.11)
    assert exp.aov_adjusted.lift == pytest.approx(8.63)
    assert exp.aov_adjusted.ci_width_ratio == pytest.approx(0.868)
    assert exp.conversion.ci == (-0.0003, 0.0039)
    assert exp.mde_aov == pytest.approx(4.32)
    assert exp.balance_gap == pytest.approx(0.0129)


def test_missing_file_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_experiment(FIXTURES / "nope.json")


def test_missing_ci_field_raises_schema_error(tmp_path: Path) -> None:
    raw = json.loads((FIXTURES / "experiment.json").read_text())
    del raw["aov"]["ci"]
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(raw))
    with pytest.raises(ReportSchemaError, match="ci"):
        load_experiment(bad)


def test_inverted_ci_raises_schema_error(tmp_path: Path) -> None:
    raw = json.loads((FIXTURES / "experiment.json").read_text())
    raw["aov"]["ci"] = [13.11, 7.36]
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(raw))
    with pytest.raises(ReportSchemaError, match="lo <= hi"):
        load_experiment(bad)


def test_wrong_length_ci_raises_schema_error(tmp_path: Path) -> None:
    raw = json.loads((FIXTURES / "experiment.json").read_text())
    raw["aov"]["ci"] = [7.36]
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(raw))
    with pytest.raises(ReportSchemaError, match="2 elements"):
        load_experiment(bad)
