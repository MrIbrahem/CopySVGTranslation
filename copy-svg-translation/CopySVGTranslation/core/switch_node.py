# core/switch_node.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from lxml import etree

from .text_node import TextNode

SVG_NS = "http://www.w3.org/2000/svg"


@dataclass(slots=True)
class SwitchNode:
    """Domain wrapper over an SVG <switch> element."""

    element: etree._Element

    def text_nodes(self) -> list[TextNode]:
        texts = self.element.xpath("./svg:text", namespaces={"svg": SVG_NS})
        return [TextNode(t) for t in texts]

    def iter_text_nodes(self) -> Iterator[TextNode]:
        yield from self.text_nodes()

    def fallback(self) -> TextNode | None:
        """Return the default (no systemLanguage) text node, if any."""
        for node in self.text_nodes():
            if node.is_fallback:
                return node
        return None

    def existing_languages(self) -> set[str]:
        return {n.language for n in self.text_nodes() if n.language}

    def find_by_language(self, lang: str) -> TextNode | None:
        for node in self.text_nodes():
            if node.language == lang:
                return node
        return None

    def append(self, node: TextNode) -> None:
        self.element.append(node.element)

    def remove(self, node: TextNode) -> None:
        self.element.remove(node.element)

    def reorder(self, put_fallback_last: bool = True) -> None:
        """Deterministic ordering of child <text> elements."""
        nodes = self.text_nodes()

        def sort_key(n: TextNode):
            lang = n.language or "fallback"
            import re

            m = re.search(r"trsvg(\d+)", n.id or "")
            num = int(m.group(1)) if m else 10**9
            is_fallback = 0 if n.is_fallback else 1
            return (is_fallback if put_fallback_last else 0, num, lang)

        ordered = sorted(nodes, key=sort_key)
        for n in ordered:
            self.element.remove(n.element)
        for n in ordered:
            self.element.append(n.element)
