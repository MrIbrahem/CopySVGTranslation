from __future__ import annotations

import logging
from pathlib import Path
from lxml import etree

logger = logging.getLogger("CopySvgTranslate")
SVG_NS = "http://www.w3.org/2000/svg"


def match_nested_tags(svg_file_path: Path):
    """Find <tspan> elements that contain nested <tspan> tags."""
    svg_file_path = Path(svg_file_path)
    if not svg_file_path.exists():
        logger.error(f"File not exists: {svg_file_path}")
        return None

    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(str(svg_file_path), parser)
    root = tree.getroot()

    if root is None:
        return None

    result = []
    # Find all <tspan> elements
    tspans = root.findall(f".//{{{SVG_NS}}}tspan")
    for tspan in tspans:
        # Check if <tspan> has element children (nested tags)
        element_children = [c for c in tspan if isinstance(c.tag, str)]
        if element_children:
            # Add string representation of nested element to results
            result.append(etree.tostring(tspan, pretty_print=False).decode("utf-8"))

    return result
