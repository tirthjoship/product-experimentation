import pytest

from src.experiment.effect import apply_simulated_effect


def test_treatment_values_scaled(frame):
    out = apply_simulated_effect(frame).set_index("order_id")
    assert out.loc["o1", "order_value"] == pytest.approx(126.0)
    assert out.loc["o3", "order_value"] == pytest.approx(31.5)
    assert out.loc["o5", "order_value"] == pytest.approx(84.0)


def test_control_values_unchanged(frame):
    out = apply_simulated_effect(frame).set_index("order_id")
    assert out.loc["o2", "order_value"] == pytest.approx(50.0)
    assert out.loc["o4", "order_value"] == pytest.approx(200.0)


def test_input_not_mutated(frame):
    apply_simulated_effect(frame)
    assert frame.set_index("order_id").loc["o1", "order_value"] == pytest.approx(120.0)
