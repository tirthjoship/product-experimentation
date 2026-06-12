"""Catalog invariants: 27 UFs, disjoint donut arms, geography-only construction."""

import pytest

from src.did.catalog import ALL_UFS, CATALOG, get_event, viable_candidates
from src.exceptions import UnknownEventError


def test_all_ufs_is_27():
    assert len(ALL_UFS) == 27


def test_catalog_has_three_dated_candidates():
    assert len(CATALOG) >= 3
    for e in CATALOG:
        assert e.boundary_date  # dated boundary (gate condition 1)
        assert e.source  # citable public record
        assert e.estimation_start < e.boundary_date < e.estimation_end_exclusive


def test_donut_arms_disjoint_and_geographic():
    for e in CATALOG:
        treated, control, excluded = (
            set(e.treated_states),
            set(e.control_states),
            set(e.excluded_states),
        )
        assert treated and control
        assert treated.isdisjoint(control)
        assert treated.isdisjoint(excluded)
        assert control.isdisjoint(excluded)
        assert (treated | control | excluded) <= ALL_UFS


def test_expected_sign_is_unit():
    for e in CATALOG:
        assert e.expected_sign in (-1, 1)
        assert e.outcome in ("delivery_days", "log_orders")


def test_viable_candidates_subset():
    viable = viable_candidates()
    assert all(e.viable_on_paper for e in viable)
    assert {e.name for e in viable} <= {e.name for e in CATALOG}


def test_get_event_unknown_raises():
    with pytest.raises(UnknownEventError):
        get_event("nonexistent")
