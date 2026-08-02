# nested/flattener.py
from __future__ import annotations

import logging
from typing import Literal

from lxml import etree

from ..exceptions import SvgNestedTspanError

logger = logging.getLogger(__name__)
SVG_NS = "http://www.w3.org/2000/svg"

NestedStrategy = Literal["preserve_style", "flatten", "raise"]


def _flatten_text(elem: etree._Element) -> str:
    """Recursively collect text and tails preserving order."""
    parts: list[str] = []
    if elem.text:
        parts.append(elem.text)
    for child in elem:
        parts.append(_flatten_text(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


class NestedTspanFlattener:
    """
    Fix nested <tspan> / <a> elements according to the chosen strategy.
    """

    def __init__(
        self,
        strategy: NestedStrategy = "preserve_style",
        *,
        also_fix_a: bool = True,
    ) -> None:
        self.strategy = strategy
        self.also_fix_a = also_fix_a

    def process(self, root: etree._Element) -> etree._Element:
        """
        Process the tree in-place and return the root.
        """
        if self.strategy == "raise":
            self._raise_if_nested(root)
            return root

        if self.strategy == "flatten":
            self._flatten_all(root, tag="tspan")
            if self.also_fix_a:
                self._flatten_all(root, tag="a")
            return root

        # preserve_style (default)
        self._preserve_style(root, tag="tspan")
        if self.also_fix_a:
            self._preserve_style(root, tag="a")
        return root

    def _raise_if_nested(self, root: etree._Element) -> None:
        for tspan in root.findall(f".//{{{SVG_NS}}}tspan"):
            element_children = [c for c in tspan if isinstance(c.tag, str)]
            if element_children:
                node_text = etree.tostring(tspan, pretty_print=True).decode("utf-8")
                raise SvgNestedTspanError(
                    element=tspan,
                    extra=[tspan.get("id", "")],
                    node_text=node_text,
                )

    def _flatten_all(self, root: etree._Element, tag: str) -> None:
        for tspan in root.findall(f".//{{{SVG_NS}}}tspan"):
            nested = tspan.findall(f".//{{{SVG_NS}}}{tag}")
            if not nested:
                continue
            flattened = _flatten_text(tspan)
            for child in list(tspan):
                tspan.remove(child)
            tspan.text = flattened
            tspan.tail = None

    def _preserve_style(self, root: etree._Element, tag: str) -> None:
        """
        Convert nested tspans into sibling tspans so styling is kept.
        """
        for parent in root.findall(f".//{{{SVG_NS}}}text"):
            direct_tspans = [
                child for child in parent
                if child.tag == f"{{{SVG_NS}}}tspan"
            ]

            for tspan in direct_tspans:
                nested_children = [
                    child for child in tspan
                    if child.tag == f"{{{SVG_NS}}}{tag}"
                ]
                if not nested_children:
                    continue

                parent_list = list(parent)
                index = parent_list.index(tspan)
                new_siblings: list[etree._Element] = []

                if tspan.text and tspan.text.strip():
                    outer = etree.Element(f"{{{SVG_NS}}}tspan")
                    outer.text = tspan.text
                    new_siblings.append(outer)

                for nested in nested_children:
                    new_tspan = etree.Element(f"{{{SVG_NS}}}tspan")
                    for k, v in nested.attrib.items():
                        new_tspan.set(k, v)
                    new_tspan.text = nested.text
                    new_siblings.append(new_tspan)

                    if nested.tail and nested.tail.strip():
                        tail_tspan = etree.Element(f"{{{SVG_NS}}}tspan")
                        tail_tspan.text = nested.tail
                        new_siblings.append(tail_tspan)

                parent.remove(tspan)
                for i, sibling in enumerate(new_siblings):
                    parent.insert(index + i, sibling)
