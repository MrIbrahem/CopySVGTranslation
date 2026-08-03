"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

logger = logging.getLogger(__name__)


def extract_root_languages(root: etree._Element) -> set[str]:
    languages: set[str] = set()
    try:
        text_elements = root.xpath(
            ".//svg:text",
            namespaces={"svg": "http://www.w3.org/2000/svg"},
        )
        for text in text_elements:
            system_language = text.get("systemLanguage")
            if system_language:
                languages.add(system_language)
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


def tree_languages(tree: etree._ElementTree | None) -> set[str]:
    """Return the list of languages declared in ``systemLanguage`` attributes."""

    if tree is None:
        return set()

    root: etree._Element | None = None

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
    ns = {"svg": "http://www.w3.org/2000/svg"}

    # Iterate over all <switch> elements
    # Get all <text> elements
    texts = elem.findall("svg:text", namespaces=ns)

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
    tspans = node.xpath("./svg:tspan", namespaces={"svg": "http://www.w3.org/2000/svg"})
    if tspans:
        return [tspan.text.strip() if tspan.text else "" for tspan in tspans]

    return [node.text.strip()] if node.text else [""]


__all__ = [
    "extract_root_languages",
    "tree_languages",
    "file_langs",
    "sort_switch_texts",
    "extract_text_from_node",
]
