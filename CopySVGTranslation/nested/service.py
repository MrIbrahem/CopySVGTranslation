"""
Service for detecting and repairing nested <tspan> / <a> elements in SVGs.
"""

from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

from ..config import TranslationConfig
from ..exceptions import SvgStructureError
from ..io import SvgDocument
from .detector import NestedTspanDetector
from .flattener import NestedStrategy, NestedTspanFlattener
from .objects import RepairResult

logger = logging.getLogger(__name__)


class NestedStructureService:
    """
    Service for analyzing and repairing nested tspan/a elements.
    """

    def __init__(
        self,
        strategy: NestedStrategy = "flatten",
        also_fix_a: bool = True,
        config: TranslationConfig | None = None,
    ) -> None:
        self.strategy = strategy
        self.also_fix_a = also_fix_a
        self.config = config or TranslationConfig()
        self.detector = NestedTspanDetector()
        self.flattener = NestedTspanFlattener(strategy=strategy, also_fix_a=also_fix_a)

    def analyze_file(
        self,
        source: Path | str,
    ) -> list[str]:
        """
        Detect nested tspan/a structures. Read-only.
        Returns a list of XML strings representing the nested elements found.
        """
        try:
            doc: SvgDocument = SvgDocument.load(source, config=self.config)
        except FileNotFoundError:
            logger.error("File does not exist: %s", source)
            return []
        except SvgStructureError as exc:
            logger.error(f"Failed to parse SVG file {source}: {exc.code}")
            return []

        if doc.tree is None:
            return []

        try:
            return self.detector.find_in_tree_return_list(doc.root)
        except Exception as exc:
            logger.error("Failed to parse %s: %s", source, exc)
            return []

    def repair_file(
        self,
        source: Path | str,
        output: Path | str | None = None,
        strategy: NestedStrategy | None = None,
        save: bool = True,
    ) -> RepairResult:
        """
        Repair nested tags in a file and write the result to another file.
        """
        src_path = Path(str(source)) if source else None

        try:
            doc: SvgDocument = SvgDocument.load(src_path, config=self.config)
        except FileNotFoundError:
            logger.error(f"SVG file not found: {src_path}")
            return RepairResult.fail(
                warnings=[f"Source file does not exist: {src_path}"],
            )
        except SvgStructureError as exc:
            logger.error(f"Failed to parse SVG file {src_path}: {exc.code}")
            return RepairResult.fail(
                warnings=[f"Failed to parse source file: {src_path}"],
            )

        if doc.tree is None:
            return RepairResult.fail(
                warnings=[f"Failed to parse source file: {src_path}"],
            )
        root = doc.root

        if root is None:
            return RepairResult.fail(warnings=["Empty SVG root"])

        result = self.repair_root(root, strategy)

        if result.success and save:
            out_path = Path(output) if output else src_path
            # Write out
            if not out_path:
                raise ValueError("new_path is None")

            doc = SvgDocument(
                tree=etree.ElementTree(root),
                path=out_path,
                config=self.config,
            )
            doc.save()
        return result

    def repair_root(
        self,
        root: etree._Element | None,
        strategy: NestedStrategy | None = None,
    ) -> RepairResult:
        if root is None:
            return RepairResult.fail(
                warnings=["Empty SVG root"],
            )

        try:
            # Count before fix
            len_before = len(self.detector.find_in_tree(root))

            # Apply repair
            chosen_strategy = strategy or self.strategy

            flattener = self.flattener
            if chosen_strategy != self.strategy:
                flattener = NestedTspanFlattener(strategy=chosen_strategy, also_fix_a=self.also_fix_a)

            root = flattener.process(root)

            # Count after fix
            len_after = len(self.detector.find_in_tree(root))

            result = RepairResult.ok(
                len_before=len_before,
                len_after=len_after,
            )

        except Exception as exc:
            logger.error("Failed to repair: %s", exc)
            result = RepairResult.fail(
                warnings=[str(exc)],
            )

        return result


__all__ = [
    "NestedStructureService",
]
