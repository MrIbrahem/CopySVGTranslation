# injection/switch_processor.py
from __future__ import annotations

import logging

from lxml import etree

from ..config import TranslationConfig
from ..core.mapping import TranslationMapping
from ..core.switch_node import SwitchNode
from ..core.text_node import TextNode
from ..result import InjectorStats
from ..titles import YearTitleHandler
from .id_manager import IdManager
from .translation_applier import TranslationApplier

logger = logging.getLogger(__name__)
SVG_NS = "http://www.w3.org/2000/svg"


class SwitchProcessor:
    def __init__(
        self,
        config: TranslationConfig,
        id_manager: IdManager,
        applier: TranslationApplier,
        year_handler: YearTitleHandler | None = None,
    ) -> None:
        self.config = config
        self.id_manager = id_manager
        self.applier = applier
        self.year_handler = year_handler or YearTitleHandler(config)

    def process(
        self,
        switch_element: etree._Element,
        mapping: TranslationMapping | dict,
        stats: InjectorStats,
    ) -> None:
        """
        1. Find fallback (default) <text> node
        2. Extract default_texts
        3. Enrich mapping with year-title expansions (if enabled)
        4. Collect existing languages in this switch
        5. For every language present in the mapping:
              - decide skip / update / insert
              - call TranslationApplier
              - update stats
        6. Optionally re-sort children of the switch
        """
        mapping = TranslationMapping.from_any(mapping)
        switch = SwitchNode(switch_element)
        default: TextNode | None = switch.default_text_node()
        if default is None:
            return

        # Find all text elements within this switch
        default_texts = default.texts(
            normalize=True,
            case_insensitive=self.config.case_insensitive,
        )

        # If there are no default texts, we can't do anything
        if not any(default_texts):
            return

        # Enrich mapping with year-title logic
        working_mapping = self.enrich_all_mappings(mapping, default_texts)

        # Collect translation mappings per-language for this fallback
        # We assume all texts share same set of languages
        langs_to_process = working_mapping.all_languages()
        langs_to_process = sorted(langs_to_process)

        if not langs_to_process:
            return

        # Gather existing translation nodes
        switch.existing_languages()

        stats.processed_switches += 1

        for lang in langs_to_process:
            # Build target translation dict
            translations_for_lang: dict[str, str] = {}
            has_any_translation = False
            for src in default_texts:
                resolved = working_mapping.lookup(src, case_insensitive=self.config.case_insensitive)
                trans = resolved.get(lang)
                if trans is not None:
                    translations_for_lang[src] = trans
                    has_any_translation = True
                else:
                    translations_for_lang[src] = src  # fallback to default text segment

            if not has_any_translation:
                continue

            existing_node = switch.find_by_language(lang)
            res = self.applier.apply_language(
                default.element,
                default_texts,
                lang,
                translations_for_lang,
                existing_node.element if existing_node is not None else None,
            )

            if res.action == "inserted" and res.node is not None:
                switch.append(TextNode(res.node))
                stats.inserted_translations += 1
            elif res.action == "updated":
                stats.updated_translations += 1
            elif res.action == "skipped":
                stats.skipped_translations += 1

        # Sort the switch elements deterministically
        switch.reorder(put_fallback_last=True)

    # -------------
    #  enrich mappings
    # -------------
    def enrich_all_mappings(self, mapping, default_texts) -> TranslationMapping:
        return self.year_handler.enrich_mapping_for_switch(
            mapping,
            default_texts,
            case_insensitive=self.config.case_insensitive,
        )


__all__ = [
    "SwitchProcessor",
]
