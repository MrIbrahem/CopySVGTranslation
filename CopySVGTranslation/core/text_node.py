# core/text_node.py
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from lxml import etree

from ..utils.text import normalize_text

SVG_NS = "http://www.w3.org/2000/svg"


@dataclass(slots=True)
class TextNode:
    """
    Thin domain wrapper over an SVG <text> or <tspan> element.
    Does not own the element - it only provides a convenient API.
    """

    element: etree._Element

    # ------------------------------------------------------------------
    # Identity & language
    # ------------------------------------------------------------------
    @property
    def id(self) -> str | None:
        return self.element.get("id")

    @id.setter
    def id(self, value: str) -> None:
        self.element.set("id", value)

    @property
    def language(self) -> str | None:
        """systemLanguage or None for the fallback/default node."""
        return self.element.get("systemLanguage")

    @language.setter
    def language(self, value: str | None) -> None:
        if value is None:
            self.element.attrib.pop("systemLanguage", None)
        else:
            self.element.set("systemLanguage", value)

    @property
    def is_fallback(self) -> bool:
        return self.language is None

    # ------------------------------------------------------------------
    # Text content
    # ------------------------------------------------------------------
    def texts(self, *, normalize: bool = True, case_insensitive: bool = False) -> list[str]:
        """
        Return the list of text segments.
        Prefer direct child <tspan>s; fall back to the element's own text.
        """
        tspans = self.tspans()
        raw = [t.text or "" for t in tspans] if tspans else [self.element.text or ""]

        if not normalize:
            return raw
        return [normalize_text(t, case_insensitive) for t in raw]

    def set_texts(self, texts: list[str]) -> None:
        """Write texts back into child tspans (or the element itself)."""
        tspans = list(self.tspans())
        if tspans:
            for i, tspan in enumerate(tspans):
                tspan.text = texts[i] if i < len(texts) else ""
        else:
            self.element.text = texts[0] if texts else ""

    def tspans(self) -> list[etree._Element]:
        return self.element.xpath("./svg:tspan", namespaces={"svg": SVG_NS})

    def iter_tspan_nodes(self) -> Iterator[TextNode]:
        for tspan in self.tspans():
            yield TextNode(tspan)

    # ------------------------------------------------------------------
    # Cloning
    # ------------------------------------------------------------------
    def clone(self) -> TextNode:
        """Deep clone the underlying element and wrap it."""
        import copy

        return TextNode(copy.deepcopy(self.element))


__all__ = [
    "TextNode",
]
