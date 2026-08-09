from __future__ import annotations

import logging
import warnings
from pathlib import Path

from lxml import etree

from .detector import NestedTspanDetector
from .flattener import NestedTspanFlattener
from .service import NestedStructureService

logger = logging.getLogger(__name__)


class MatchFixNestedTags:
    """
    Deprecated legacy wrapper. Use NestedStructureService instead.
    """

    def __init__(
        self,
        source_file: Path | str | None,
        new_path: Path | str | None,
        pretty_print: bool | None = None,
        strategy: str = "flatten",
        also_fix_a: bool = True,
    ) -> None:
        warnings.warn(
            "MatchFixNestedTags is deprecated and will be removed in a future version. "
            "Use NestedStructureService instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.source_file = Path(source_file) if source_file else None
        self.new_path = Path(new_path) if new_path else None
        self.pretty_print = pretty_print
        self.strategy = strategy
        self.also_fix_a = also_fix_a

        self.service = NestedStructureService(strategy=strategy, also_fix_a=also_fix_a)
        self.flattener = self.service.flattener
        self.detector = self.service.detector

        self.len_tags_before_fix = 0
        self.root: etree._Element | None = None

    def _get_root(self) -> etree._Element | None:
        if self.root is not None:
            return self.root

        if not self.source_file:
            return None

        parser = etree.XMLParser(
            remove_blank_text=False,
            resolve_entities=False,
        )
        try:
            tree = etree.parse(str(self.source_file), parser)
            self.root = tree.getroot()
            return self.root
        except (etree.XMLSyntaxError, OSError) as exc:
            logger.error(f"Failed to parse SVG file {self.source_file}: {exc}")
            return None

    def _flatten_all(self, root: etree._Element) -> etree._Element:
        self.flattener.process(root)
        return root

    def _save_file(self, root: etree._Element) -> None:
        _str = etree.tostring(
            root,
            encoding="unicode",
            pretty_print=self.pretty_print,
        )  # pyright: ignore[reportCallIssue]

        if self.new_path is None:
            raise Exception("new_path is None")

        self.new_path.write_text(_str, encoding="utf-8")

    def match_nested(self) -> list[str]:
        root = self._get_root()
        if root is None:
            return []
        return self.service.analyze(root)

    def fix_file(self) -> bool:
        root = self._get_root()
        if root is None:
            return False

        self.len_tags_before_fix = len(self.detector.find_in_tree(root))
        self.service.repair(root, strategy=self.strategy)

        try:
            self._save_file(root)
            return True
        except Exception:
            logger.error(f"Failed to write fixed svg file to: {str(self.new_path)}")
        return False


__all__ = [
    "MatchFixNestedTags",
]
