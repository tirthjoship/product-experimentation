"""Pure HTML-string builders for dashboard v3 UI components.

These functions emit HTML snippets that rely on CSS classes defined in
``dashboard/theme.py``'s ``CSS`` block.  They are importable and unit-testable
with no Streamlit dependency.

Class-name mapping
------------------
``valuecolor.verdict_class`` returns one of: ``"good"`` / ``"average"`` / ``"poor"``.

The CSS has *two* namespaces that use those names differently:

* **Value spans** (``.v-<cls>``)  — ``.v-good``, ``.v-average``, ``.v-poor``,
  ``.v-neutral``.  ``value()`` maps directly (``cls`` token → ``v-{cls}``).

* **Chip badges** (``.chip.<variant>``) — CSS defines ``.chip.ship``,
  ``.chip.no``, ``.chip.more``.  These are *not* "good/average/poor".
  ``takeaway()`` therefore accepts the chip variant token directly
  (``"ship"`` / ``"no"`` / ``"more"``).  Callers that hold a valuecolor class
  can convert with the convenience mapping ``CHIP_FOR_VALUE``::

      from dashboard.sections._ui import CHIP_FOR_VALUE
      chip_cls = CHIP_FOR_VALUE["good"]   # → "ship"

* **vtag badges** (``.vtag.<cls>``) — CSS defines ``.vtag.good``,
  ``.vtag.avg`` / ``.vtag.average``, ``.vtag.bad`` / ``.vtag.poor``.
  ``value()`` passes ``cls`` straight through (``"good"`` / ``"average"`` /
  ``"poor"`` / ``"neutral"`` all have matching rules).

* **Tooltip mechanism** — ``.ci`` and ``.term`` both use a CSS ``::after``
  pseudo-element that reads ``attr(data-def)``.  The ``define()`` call in
  ``term()`` raises ``KeyError`` for unknown glossary entries; callers must
  use a key present in ``dashboard.glossary._TERMS``.
"""

from __future__ import annotations

from dashboard import glossary

# ---------------------------------------------------------------------------
# Convenience: map a valuecolor class to the matching chip variant
# ---------------------------------------------------------------------------
CHIP_FOR_VALUE: dict[str, str] = {
    "good": "ship",
    "average": "more",
    "poor": "no",
    "neutral": "more",  # fallback — neutral verdicts default to "need more data"
}


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def term(label: str, key: str) -> str:
    """Return a glossary-hover ``<span>`` for *label*.

    The ``data-def`` attribute is populated from ``glossary.define(key)``
    so the hover tooltip stays in sync with the single source of truth in
    ``dashboard/glossary.py``.  Raises ``KeyError`` if *key* is not defined.

    CSS: ``.term`` (dotted underline + ``::after`` tooltip via ``attr(data-def)``).
    """
    definition = glossary.define(key)
    return f'<span class="term" data-def="{definition}">{label}</span>'


def info(text: str) -> str:
    """Return a chart-info ``ⓘ`` icon that shows *text* on hover.

    Renders as a small circled ``i`` badge.  Typically placed immediately
    after a chart ``<h3>`` title.

    CSS: ``.ci`` (15 × 15 px circle + ``::after`` tooltip via ``attr(data-def)``).
    """
    return f'<span class="ci" data-def="{text}">i</span>'


def takeaway(
    kicker: str,
    question: str,
    verdict_label: str,
    verdict_cls: str,
    body_html: str,
) -> str:
    """Return a full bottom-line takeaway tile.

    Parameters
    ----------
    kicker:
        Short all-caps label shown above the question (e.g. ``"The bottom line"``).
    question:
        The plain-language question the tile answers.
    verdict_label:
        Text shown inside the chip badge (e.g. ``"SHIP — in the optimistic case"``).
    verdict_cls:
        CSS chip variant — one of ``"ship"``, ``"no"``, ``"more"``.
        Use ``CHIP_FOR_VALUE[valuecolor_cls]`` to convert from a valuecolor class.
    body_html:
        Body paragraph HTML (may include ``<b>``, ``<span class="num">`` etc.).

    CSS: ``.takeaway``, ``.takeaway .lab``, ``.takeaway .q``,
    ``.takeaway .verdline``, ``.chip.<verdict_cls>``, ``.takeaway p``.
    """
    return (
        f'<div class="takeaway">'
        f'<div class="lab">{kicker}</div>'
        f'<div class="q">{question}</div>'
        f'<div class="verdline"><span class="chip {verdict_cls}">{verdict_label}</span></div>'
        f"<p>{body_html}</p>"
        f"</div>"
    )


def value(num: str, cls: str, tag: str | None = None) -> str:
    """Return a colored value span, optionally followed by a vtag badge.

    Parameters
    ----------
    num:
        The formatted number string (e.g. ``"R$8.63"``).
    cls:
        Value-color class — one of ``"good"``, ``"average"``, ``"poor"``,
        ``"neutral"``.  Rendered as ``v-{cls}`` (e.g. ``.v-good``).
    tag:
        Optional short label for the inline vtag badge (e.g. ``"strong"``).
        The badge uses ``.vtag.{cls}`` — the same *cls* token maps to both
        namespaces because the vtag CSS aliases cover ``"good"``, ``"average"``,
        ``"poor"``, and ``"neutral"`` via ``.vtag.good`` / ``.vtag.avg`` etc.
        If ``None``, no vtag is emitted.

    CSS: ``.v-good`` / ``.v-average`` / ``.v-poor`` / ``.v-neutral``;
    ``.vtag.good`` / ``.vtag.avg`` / ``.vtag.average`` / ``.vtag.bad`` / ``.vtag.poor``.
    """
    tag_span = f'<span class="vtag {cls}">{tag}</span>' if tag is not None else ""
    return f'<span class="v-{cls}">{num}</span>{tag_span}'
