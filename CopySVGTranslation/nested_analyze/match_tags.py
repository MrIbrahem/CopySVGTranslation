from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

logger = logging.getLogger(__name__)
SVG_NS = "http://www.w3.org/2000/svg"

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

__all__ = [
    "match_nested_tags",
]
