"""Property tests on the data transform — CI ordering invariants.

Per design review: property-test the transform, NOT plotly trace geometry
(brittle, version-coupled).
"""

from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from dashboard.data import ReportSchemaError, _ci

FAKE = Path("fake.json")

finite = st.floats(allow_nan=False, allow_infinity=False, width=32)


@given(lo=finite, hi=finite)
def test_valid_ci_roundtrips_ordered(lo: float, hi: float) -> None:
    lo, hi = min(lo, hi), max(lo, hi)
    out = _ci({"ci": [lo, hi]}, "ci", FAKE)
    assert out == (lo, hi)
    assert out[0] <= out[1]


@given(lo=finite, hi=finite)
def test_inverted_ci_always_raises(lo: float, hi: float) -> None:
    lo, hi = min(lo, hi), max(lo, hi)
    if lo == hi:
        return
    with pytest.raises(ReportSchemaError):
        _ci({"ci": [hi, lo]}, "ci", FAKE)


@given(st.lists(finite, min_size=0, max_size=5).filter(lambda x: len(x) != 2))
def test_wrong_length_ci_always_raises(raw: list[float]) -> None:
    with pytest.raises(ReportSchemaError):
        _ci({"ci": raw}, "ci", FAKE)
