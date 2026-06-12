"""Stage orchestration: feasibility writes artifacts; estimate refuses without GO."""

import json

import pytest

from src.did import run_did
from src.exceptions import BlindingError
from tests.did_factory import make_synthetic_panel


@pytest.fixture
def fake_panels(monkeypatch):
    def _build_panel(con, event, *, unblind_post=False, verdict_path=None):
        panel = make_synthetic_panel(seed=42)
        if not unblind_post:
            return panel[~panel["post"]].reset_index(drop=True)
        from src.did.panel import require_go

        require_go(verdict_path, event.name)
        return panel

    monkeypatch.setattr(run_did, "build_panel", _build_panel)
    monkeypatch.setattr(run_did, "_connect", lambda: None)


def test_feasibility_stage_writes_md_and_json(fake_panels, tmp_path):
    run_did.stage_feasibility(out_md=tmp_path / "f.md", out_json=tmp_path / "f.json")
    assert (tmp_path / "f.md").exists()
    data = json.loads((tmp_path / "f.json").read_text())
    assert data[0]["event"] == "truckers_strike_2018"


def test_gate_stage_writes_verdict(fake_panels, tmp_path):
    path = tmp_path / "verdict.json"
    run_did.stage_gate("truckers_strike_2018", verdict_path=path)
    assert json.loads(path.read_text())["verdict"] in ("GO", "FAIL")


def test_estimate_stage_blocked_without_go(fake_panels, tmp_path):
    with pytest.raises(BlindingError):
        run_did.stage_estimate(
            "truckers_strike_2018",
            verdict_path=tmp_path / "missing.json",
            out_md=tmp_path / "r.md",
            out_json=tmp_path / "r.json",
        )
