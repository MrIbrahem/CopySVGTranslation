"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from lxml import etree

logger = logging.getLogger(__name__)

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
        return [t.text.strip() if t.text else "" for t in tspans]
    return [node.text.strip()] if node.text else [""]


def extract_root_languages(root: etree._Element) -> set[str]:
    languages: set[str] = set()
    try:
        text_elements = root.xpath(
            ".//svg:text",
            namespaces={"svg": SVG_NS},
        )
        for text in text_elements:
            lang = text.get("systemLanguage")
            if lang:
                languages.add(lang)
    except (etree.XMLSyntaxError, OSError):
        logger.exception("Error parsing svg languages")

    return languages


def file_langs(file: Path | str | None) -> set[str]:
    """Return the list of languages declared in ``systemLanguage`` attributes."""
    if not file:
        return set()

    root: etree._Element | None = None
    svg_path = Path(str(file))

    try:
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(str(svg_path), parser)
        root = tree.getroot()
    except (etree.XMLSyntaxError, OSError):
        logger.exception("Error parsing svg languages")
        return set()

    languages = extract_root_languages(root)

    return languages


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
    texts = [c for c in switch if isinstance(c.tag, str) and is_svg_element(c, "text")]

    def sort_key(el: etree._Element):
        lang = el.get("systemLanguage") or "fallback"
        m = re.search(r"trsvg(\d+)", (el.get("id") or ""))
        num = int(m.group(1)) if m else 10**9
        fallback_val = 1 if lang == "fallback" else 0
        return (fallback_val if put_fallback_last else (1 - fallback_val), num, lang)

    texts_sorted = sorted(texts, key=sort_key)
    # re-append in sorted order, leaving non-text children (if any) as-is
    for t in texts_sorted:
        switch.remove(t)
    for t in texts_sorted:
        switch.append(t)


def tree_languages(tree: etree._ElementTree | None) -> set[str]:
    """
    Return the set of systemLanguage values present in the tree.
    """
    if tree is None:
        return set()
    try:
        root = tree.getroot()

    except (etree.XMLSyntaxError, OSError):
        logger.exception(f"Error parsing SVG file: {tree}")

    if root is None:
        return set()

    languages = extract_root_languages(root)

    return languages


def sort_switch_texts(elem):
    """
    Sort <text> elements inside each <switch> so that elements
    without systemLanguage attribute come last.
    """

    # Iterate over all <switch> elements
    # Get all <text> elements
    texts = elem.findall("svg:text", namespaces={"svg": SVG_NS})

    # Separate those with systemLanguage and those without
    without_lang = [t for t in texts if t.get("systemLanguage") is None]

    # Clear switch content
    for t in without_lang:
        elem.remove(t)

    # Re-insert <text> elements: first with language, then without
    for t in without_lang:
        elem.append(t)

    return elem


def extract_text_from_node(node) -> list[str]:
    """Extract text content from an SVG ``<text>`` element, honouring ``<tspan>``."""
    tspans = node.xpath("./svg:tspan", namespaces={"svg": SVG_NS})
    if tspans:
        return [tspan.text.strip() if tspan.text else "" for tspan in tspans]

    return [node.text.strip()] if node.text else [""]


__all__ = [
    "sort_switch_children",
    "extract_root_languages",
    "tree_languages",
    "file_langs",
    "sort_switch_texts",
    "extract_text_from_node",
]
