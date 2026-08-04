from __future__ import annotations

import logging
from pathlib import Path
from .nested_base import FixNestedTagsBase

logger = logging.getLogger(__name__)

SVG_NS = "http://www.w3.org/2000/svg"

def flatten_text(elem):
    """Recursively collect text and tails preserving order."""
    parts = []
    if elem.text:
        parts.append(elem.text)
    for child in elem:
        parts.append(flatten_text(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)

class FixNestedTags(FixNestedTagsBase):

    def _flatten_all(self, root, tag=None):
        """
        Flatten nested <tspan> elements while preserving text order and spacing.
        """
        tag = tag or "tspan"
        # Process all tspans that contain nested tspans
        for tspan in root.findall(f".//{{{SVG_NS}}}tspan"):
            nested = tspan.findall(f".//{{{SVG_NS}}}{tag}")
            if not nested:
                continue
            flattened = flatten_text(tspan)
            for child in list(tspan):
                tspan.remove(child)
            tspan.text = flattened
            tspan.tail = None

        return root

def fix_nested_file(
    source_file: Path,
    new_path: Path | None = None,
    pretty_print: bool | None = None,
) -> bool:
    processer = FixNestedTags(pretty_print=pretty_print)

    return processer.fix_file(
        source_file=source_file,
        new_path=new_path,
    )

def fix_nested_tspans(root, tag=None):
    """
    Flatten nested <tspan> elements while preserving text order and spacing.
    """
    processer = FixNestedTags()
    return processer._flatten_all(root, tag=tag)


__all__ = [
    "FixNestedTags",
    "fix_nested_tspans",
    "fix_nested_file",
]
