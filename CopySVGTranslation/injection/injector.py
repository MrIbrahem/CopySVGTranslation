"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

from ..config import TranslationConfig
from ..core.mapping import InjectorData, TranslationMapping
from ..exceptions import (
    SvgNestedTspanError,
    SvgStructureError,
)
from ..io import SvgDocument
from ..preparation import SvgPreparationPipeline
from ..result import InjectorStats
from ..titles import YearTitleHandler
from ..utils import sort_switch_texts
from ..utils.xml import extract_root_languages
from .id_manager import IdManager
from .switch_processor import SwitchProcessor
from .translation_applier import TranslationApplier

logger = logging.getLogger(__name__)
SVG_NS = "http://www.w3.org/2000/svg"


class SVGTranslationInjector:
    """Injects translations into SVG files."""

    def __init__(
        self,
        config: TranslationConfig | None = None,
    ) -> None:
        self.config = config or TranslationConfig()
        self.preparer = SvgPreparationPipeline(self.config)

        self.id_manager = IdManager()
        self.applier = TranslationApplier(self.config, self.id_manager)
        self.switch_processor = SwitchProcessor(
            self.config,
            self.id_manager,
            self.applier,
            YearTitleHandler(self.config),
        )

    def _finalize_switches(self, root: etree._Element) -> None:
        if not self.config.sort_switches:
            return

        for elem in root.findall(".//svg:switch", namespaces={"svg": SVG_NS}):
            # Fix old <svg:switch> tags if present
            elem.tag = "switch"

            # Sort <svg:text> tags inside <svg:switch> tags
            sort_switch_texts(elem)

    def inject(
        self,
        svg_path: Path | str,
        mapping: TranslationMapping | dict,
        *,
        save_path: Path | None = None,
        save: bool = False,
    ) -> InjectorData:
        """
        Inject translations into the provided SVG file.
        """
        result = InjectorData()

        svg_path = Path(str(svg_path))

        if not svg_path.exists():
            logger.error(f"SVG file not found: {svg_path}")
            result.error.label = "File does not exist"
            return result

        if not mapping:
            logger.error("No valid mappings found")
            result.error.label = "No valid mappings found"
            return result

        logger.debug(f"Injecting translations into {svg_path}")

        # 1. Prepare (pipeline)
        try:
            tree, root = self.preparer.run(svg_path)
        except SvgNestedTspanError as exc:
            result.error.code = "nested_tspan_error"
            return result

        except SvgStructureError as exc:
            result.error.from_error(exc)
            return result

        except etree.XMLSyntaxError as exc:
            logger.error("Failed with XMLSyntaxError when parse SVG file: %s", exc)
            result.error.from_error(exc)
            return result

        except Exception as exc:
            logger.error("Failed to parse SVG file: %s", exc)
            result.error.from_error(exc)
            return result

        if tree is None or root is None:
            result.error.code = "preparation_returned_none_tree"
            return result

        result.tree = tree

        # 2. Snapshot languages before
        before_languages = extract_root_languages(root)
        result.inject_stats.languages_before = sorted(before_languages)

        # 3. Seed IdManager with existing IDs
        self.id_manager.register_many(root.xpath("//@id"))

        # 4. Process every switch
        mapping_obj = TranslationMapping.from_any(mapping)

        self.work_on_switches(
            root=root,
            mapping=mapping_obj,
            stats=result.inject_stats,
        )

        # 5. Final housekeeping
        self._finalize_switches(root)

        # 6. Languages after + stats
        after_languages = extract_root_languages(root)
        self._update_data(result.inject_stats, before_languages, after_languages)

        if save:
            # 7. Save if requested
            if save_path is None:
                logger.error("save is True but no save_path was provided")
                result.error.label = "No target path provided"
                return result

            try:
                doc = SvgDocument(tree=tree, path=save_path, config=self.config)
                doc.save()
            except OSError as e:
                logger.error(f"Failed writing {str(save_path)}: {e}")
                result.error.label = f"Failed writing {str(save_path)}: {e}"

        return result

    def work_on_switches(
        self,
        root: etree._Element,
        mapping: TranslationMapping | dict,
        existing_ids: set[str] | None = None,
        stats: InjectorStats | None = None,
    ) -> InjectorStats:
        """Process ``<switch>`` elements and insert or update translations."""
        mapping = TranslationMapping.from_any(mapping)
        if not stats:
            stats = InjectorStats()

        if existing_ids:
            self.id_manager.register_many(existing_ids)

        # Process every switch
        switches = root.xpath("//svg:switch", namespaces={"svg": SVG_NS})
        logger.debug("Found %s switch elements", len(switches))

        for switch in switches:
            self.switch_processor.process(
                switch_element=switch,
                mapping=mapping,
                stats=stats,
            )
        return stats

    def prepare(self, svg_path: Path | str) -> etree._ElementTree:
        """Public helper used by service.prepare_only()."""
        svg_path = Path(svg_path)
        tree, _ = self.preparer.run(svg_path)
        return tree

    def _update_data(
        self,
        stats: InjectorStats,
        before_languages: set[str],
        after_languages: set[str],
    ) -> None:
        new_languages_count = after_languages - before_languages

        stats.all_languages_count = len(after_languages)
        stats.new_languages_count = len(new_languages_count)
        stats.languages_after = sorted(new_languages_count)

        logger.debug(f"Processed {stats.processed_switches} switches")
        logger.debug(f"Inserted {stats.inserted_translations} translations")
        logger.debug(f"Updated {stats.updated_translations} translations")
        logger.debug(f"Skipped {stats.skipped_translations} existing translations")

        logger.debug(f"All langs: {stats.all_languages_count}")
        logger.debug(f"New langs: {stats.new_languages_count}")


__all__ = [
    "SVGTranslationInjector",
]
