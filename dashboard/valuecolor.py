"""Pure good/average/poor classification of values for color-coding.

Returns a class string ("good" | "average" | "poor" | "neutral"). The render
layer maps the class to a CSS color (theme.value_color). Thresholds are
interpretation, not new metrics — keep them here, documented and tested.
"""

_VERDICT = {"SHIP": "good", "NEED MORE DATA": "average", "DO NOT SHIP": "poor"}


def verdict_class(verdict: str) -> str:
    return _VERDICT.get(verdict, "neutral")


def power_class(power: float) -> str:
    if power >= 0.80:
        return "good"
    if power >= 0.50:
        return "average"
    return "poor"


def mde_class(adjusted_lift: float, mde: float) -> str:
    """Good when the effect is detectable (|lift| >= MDE), else average."""
    return "good" if abs(adjusted_lift) >= mde else "average"
