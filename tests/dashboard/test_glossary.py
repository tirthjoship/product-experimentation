import pytest

from dashboard import glossary


def test_known_terms_have_nonempty_defs() -> None:
    for term in [
        "AOV",
        "CI",
        "MDE",
        "raw lift",
        "adjusted lift",
        "theta",
        "conversion",
        "D7",
        "power",
        "alpha",
        "pre-trends",
        "guardrail",
    ]:
        d = glossary.define(term)
        assert isinstance(d, str) and len(d) > 10


def test_unknown_term_raises() -> None:
    with pytest.raises(KeyError):
        glossary.define("not-a-real-term")
