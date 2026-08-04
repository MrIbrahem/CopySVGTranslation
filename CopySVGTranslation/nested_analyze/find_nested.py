from __future__ import annotations

import logging
import warnings
from pathlib import Path

from lxml import etree

logger = logging.getLogger(__name__)
SVG_NS = "http://www.w3.org/2000/svg"


def flatten_text(elem):
    """Recursively collect text and tails preserving order."""
    text_parts = []
    if elem.text:
        text_parts.append(elem.text)
    for child in elem:
        text_parts.append(flatten_text(child))
        if child.tail:
            text_parts.append(child.tail)
    return "".join(text_parts)


def fix_nested_tspans(root, tag=None):
    """
    Flatten nested <tspan> elements while preserving text order and spacing.
    """
    tag = tag or "tspan"
    # Process all tspans that contain nested tspans
    for tspan in root.findall(f".//{{{SVG_NS}}}tspan"):
        nested = tspan.findall(f".//{{{SVG_NS}}}{tag}")
        if nested:
            flattened = flatten_text(tspan)
            for child in list(tspan):
                tspan.remove(child)
            tspan.text = flattened
            tspan.tail = None

    return root


def match_nested_tags(source_file: Path) -> list:
    """Find <tspan> elements that contain nested <tspan> tags."""
    result = []
    source_file = Path(source_file)

    if not source_file.exists():
        logger.error(f"File not exists: {source_file}")
        return []

    parser = etree.XMLParser(remove_blank_text=True)

    try:
        tree = etree.parse(str(source_file), parser)
    except (etree.XMLSyntaxError, OSError) as exc:
        logger.error(f"Failed to parse SVG file {source_file}: {exc}")
        return []

    root = tree.getroot()

    if root is None:
        return []

    # Find all <tspan> elements
    tspans = root.findall(f".//{{{SVG_NS}}}tspan")
    for tspan in tspans:
        # Check if <tspan> has element children (nested tags)
        element_children = [c for c in tspan if isinstance(c.tag, str)]
        if element_children:
            # Add string representation of nested element to results
            tspan_str = etree.tostring(
                tspan,
                pretty_print=False,
            ).decode("utf-8")
            result.append(tspan_str)

    return result


def fix_nested_file(source_file: Path, new_path: Path | None = None, pretty_print: bool | None = None) -> bool:
    """
    !
    """
    # ---
    source_file = Path(source_file)
    if new_path is None:
        warnings.warn(
            "Calling fix_nested_file without new_path is deprecated. "
            "Pass an explicit output path to avoid overwriting the input file.",
            DeprecationWarning,
            stacklevel=2,
        )
    new_path = Path(new_path or source_file)
    # ---
    parser = etree.XMLParser(remove_blank_text=False)
    # ---
    try:
        tree = etree.parse(str(source_file), parser)
    except (etree.XMLSyntaxError, OSError) as exc:
        logger.error(f"Failed to parse SVG file {source_file}: {exc}")
        return False
    # ---
    root = tree.getroot()
    # ---
    if root is None:
        return False
    # ---
    root = fix_nested_tspans(root)
    # ---
    # NOTE: <a tags can also be nested inside <tspan>, so fix those too
    # https://svgtranslate.toolforge.org/ result: This file has unexpected content within a text element.
    # Only tspan elements should be used within text.
    root = fix_nested_tspans(root, "a")
    # ---
    try:
        _str = etree.tostring(
            root,
            encoding="unicode",
            pretty_print=pretty_print,
        )  # pyright: ignore[reportCallIssue]
        new_path.write_text(_str, encoding="utf-8")
        return True
    except Exception:
        logger.error(f"Failed to write fixed svg file to: {str(new_path)}")
    # ---
    return False


__all__ = [
    "match_nested_tags",
    "fix_nested_file",
]
