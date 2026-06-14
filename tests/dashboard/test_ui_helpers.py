"""Unit tests for dashboard/sections/_ui.py — pure string assertions only."""

import pytest

from dashboard.sections._ui import CHIP_FOR_VALUE, info, takeaway, term, value

# ---------------------------------------------------------------------------
# term()
# ---------------------------------------------------------------------------


class TestTerm:
    def test_embeds_label(self) -> None:
        result = term("AOV", "AOV")
        assert "AOV" in result

    def test_embeds_glossary_definition(self) -> None:
        result = term("AOV", "AOV")
        assert "Average order value" in result

    def test_uses_term_class(self) -> None:
        result = term("CI", "CI")
        assert 'class="term"' in result

    def test_uses_data_def_attribute(self) -> None:
        result = term("power", "power")
        assert "data-def=" in result
        # definition text is embedded in the attribute
        assert "Probability of detecting" in result

    def test_span_tag(self) -> None:
        result = term("guardrail", "guardrail")
        assert result.startswith("<span") and result.endswith("</span>")

    def test_unknown_key_raises(self) -> None:
        with pytest.raises(KeyError):
            term("Unknown", "no_such_key_xyz")


# ---------------------------------------------------------------------------
# info()
# ---------------------------------------------------------------------------


class TestInfo:
    def test_ci_class_present(self) -> None:
        result = info("How to read: some explanation.")
        assert 'class="ci"' in result

    def test_embeds_text_in_data_def(self) -> None:
        explanation = "How to read: dot = lift, line = CI."
        result = info(explanation)
        assert explanation in result

    def test_inner_text_is_i(self) -> None:
        result = info("tooltip text")
        assert ">i<" in result

    def test_is_span(self) -> None:
        result = info("x")
        assert result.startswith("<span") and result.endswith("</span>")


# ---------------------------------------------------------------------------
# takeaway()
# ---------------------------------------------------------------------------


class TestTakeaway:
    def _make(self, verdict_cls: str = "ship") -> str:
        return takeaway(
            kicker="The bottom line",
            question="Should we ship?",
            verdict_label="SHIP — optimistic case",
            verdict_cls=verdict_cls,
            body_html="<b>Yes</b>, ship it.",
        )

    def test_takeaway_class(self) -> None:
        assert 'class="takeaway"' in self._make()

    def test_kicker_in_lab(self) -> None:
        result = self._make()
        assert 'class="lab"' in result
        assert "The bottom line" in result

    def test_question_in_q(self) -> None:
        result = self._make()
        assert 'class="q"' in result
        assert "Should we ship?" in result

    def test_verdict_label_in_chip(self) -> None:
        result = self._make()
        assert "SHIP — optimistic case" in result

    def test_chip_ship_class(self) -> None:
        result = self._make(verdict_cls="ship")
        assert 'class="chip ship"' in result

    def test_chip_no_class(self) -> None:
        result = takeaway("", "", "DO NOT SHIP", "no", "")
        assert 'class="chip no"' in result

    def test_chip_more_class(self) -> None:
        result = takeaway("", "", "NEED MORE DATA", "more", "")
        assert 'class="chip more"' in result

    def test_body_html_in_p(self) -> None:
        result = self._make()
        assert "<b>Yes</b>, ship it." in result

    def test_verdline_wrapper(self) -> None:
        assert 'class="verdline"' in self._make()


# ---------------------------------------------------------------------------
# value()
# ---------------------------------------------------------------------------


class TestValue:
    def test_good_class(self) -> None:
        result = value("R$8.63", "good")
        assert 'class="v-good"' in result

    def test_average_class(self) -> None:
        result = value("+2%", "average")
        assert 'class="v-average"' in result

    def test_poor_class(self) -> None:
        result = value("-5%", "poor")
        assert 'class="v-poor"' in result

    def test_neutral_class(self) -> None:
        result = value("0.54", "neutral")
        assert 'class="v-neutral"' in result

    def test_number_embedded(self) -> None:
        result = value("R$8.63", "good")
        assert "R$8.63" in result

    def test_no_tag_when_none(self) -> None:
        result = value("R$8.63", "good")
        assert "vtag" not in result

    def test_tag_span_present_when_given(self) -> None:
        result = value("51.4%", "good", tag="strong")
        assert 'class="vtag good"' in result
        assert "strong" in result

    def test_tag_span_absent_when_not_given(self) -> None:
        result = value("51.4%", "good", tag=None)
        assert '<span class="vtag' not in result

    def test_tag_value_poor(self) -> None:
        result = value("−7.56", "poor", tag="bad")
        assert 'class="vtag poor"' in result
        assert "bad" in result


# ---------------------------------------------------------------------------
# CHIP_FOR_VALUE mapping
# ---------------------------------------------------------------------------


class TestChipForValue:
    def test_good_maps_to_ship(self) -> None:
        assert CHIP_FOR_VALUE["good"] == "ship"

    def test_average_maps_to_more(self) -> None:
        assert CHIP_FOR_VALUE["average"] == "more"

    def test_poor_maps_to_no(self) -> None:
        assert CHIP_FOR_VALUE["poor"] == "no"

    def test_all_values_are_valid_chip_variants(self) -> None:
        valid = {"ship", "no", "more"}
        for val in CHIP_FOR_VALUE.values():
            assert val in valid
