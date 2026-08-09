"""
Service for detecting and repairing nested <tspan> / <a> elements in SVGs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from .detector import NestedTspanDetector
from .flattener import NestedTspanFlattener, NestedStrategy

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RepairResult:
    """
    Statistics and results of a nested structure repair operation.
    """
    success: bool
    len_tags_before_fix: int
    len_tags_after_fix: int
    warnings: list[str] = field(default_factory=list)


class NestedStructureService:
    """
    Service for analyzing and repairing nested tspan/a elements.
    """

    def __init__(self, strategy: NestedStrategy = "preserve_style", also_fix_a: bool = True) -> None:
        self.strategy = strategy
        self.also_fix_a = also_fix_a
        self.detector = NestedTspanDetector()
        self.flattener = NestedTspanFlattener(strategy=strategy, also_fix_a=also_fix_a)

    def analyze(self, source: Path | str | etree._Element) -> list[str]:
        """
        Detect nested tspan/a structures. Read-only.
        Returns a list of XML strings representing the nested elements found.
        """
        if isinstance(source, (Path, str)):
            path = Path(source)
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
                return self.detector.find_in_tree_return_list(root)
            except (etree.XMLSyntaxError, OSError) as exc:
                logger.error("Failed to parse %s: %s", path, exc)
                return []
        else:
            return self.detector.find_in_tree_return_list(source)

    def repair(
        self,
        source: Path | str | etree._Element | etree._ElementTree,
        strategy: NestedStrategy | None = None,
    ) -> etree._ElementTree:
        """
        Repair nested structures in-place or from a file.
        Returns an etree._ElementTree object containing the repaired SVG.
        """
        chosen_strategy = strategy or self.strategy
        flattener = self.flattener if chosen_strategy == self.strategy else NestedTspanFlattener(strategy=chosen_strategy, also_fix_a=self.also_fix_a)

        if isinstance(source, (Path, str)):
            path = Path(source)
            parser = etree.XMLParser(
                remove_blank_text=False,
                resolve_entities=False,
                no_network=True,
            )
            tree = etree.parse(str(path), parser)
            root = tree.getroot()
            if root is not None:
                flattener.process(root)
            return tree
        elif isinstance(source, etree._ElementTree):
            root = source.getroot()
            if root is not None:
                flattener.process(root)
            return source
        else:
            # It's an _Element
            flattener.process(source)
            # Find or construct its tree
            tree = source.getroottree()
            if tree is None:
                tree = etree.ElementTree(source)
            return tree

    def repair_file(
        self,
        source: Path | str,
        output: Path | str,
        strategy: NestedStrategy | None = None,
    ) -> RepairResult:
        """
        Repair nested tags in a file and write the result to another file.
        """
        src_path = Path(source)
        out_path = Path(output)
        warnings: list[str] = []

        if not src_path.exists():
            return RepairResult(
                success=False,
                len_tags_before_fix=0,
                len_tags_after_fix=0,
                warnings=[f"Source file does not exist: {src_path}"],
            )

        try:
            # Parse source file
            parser = etree.XMLParser(
                remove_blank_text=False,
                resolve_entities=False,
                no_network=True,
            )
            tree = etree.parse(str(src_path), parser)
            root = tree.getroot()

            if root is None:
                return RepairResult(
                    success=False,
                    len_tags_before_fix=0,
                    len_tags_after_fix=0,
                    warnings=["Empty SVG root"],
                )

            # Count before fix
            len_before = len(self.detector.find_in_tree(root))

            # Apply repair
            chosen_strategy = strategy or self.strategy
            flattener = self.flattener if chosen_strategy == self.strategy else NestedTspanFlattener(strategy=chosen_strategy, also_fix_a=self.also_fix_a)
            flattener.process(root)

            # Count after fix
            len_after = len(self.detector.find_in_tree(root))

            # Write out
            _str = etree.tostring(
                root,
                encoding="unicode",
                pretty_print=None,
            )
            out_path.write_text(_str, encoding="utf-8")

            return RepairResult(
                success=True,
                len_tags_before_fix=len_before,
                len_tags_after_fix=len_after,
                warnings=warnings,
            )

        except Exception as exc:
            logger.error("Failed to repair file %s: %s", src_path, exc)
            return RepairResult(
                success=False,
                len_tags_before_fix=0,
                len_tags_after_fix=0,
                warnings=[str(exc)],
            )


__all__ = [
    "RepairResult",
    "NestedStructureService",
]
