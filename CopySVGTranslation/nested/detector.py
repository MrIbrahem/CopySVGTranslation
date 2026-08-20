from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

logger = logging.getLogger(__name__)
SVG_NS = "http://www.w3.org/2000/svg"


class NestedTspanDetector:
    """Find repairable nested structures inside SVG ``<tspan>`` elements.

    The nested flattener only changes ``<tspan>`` elements that contain
    descendant ``<tspan>`` or ``<a>`` nodes.  An outer clickable title wrapper,
    such as ``<a><text><tspan>Title</tspan></text></a>``, is valid SVG and is
    intentionally not changed by the flattener, so it must not be reported as
    a nested structure.
    """

    def __init__(self, tags: tuple[str, ...] = ("tspan", "a")) -> None:
        """Configure descendant SVG tags that make a ``<tspan>`` repairable."""
        self.tags = tags

    def find_in_tree(self, root: etree._Element) -> list[etree._Element]:
        """Return ``<tspan>`` elements containing configured descendants.

        This criterion deliberately matches :class:`NestedTspanFlattener`.
        It keeps links nested *inside* text spans detectable while ignoring
        valid link wrappers that merely contain text or tspan elements.
        """
        result: list[etree._Element] = []
        for tspan in root.findall(f".//{{{SVG_NS}}}tspan"):
            if any(tspan.findall(f".//{{{SVG_NS}}}{tag}") for tag in self.tags):
                result.append(tspan)
        return result

    def find_in_file(self, source_file: Path | str) -> list[str]:
        """
        Parse a file and return serialised representations of nested tspans.
        Returns an empty list on parse errors.
        """
        path = Path(source_file)
        if not path.exists():
            logger.error("File does not exist: %s", path)
            return []

        try:
            parser = etree.XMLParser(
                remove_blank_text=True,
                resolve_entities=False,
                no_network=True,
            )
            tree = etree.parse(str(path), parser)
            root = tree.getroot()
            if root is None:
                return []
        except (etree.XMLSyntaxError, OSError) as exc:
            logger.error("Failed to parse %s: %s", path, exc)
            return []

        return self.find_in_tree_return_list(root)

    def find_in_tree_return_list(self, root) -> list[str]:
        nested = self.find_in_tree(root)
        return [
            etree.tostring(
                tspan,
                pretty_print=False,
            ).decode("utf-8")
            for tspan in nested
        ]

    def has_nested(self, root: etree._Element) -> bool:
        return bool(self.find_in_tree(root))


__all__ = [
    "NestedTspanDetector",
]
