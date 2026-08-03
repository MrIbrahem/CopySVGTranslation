# injection/injector.py
from __future__ import annotations

import logging
from pathlib import Path

from lxml import etree

from ..config import TranslationConfig
from ..core.mapping import TranslationMapping
from ..result import InjectorStats
from ..titles.year_handler import YearTitleHandler
from ..utils.xml import tree_languages
from .id_manager import IdManager
from ..preparation import SvgPreparationPipeline
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

        # 1. Prepare SVG
        try:
            tree, root = self.preparer.run(svg_path)
        except Exception as exc:
            stats.error = f"preparation_failed: {exc}"
            return None, stats

        if tree is None:
            stats.error = "preparation_returned_none_tree"
            return None, stats

        # 2. Track existing languages
        before = tree_languages(tree)
        stats.languages_before = sorted(before)

        # 3. Seed ID Manager
        self.id_manager.register_many(root.xpath("//@id"))

        # 4. Inject
        switches = root.xpath("//svg:switch", namespaces={"svg": SVG_NS})
        for switch in switches:
            self.switch_processor.process(switch, mapping, stats)

        # 5. Save if requested
        after = tree_languages(tree)
        stats.languages_after = sorted(after - before)
        stats.all_languages = len(after)
        stats.new_languages = len(after - before)

        if save and save_path:
            self._save(tree, save_path)

        return tree, stats

    def prepare(self, svg_path: Path | str) -> etree._ElementTree:
        svg_path = Path(svg_path)
        tree, _ = self.preparer.run(svg_path)
        return tree

    def _save(self, tree: etree._ElementTree, path: Path) -> None:
        if self.config.create_parents:
            path.parent.mkdir(parents=True, exist_ok=True)
        tree.write(
            str(path),
            encoding="utf-8",
            xml_declaration=True,
            pretty_print=self.config.pretty_print,
        )
