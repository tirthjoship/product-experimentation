from dashboard import valuecolor as vc


def test_power_thresholds() -> None:
    assert vc.power_class(0.95) == "good"
    assert vc.power_class(0.65) == "average"
    assert vc.power_class(0.30) == "poor"


def test_verdict_value_class() -> None:
    assert vc.verdict_class("SHIP") == "good"
    assert vc.verdict_class("NEED MORE DATA") == "average"
    assert vc.verdict_class("DO NOT SHIP") == "poor"


def test_mde_detectability() -> None:
    assert vc.mde_class(adjusted_lift=8.63, mde=4.32) == "good"
    assert vc.mde_class(adjusted_lift=0.54, mde=4.11) == "average"
