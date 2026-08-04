"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path

from lxml import etree

from ..config import TranslationConfig
from ..exceptions import (
    SvgNestedTspanError,
    SvgStructureError,
)
from ..preparation import SvgPreparationPipeline
from ..result import InjectorData, InjectorStats
from ..utils import (
    sort_switch_texts,
    tree_languages,
)
from .switch_processor import SwitchProcessor

logger = logging.getLogger(__name__)
SVG_NS = "http://www.w3.org/2000/svg"


class SVGTranslationInjector:
    """Injects translations into SVG files."""

    def __init__(
        self,
        config: TranslationConfig | None = None,
    ) -> None:
        """ """

        self.config = config or TranslationConfig()
        self.preparer = SvgPreparationPipeline(self.config)
        self.switch_processor = SwitchProcessor(self.config.overwrite, self.config.case_insensitive)

    def _parse_svg(
        self, inject_path, stats: InjectorStats
    ) -> tuple[etree._ElementTree, etree._Element] | tuple[None, None]:
        try:
            tree, root = self.preparer.run(inject_path)
            return tree, root

        except SvgNestedTspanError as exc:
            stats.error = "nested_tspan_error"

        except SvgStructureError as exc:
            stats.error = str(exc)

        except etree.XMLSyntaxError as exc:
            logger.error("Failed with XMLSyntaxError when parse SVG file: %s", exc)
            stats.error = str(exc)

        except Exception as exc:
            logger.error("Failed to parse SVG file: %s", exc)
            stats.error = str(exc)

        return None, None

    def _finalize_switches(self, root) -> None:
        # Fix old <svg:switch> tags if present
        for elem in root.findall(".//svg:switch", namespaces={"svg": SVG_NS}):
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
        result = InjectorData()

        inject_path = Path(str(inject_file))

        if not inject_path.exists():
            logger.error(f"SVG file not found: {inject_path}")
            result.new_stats.error = "File does not exist"
            return result

        if not all_mappings:
            logger.error("No valid mappings found")
            result.new_stats.error = "No valid mappings found"
            return result

        logger.debug(f"Injecting translations into {inject_path}")
        stats = result.new_stats
        # 1. Prepare (pipeline)
        try:
            tree, root = self._parse_svg(inject_path, result.new_stats)
        except Exception as exc:
            stats.error = f"preparation_failed: {exc}"
            return result

        if tree is None or root is None:
            stats.error = "preparation_returned_none_tree"
            return result

        result.tree = tree

        # 2. Snapshot languages before
        before_languages = tree_languages(tree)
        stats.languages_before = sorted(before_languages)

        # 4. Process every switch
        self.work_on_switches(
            root=root,
            mapping=all_mappings,
            stats=stats,
        )

        # 5. Final housekeeping
        self._finalize_switches(root)

        # 6. Languages after + stats
        after_languages = tree_languages(tree)
        self._update_data(stats, before_languages, after_languages)

        if not save_result:
            return result

        # 7. Save if requested
        if save_path is None:
            logger.error("save_result is True but no save_path was provided")
            result.new_stats.error = "No target path provided"
            return result

        try:
            self._save(tree, save_path)
        except OSError as e:
            logger.error(f"Failed writing {str(save_path)}: {e}")
            result.new_stats.error = f"Failed writing {str(save_path)}: {e}"

        return result

    def work_on_switches(
        self,
        root: etree._Element,
        mapping: Mapping,
        existing_ids: set[str] | None = None,
        stats: InjectorStats | None = None,
    ) -> InjectorStats:
        """Process ``<switch>`` elements and insert or update translations."""
        if not stats:
            stats = InjectorStats()

        if not existing_ids:
            # Collect all existing IDs to ensure uniqueness
            # existing_ids = {elem.get('id') for elem in root.xpath('//*[@id]') if elem.get('id')}
            existing_ids = set(root.xpath("//@id"))

        # Process every switch
        switches = root.xpath("//svg:switch", namespaces={"svg": SVG_NS})
        logger.debug("Found %s switch elements", len(switches))

        for switch in switches:
            self.switch_processor.process(
                switch_element=switch,
                mapping=mapping,
                stats=stats,
                existing_ids=existing_ids,
            )
        return stats

    def prepare(self, svg_path: Path | str) -> etree._ElementTree:
        """Public helper used by service.prepare_only()."""
        svg_path = Path(svg_path)
        tree, _ = self.preparer.run(svg_path)
        return tree

    def _save(
        self,
        tree: etree._ElementTree,
        save_path: Path,
    ) -> None:
        tree.write(
            str(save_path),
            encoding="utf-8",
            xml_declaration=True,
            pretty_print=self.config.pretty_print,
        )
        logger.debug(f"Saved modified SVG to {save_path}")

    def _update_data(
        self,
        stats: InjectorStats,
        before_languages: set[str],
        after_languages: set[str],
    ) -> None:
        new_languages = after_languages - before_languages

        stats.all_languages = len(after_languages)
        stats.new_languages = len(new_languages)
        stats.languages_after = sorted(new_languages)

        logger.debug(f"Processed {stats.processed_switches} switches")
        logger.debug(f"Inserted {stats.inserted_translations} translations")
        logger.debug(f"Updated {stats.updated_translations} translations")
        logger.debug(f"Skipped {stats.skipped_translations} existing translations")


__all__ = [
    "SVGTranslationInjector",
]
