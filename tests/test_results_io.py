import json

import numpy as np
import pytest

from src.report.results_io import results_to_json, write_results_json


def _sample_results() -> dict:
    return {
        "sample_sizes": {"control": 3, "treatment": 3},
        "aov": {
            "control": 103.33,
            "treatment": np.float64(76.66),
            "lift": -26.67,
            "ci": (np.float64(-40.0), np.float64(-13.0)),
            "p": 0.01,
        },
        "simulated_effect": 0.05,
    }


def test_results_to_json_is_valid_json():
    parsed = json.loads(results_to_json(_sample_results()))
    assert parsed["sample_sizes"]["control"] == 3


def test_tuple_ci_becomes_list_and_numpy_coerced():
    parsed = json.loads(results_to_json(_sample_results()))
    assert parsed["aov"]["ci"] == [-40.0, -13.0]
    assert isinstance(parsed["aov"]["treatment"], float)


def test_write_results_json_roundtrips(tmp_path):
    path = tmp_path / "out.json"
    write_results_json(_sample_results(), path)
    parsed = json.loads(path.read_text())
    assert parsed["aov"]["p"] == 0.01


def test_numpy_scalars_coerced_via_default():
    payload = {"f": np.float32(1.5), "i": np.int32(7)}
    parsed = json.loads(results_to_json(payload))
    assert parsed == {"f": 1.5, "i": 7}


def test_non_serializable_raises_type_error():
    with pytest.raises(TypeError):
        results_to_json({"bad": object()})
