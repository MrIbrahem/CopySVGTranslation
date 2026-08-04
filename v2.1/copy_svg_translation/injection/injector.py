"""Helpers for injecting translations into SVG files."""

from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

from ..config import TranslationConfig
from ..core.mapping import TranslationMapping
from ..preparation import SvgPreparationPipeline
from ..result import InjectorData, InjectorStats
from ..titles import YearTitleHandler
from ..utils.xml import tree_languages
from .id_manager import IdManager
from .switch_processor import SwitchProcessor
from .translation_applier import TranslationApplier

logger = logging.getLogger(__name__)
SVG_NS = "http://www.w3.org/2000/svg"


class SVGTranslationInjector:
    def __init__(self, config: TranslationConfig) -> None:
        self.config = config
        self.id_manager = IdManager()
        self.applier = TranslationApplier(config, self.id_manager)
        self.switch_processor = SwitchProcessor(config, self.id_manager, self.applier, YearTitleHandler(config))
        self.preparer = SvgPreparationPipeline(config)

    def _inject(
        self,
        svg_path: Path | str,
        mapping: TranslationMapping,
        *,
        save_path: Path | None = None,
        save: bool = False,
    ) -> InjectorData:
        svg_path = Path(svg_path)
        stats = InjectorStats()

        # 1. Prepare (pipeline)
        try:
            tree, root = self.preparer.run(svg_path)
        except Exception as exc:
            stats.error = f"preparation_failed: {exc}"
            return None, stats

        if tree is None or root is None:
            stats.error = "preparation_returned_none_tree"
            return None, stats

        # 2. Snapshot languages before
        before_languages = tree_languages(tree)
        stats.languages_before = sorted(before_languages)

        # 3. Seed IdManager with existing IDs
        self.id_manager.register_many(root.xpath("//@id"))

        # 4. Process every switch
        self.work_on_switches(root, mapping, stats)

        # 5. Final housekeeping
        # self._finalize_switches(root)

        # 6. Languages after + stats
        after_languages = tree_languages(tree)
        self._update_data(stats, before_languages, after_languages)

        # 7. Save if requested
        if save and save_path:
            self._save(tree, save_path)

        return tree, stats

    def inject(
        self,
        svg_path: Path | str,
        mapping: TranslationMapping,
        *,
        save_path: Path | None = None,
        save: bool = False,
    ) -> tuple[etree._ElementTree | None, InjectorStats]:
        svg_path = Path(svg_path)
        stats = InjectorStats()

        # 1. Prepare (pipeline)
        try:
            tree, root = self.preparer.run(svg_path)
        except Exception as exc:
            stats.error = f"preparation_failed: {exc}"
            return None, stats

        if tree is None or root is None:
            stats.error = "preparation_returned_none_tree"
            return None, stats

        # 2. Snapshot languages before
        before_languages = tree_languages(tree)
        stats.languages_before = sorted(before_languages)

        # 3. Seed IdManager with existing IDs
        self.id_manager.register_many(root.xpath("//@id"))

        # 4. Process every switch
        self.work_on_switches(root, mapping, stats)

        # 5. Final housekeeping
        # self._finalize_switches(root)

        # 6. Languages after + stats
        after_languages = tree_languages(tree)
        self._update_data(stats, before_languages, after_languages)

        # 7. Save if requested
        if save and save_path:
            self._save(tree, save_path)

        return tree, stats

    def work_on_switches(self, root, mapping, stats):
        switches = root.xpath("//svg:switch", namespaces={"svg": SVG_NS})
        for switch in switches:
            self.switch_processor.process(switch, mapping, stats)

    def prepare(self, svg_path: Path | str) -> etree._ElementTree:
        """Public helper used by service.prepare_only()."""
        svg_path = Path(svg_path)
        tree, _ = self.preparer.run(svg_path)
        return tree

    def _save(self, tree: etree._ElementTree, save_path: Path) -> None:
        if self.config.create_parents:
            save_path.parent.mkdir(parents=True, exist_ok=True)
        tree.write(
            str(save_path),
            encoding="utf-8",
            xml_declaration=True,
            pretty_print=self.config.pretty_print,
        )

    def _update_data(self, stats, before_languages: set[str], after_languages: set[str]) -> None:
        new_languages = after_languages - before_languages

        stats.all_languages = len(after_languages)
        stats.new_languages = len(new_languages)
        stats.languages_after = sorted(new_languages)
