import pytest

from src.experiment.assignment import assign_variant


@pytest.mark.parametrize(
    "uid,expected",
    [
        ("u1", "treatment"),
        ("u2", "control"),
        ("u3", "control"),
        ("u4", "treatment"),
        ("u5", "control"),
    ],
)
def test_known_assignments_seed_42(uid, expected):
    assert assign_variant(uid) == expected


def test_deterministic():
    assert assign_variant("abc") == assign_variant("abc")


def test_only_two_variants():
    assert assign_variant("anything") in {"control", "treatment"}


def test_seed_changes_assignment_space():
    # different seed is allowed to differ; just must stay valid
    assert assign_variant("u1", seed=7) in {"control", "treatment"}
