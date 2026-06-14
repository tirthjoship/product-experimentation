from pathlib import Path

import pytest

from dashboard import data

FIX = Path(__file__).parent.parent / "fixtures" / "experiment_grid.json"


def test_load_grid_parses_all_points() -> None:
    grid = data.load_grid(FIX)
    assert len(grid) == 3
    effects = sorted(p.result.simulated_effect for p in grid)
    assert effects == [-0.05, 0.0, 0.05]
    assert {p.verdict for p in grid} == {"DO NOT SHIP", "NEED MORE DATA", "SHIP"}


def test_load_grid_rejects_non_list(tmp_path: Path) -> None:
    bad = tmp_path / "g.json"
    bad.write_text('{"not": "a list"}')
    with pytest.raises(data.ReportSchemaError):
        data.load_grid(bad)
