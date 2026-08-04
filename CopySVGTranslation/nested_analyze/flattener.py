# nested/flattener.py
from __future__ import annotations

import logging
from typing import Literal

from lxml import etree

from ..exceptions import SvgNestedTspanError

logger = logging.getLogger(__name__)

SVG_NS = "http://www.w3.org/2000/svg"

NestedStrategy = Literal["split_nested_tspans", "preserve_style", "flatten", "raise"]


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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
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

        # preserve_style / split_nested_tspans (default)
        if self.strategy == "preserve_style" or self.strategy == "split_nested_tspans":
            self._preserve_style(root, tag="tspan")
            if self.also_fix_a:
                # <a> inside tspan is also invalid for many tools
                self._preserve_style(root, tag="a")
            return root

        raise ValueError(f"Unknown strategy: {self.strategy}")

    # ------------------------------------------------------------------
    # Strategy: raise
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Strategy: flatten
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Strategy: split_nested_tspans / preserve_style
    # ------------------------------------------------------------------
    def _preserve_style(self, root: etree._Element, tag: str) -> None:
        """
        Convert nested tspans into sibling tspans so styling is kept.

        Example
        -------
        Before:
            <tspan x="16" y="581">
                <tspan style="font-weight:700">Data source:</tspan>
                United Nations ...
            </tspan>

        After:
            <tspan style="font-weight:700">Data source:</tspan>
            <tspan>United Nations ...</tspan>
        """
        # Process per parent <text> so we can safely replace children
        for parent in root.findall(f".//{{{SVG_NS}}}text"):
            # Get direct tspan children of this text element
            direct_tspans = [child for child in parent if child.tag == f"{{{SVG_NS}}}tspan"]

            for tspan in direct_tspans:
                # Check if this tspan has nested children (direct children only)
                nested_children = [child for child in tspan if child.tag == f"{{{SVG_NS}}}{tag}"]

                if not nested_children:
                    continue

                # Get the position of the current tspan in its parent
                parent_list = list(parent)
                index = parent_list.index(tspan)

                # Collect all the new sibling tspans we'll create
                new_siblings: list[etree._Element] = []

                # If the parent tspan has its own text before children, preserve it
                # Note: We skip text that is only whitespace (e.g., indentation) as it's not
                # semantically meaningful. Text with actual content is always preserved.

                # Text that belongs to the outer tspan (before any children)
                if tspan.text and tspan.text.strip():
                    outer = etree.Element(f"{{{SVG_NS}}}tspan")
                    outer.text = tspan.text
                    # optionally copy non-position attributes from outer tspan
                    new_siblings.append(outer)

                # Process each nested child in order
                for nested in nested_children:
                    # Clone the nested element (it becomes a sibling)
                    new_tspan = etree.Element(f"{{{SVG_NS}}}tspan")
                    # Copy all attributes from the nested element
                    for k, v in nested.attrib.items():
                        new_tspan.set(k, v)
                    # Copy the text content
                    new_tspan.text = nested.text
                    new_siblings.append(new_tspan)

                    # Tail after the nested element:

                    # If the nested element has a tail, wrap it in a new tspan
                    # Note: We skip tail text that is only whitespace (e.g., indentation)
                    # as it's not semantically meaningful. Tail text with actual content is preserved.
                    if nested.tail and nested.tail.strip():
                        tail_tspan = etree.Element(f"{{{SVG_NS}}}tspan")
                        tail_tspan.text = nested.tail
                        new_siblings.append(tail_tspan)

                # Remove the original tspan
                parent.remove(tspan)

                # Insert the new siblings at the position where the original tspan was
                for i, sibling in enumerate(new_siblings):
                    parent.insert(index + i, sibling)


__all__ = [
    "NestedTspanFlattener",
]
