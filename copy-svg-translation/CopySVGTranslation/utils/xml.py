# utils/xml.py
from __future__ import annotations

import re
from typing import Iterable

from lxml import etree

SVG_NS = "http://www.w3.org/2000/svg"
SVG_NSMAP = {"svg": SVG_NS}


def svg_tag(local: str) -> str:
    """Return a Clark-notation tag for the SVG namespace."""
    return f"{{{SVG_NS}}}{local}"


def local_name(element: etree._Element) -> str:
    """Return the local tag name without namespace."""
    tag = element.tag
    if isinstance(tag, str) and tag.startswith("{"):
        return tag.rsplit("}", 1)[-1]
    return str(tag)


def is_svg_element(element: etree._Element, name: str) -> bool:
    """Check whether element is an SVG element with the given local name."""
    return element.tag in (svg_tag(name), name)


def findall_svg(root: etree._Element, name: str) -> list[etree._Element]:
    """Find all descendant elements with the given SVG local name."""
    return root.findall(f".//{{{SVG_NS}}}{name}")


def xpath_svg(root: etree._Element, expression: str):
    """Run an XPath expression with the standard svg prefix bound."""
    return root.xpath(expression, namespaces=SVG_NSMAP)


def extract_text_segments(node: etree._Element) -> list[str]:
    """
    Extract text segments from a <text> (or similar) node.
    Prefers direct child <tspan>s; falls back to the node's own text.
    """
    tspans = node.xpath("./svg:tspan", namespaces=SVG_NSMAP)
    if tspans:
        return [t.text or "" for t in tspans]
    return [node.text or ""]


def get_text_content(element: etree._Element) -> str:
    """Return concatenated text content (like DOM textContent)."""
    return "".join(element.itertext())


def collect_ids(root: etree._Element) -> set[str]:
    """Return the set of all id attribute values in the tree."""
    return {id_ for id_ in root.xpath("//@id") if id_}


def sort_switch_children(
    switch: etree._Element,
    *,
    put_fallback_last: bool = True,
) -> None:
    """
    Deterministically reorder <text> children of a <switch>.
    Fallback (no systemLanguage) goes last by default.
    """
    texts = [
        c for c in switch
        if isinstance(c.tag, str) and is_svg_element(c, "text")
    ]

    def sort_key(el: etree._Element):
        lang = el.get("systemLanguage") or "fallback"
        m = re.search(r"trsvg(\d+)", el.get("id") or "")
        num = int(m.group(1)) if m else 10**9
        is_fallback = 0 if el.get("systemLanguage") is None else 1
        primary = is_fallback if put_fallback_last else 0
        return (primary, num, lang)

    ordered = sorted(texts, key=sort_key)
    for t in ordered:
        switch.remove(t)
    for t in ordered:
        switch.append(t)


def tree_languages(tree: etree._ElementTree | None) -> set[str]:
    """Return the set of systemLanguage values present in the tree."""
    if tree is None:
        return set()
    root = tree.getroot()
    if root is None:
        return set()
    langs: set[str] = set()
    for text in findall_svg(root, "text"):
        lang = text.get("systemLanguage")
        if lang:
            langs.add(lang)
    return langs
