# preparation/steps/normalize_tspans.py
from __future__ import annotations

from lxml import etree

from ...nested import NestedTspanFlattener
from .base import PreparationContext, PreparationStep

SVG_NS = "http://www.w3.org/2000/svg"


class NormalizeTspans(PreparationStep):
    """
    1. Apply nested-tspan strategy (via NestedTspanFlattener).
    2. Wrap loose text / tails under <text> into <tspan>.
    """

    def execute(self, ctx: PreparationContext) -> None:
        if ctx.root is None:
            return

        flattener = NestedTspanFlattener(self.config.nested_strategy)
        flattener.process(ctx.root)

        for text_el in ctx.root.findall(f".//{{{SVG_NS}}}text"):
            self._wrap_loose_text(text_el)

    def _wrap_loose_text(self, text_el: etree._Element) -> None:
        children = list(text_el)

        if not children:
            if text_el.text and text_el.text.strip():
                tspan = etree.Element(f"{{{SVG_NS}}}tspan")
                tspan.text = text_el.text
                text_el.text = None
                text_el.append(tspan)
            return

        if text_el.text and text_el.text.strip():
            tspan = etree.Element(f"{{{SVG_NS}}}tspan")
            tspan.text = text_el.text
            text_el.text = None
            text_el.insert(0, tspan)

        for child in children:
            if child.tail and child.tail.strip():
                new_tspan = etree.Element(f"{{{SVG_NS}}}tspan")
                new_tspan.text = child.tail
                child.tail = None
                idx = text_el.index(child)
                text_el.insert(idx + 1, new_tspan)


__all__ = ["NormalizeTspans"]
