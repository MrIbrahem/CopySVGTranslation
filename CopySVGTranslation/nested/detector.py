from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

from ..config import TranslationConfig
from ..exceptions import SvgStructureError
from ..io import SvgDocument

logger = logging.getLogger(__name__)

SVG_NS = "http://www.w3.org/2000/svg"


class NestedTspanDetector:
    """
    Find repairable nested structures inside SVG ``<tspan>`` elements.

    The nested flattener only changes ``<tspan>`` elements that contain
    descendant ``<tspan>`` or ``<a>`` nodes.  An outer clickable title wrapper,
    such as ``<a><text><tspan>Title</tspan></text></a>``, is valid SVG and is
    intentionally not changed by the flattener, so it must not be reported as
    a nested structure.
    """

    def __init__(self, tags: tuple[str, ...] = ("tspan", "a")) -> None:
        """
        Configure descendant SVG tags that make a ``<tspan>`` repairable.
        """
        self.tags = tags

    def find_in_tree(self, root: etree._Element) -> list[etree._Element]:
        """
        Return all tspan elements that have element children.
        """
        result: list[etree._Element] = []

        # Find all <tspan> elements
        tspans = root.findall(f".//{{{SVG_NS}}}tspan")
        for tspan in tspans:
            # Check if <tspan> has element children (nested tags)
            element_children = [c for c in tspan if isinstance(c.tag, str)]
            if element_children:
                result.append(tspan)

        return result

    def find_in_file(self, source_file: Path | str) -> list[str]:
        """
        Parse a file and return serialised representations of nested tspans.
        Returns an empty list on parse errors.
        """
        try:
            config = TranslationConfig(remove_blank_text=True)
            doc: SvgDocument = SvgDocument.load(source_file, config=config)
        except FileNotFoundError:
            logger.error("File does not exist: %s", source_file)
            return []
        except SvgStructureError as exc:
            logger.error(f"Failed to parse SVG file {source_file}: {exc.code}")
            return []

        root = doc.root
        if doc.tree is None or root is None:
            return []

        return self.find_in_tree_return_list(root)

    def find_in_tree_return_list(self, root: etree._Element) -> list[str]:
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
