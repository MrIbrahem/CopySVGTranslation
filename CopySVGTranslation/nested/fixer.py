from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

from .detector import NestedTspanDetector
from .flattener import NestedTspanFlattener

logger = logging.getLogger(__name__)


class MatchFixNestedTags:
    def __init__(
        self,
        source_file: Path | str,
        new_path: Path | str,
        pretty_print: bool | None = None,
        strategy: str = "flatten",
        also_fix_a: bool = True,
    ) -> None:
        self.source_file = Path(source_file)
        self.new_path = Path(new_path)
        self.pretty_print = pretty_print
        self.flattener = NestedTspanFlattener(strategy=strategy, also_fix_a=also_fix_a)
        self.detector = NestedTspanDetector()

        self.len_tags_before_fix = 0

    def _flatten_all(self, root):
        # Process nested tspans using Flattener
        self.flattener.process(root)
        return root

    def _get_root(self):
        parser = etree.XMLParser(remove_blank_text=False)
        # ---
        try:
            tree = etree.parse(str(self.source_file), parser)
        except (etree.XMLSyntaxError, OSError) as exc:
            logger.error(f"Failed to parse SVG file {self.source_file}: {exc}")
            return None
        # ---
        root = tree.getroot()
        return root

    def _save_file(self, root: etree.Element) -> None:
        _str = etree.tostring(
            root,
            encoding="unicode",
            pretty_print=self.pretty_print,
        )  # pyright: ignore[reportCallIssue]

        self.new_path.write_text(_str, encoding="utf-8")

    def match_nested(self) -> list:
        return self.detector.find_in_file(self.source_file)

    def fix_file(self) -> bool:
        # ---
        root = self._get_root()
        # ---
        if root is None:
            return False
        # ---
        self.len_tags_before_fix = len(self.detector.find_in_tree(root))
        # ---
        root = self._flatten_all(root)
        # ---
        try:
            self._save_file(root)
            return True
        except Exception:
            logger.error(f"Failed to write fixed svg file to: {str(self.new_path)}")
        # ---
        return False


__all__ = [
    "MatchFixNestedTags",
]
