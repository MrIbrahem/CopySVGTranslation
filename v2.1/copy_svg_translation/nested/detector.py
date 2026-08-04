from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

logger = logging.getLogger(__name__)
SVG_NS = "http://www.w3.org/2000/svg"


class NestedTspanDetector:
    """
    Find <tspan> elements that contain nested element children.
    Useful for diagnostics and pre-flight checks.
    """

    def __init__(self, tags: tuple[str, ...] = ("tspan", "a")) -> None:
        self.tags = tags

    def find_in_tree(self, root: etree._Element) -> list[etree._Element]:
        """Return all tspan elements that have element children."""
        result: list[etree._Element] = []
        for tspan in root.findall(f".//{{{SVG_NS}}}tspan"):
            element_children = [c for c in tspan if isinstance(c.tag, str)]
            if element_children:
                result.append(tspan)
        return result

    def find_in_file(self, path: Path | str) -> list[str]:
        """
        Parse a file and return serialised representations of nested tspans.
        Returns an empty list on parse errors.
        """
        path = Path(path)
        if not path.exists():
            logger.error("File does not exist: %s", path)
            return []

        try:
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.parse(str(path), parser)
            root = tree.getroot()
            if root is None:
                return []
        except (etree.XMLSyntaxError, OSError) as exc:
            logger.error("Failed to parse %s: %s", path, exc)
            return []

        nested = self.find_in_tree(root)
        return [
            etree.tostring(
                t,
                pretty_print=False,
            ).decode("utf-8")
            for t in nested
        ]

    def has_nested(self, root: etree._Element) -> bool:
        return bool(self.find_in_tree(root))


__all__ = [
    "NestedTspanDetector",
]
