"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path

from lxml import etree

from ..preparation import SvgPreparationPipeline
from ..utils import (
    sort_switch_texts,
    tree_languages,
)
from .exceptions import (
    SvgNestedTspanExceptionError,
    SvgStructureExceptionError,
)
from .objects import InjectorData, InjectorStats
from .switch_processor import SwitchProcessor

logger = logging.getLogger(__name__)


class SVGTranslationInjector:
    """Injects translations into SVG files."""

    def __init__(
        self,
        case_insensitive: bool = True,
        overwrite: bool = False,
        pretty_print: bool | None = None,
    ) -> None:
        """
        Parameters:
            case_insensitive (bool): If True, translation lookups are
                case-insensitive (keys are lowercased).
            overwrite (bool): If True, existing language nodes are updated
                in place instead of being skipped.
        """
        self.case_insensitive = case_insensitive
        self.overwrite = overwrite
        self.pretty_print = pretty_print
        self.result = InjectorData()
        self.new_stats: InjectorStats = self.result.new_stats

        self.switch_processor = SwitchProcessor(self.overwrite, self.case_insensitive)

    def work_on_switches(
        self,
        root: etree._Element,
        mappings: Mapping,
        existing_ids: set[str] | None = None,
    ) -> None:
        """Process ``<switch>`` elements and insert or update translations."""
        svg_ns = {"svg": "http://www.w3.org/2000/svg"}

        if not existing_ids:
            # Collect all existing IDs to ensure uniqueness
            # existing_ids = {elem.get('id') for elem in root.xpath('//*[@id]') if elem.get('id')}
            existing_ids = set(root.xpath("//@id"))

        # 4. Process every switch
        switches = root.xpath("//svg:switch", namespaces=svg_ns)
        logger.debug(f"Found {len(switches)} switch elements")
        for switch in switches:
            self.switch_processor.process(switch, mappings, self.new_stats, existing_ids)

    def _parse_svg(self, inject_path) -> tuple[etree._ElementTree, etree._Element] | tuple[None, None]:
        try:
            preparer = SvgPreparationPipeline(inject_path)
            tree, root = preparer.run(inject_path)
            return tree, root

        except SvgNestedTspanExceptionError as exc:
            self.new_stats.error = "nested_tspan_error"

        except SvgStructureExceptionError as exc:
            self.new_stats.error = str(exc)

        except etree.XMLSyntaxError as exc:
            logger.error("Failed with XMLSyntaxError when parse SVG file: %s", exc)
            self.new_stats.error = str(exc)

        except Exception as exc:
            logger.error("Failed to parse SVG file: %s", exc)
            self.new_stats.error = str(exc)

        return None, None

    def _fix_old_switches(self, root) -> None:
        # Fix old <svg:switch> tags if present
        for elem in root.findall(".//svg:switch", namespaces={"svg": "http://www.w3.org/2000/svg"}):
            elem.tag = "switch"
            sort_switch_texts(elem)

    def inject(
        self,
        inject_file: Path | str,
        all_mappings: Mapping | None = None,
        *,
        save_path: Path | None = None,
        save_result: bool = False,
    ) -> InjectorData:
        """Inject translations into the provided SVG file."""

        # Reset state to prevent accumulation across calls
        self.result = InjectorData()
        self.new_stats = self.result.new_stats

        inject_path = Path(str(inject_file))

        if not inject_path.exists():
            logger.error(f"SVG file not found: {inject_path}")
            self.new_stats.error = "File does not exist"
            return self.result

        if not all_mappings:
            logger.error("No valid mappings found")
            self.new_stats.error = "No valid mappings found"
            return self.result

        logger.debug(f"Injecting translations into {inject_path}")
        stats = self.new_stats
        # 1. Prepare (pipeline)
        try:
            tree, root = self._parse_svg(inject_path)
        except Exception as exc:
            stats.error = f"preparation_failed: {exc}"
            return self.result

        if tree is None or root is None:
            stats.error = "preparation_returned_none_tree"
            return self.result

        self.result.tree = tree

        # 2. Snapshot languages before
        before_languages = tree_languages(tree)
        stats.languages_before = sorted(before_languages)

        # 4. Process every switch
        self.work_on_switches(root=root, mappings=all_mappings)

        self._fix_old_switches(root=root)

        # 6. Languages after + stats
        after_languages = tree_languages(tree)
        self._update_data(before_languages, after_languages)

        # 7. Save if requested
        if save_result:
            self._save(save_path, inject_path.name, tree)

        return self.result

    def _save(
        self,
        save_path: Path | None,
        inject_file_name: str,
        tree: etree._ElementTree,
    ) -> None:
        if save_path is None:
            logger.error("save_result is True but no save_path was provided")
            self.new_stats.error = "No target path provided"
            return

        try:
            tree.write(
                str(save_path),
                encoding="utf-8",
                xml_declaration=True,
                pretty_print=self.pretty_print,
            )
            logger.debug(f"Saved modified SVG to {save_path}")
        except OSError as e:
            logger.error(f"Failed writing {inject_file_name}: {e}")
            self.new_stats.error = f"Failed writing {inject_file_name}: {e}"
            self.result.tree = None

    def _update_data(self, before_languages: set[str], after_languages: set[str]) -> None:
        new_languages = after_languages - before_languages

        self.new_stats.all_languages = len(after_languages)
        self.new_stats.new_languages = len(new_languages)
        self.new_stats.languages_after = sorted(new_languages)

        logger.debug(f"Processed {self.new_stats.processed_switches} switches")
        logger.debug(f"Inserted {self.new_stats.inserted_translations} translations")
        logger.debug(f"Updated {self.new_stats.updated_translations} translations")
        logger.debug(f"Skipped {self.new_stats.skipped_translations} existing translations")


__all__ = [
    "SVGTranslationInjector",
]
