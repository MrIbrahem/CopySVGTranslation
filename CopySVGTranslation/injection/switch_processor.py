# injection/switch_processor.py
from __future__ import annotations

import logging
from typing import Any

from lxml import etree

from ..config import TranslationConfig
from ..core.mapping import TranslationMapping
from ..core.switch_node import SwitchNode
from ..core.text_node import TextNode
from ..result import InjectorStats
from ..titles import YearTitleHandler
from ..utils import normalize_text
from .id_manager import IdManager
from .translation_applier import TranslationApplier

logger = logging.getLogger(__name__)
SVG_NS = "http://www.w3.org/2000/svg"


def _extract_text_from_node(node: etree._Element | None) -> list[str]:
    """Extract text content from an SVG ``<text>`` element, honouring ``<tspan>``."""
    if node is None:
        return []

    tspans = node.xpath("./svg:tspan", namespaces={"svg": SVG_NS})
    if tspans:
        return [tspan.text.strip() if tspan.text else "" for tspan in tspans]

    return [node.text.strip()] if node.text else [""]


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

        text_elements = switch_element.xpath("./svg:text", namespaces={"svg": SVG_NS})

        if not text_elements:
            return

        # Find all text elements within this switch
        default_node = self.get_default_node(text_elements)
        default_texts = self.get_default_texts(default_node)
        # _default_texts = default.texts(
        #     normalize=True,
        #     case_insensitive=self.config.case_insensitive,
        # )

        # assert _default_texts != default_texts

        # If there are no default texts, we can't do anything
        if not default_texts or default_node is None:
            return

        # Enrich mapping with year-title logic
        working_mapping = self.enrich_all_mappings(mapping, default_texts)

        # Determine translations for each text line
        available_translations = self.get_available_translations(default_texts, working_mapping.new)

        if not available_translations:
            return

        # Collect translation mappings per-language for this fallback
        # We assume all texts share same set of languages
        langs_to_process = self.all_languages(available_translations)
        if not langs_to_process:
            return

        # Gather existing translation nodes
        existing_languages = self.get_existing_languages(text_elements)

        for lang in langs_to_process:
            if lang in existing_languages:
                if not self.config.overwrite:
                    stats.skipped_translations += 1
                    continue

                # update node
                for text_elem in text_elements:
                    if text_elem.get("systemLanguage") == lang:
                        self.update_node(text_elem, default_texts, available_translations, lang)
                        break

                stats.updated_translations += 1
                continue

            # Create node
            new_node = self.create_node(default_node, working_mapping.new, lang)
            stats.inserted_translations += 1
            switch_element.append(new_node)

        stats.processed_switches += 1

    # -------------
    # default_texts
    # -------------
    def get_default_node(self, text_elements: list[etree._Element]) -> Any | None:

        for node in text_elements:
            system_lang = node.get("systemLanguage")
            if system_lang:
                continue

            return node

        return None

    def get_default_texts(self, node: etree._Element) -> list[str]:
        text_contents = _extract_text_from_node(node)
        default_texts = [normalize_text(text, self.config.case_insensitive) for text in text_contents]
        return default_texts

    # -------------
    # existing_languages
    # -------------
    def get_existing_languages(self, text_elements):
        existing_languages = {t.get("systemLanguage") for t in text_elements if t.get("systemLanguage")}
        return existing_languages

    # -------------
    #  enrich mappings
    # -------------
    def enrich_all_mappings(self, mapping, default_texts) -> TranslationMapping:
        return self.year_handler.enrich_mapping_for_switch(
            mapping,
            default_texts,
            case_insensitive=self.config.case_insensitive,
        )

    # -------------
    #
    # -------------
    def get_available_translations(self, default_texts, mapping):
        available_translations = {}
        for text in default_texts:
            key = text.lower() if self.config.case_insensitive else text
            if key in mapping:
                available_translations[key] = mapping[key]
            else:
                logger.debug(f"No mapping for '{key}'")
        return available_translations

    # -------------
    #
    # -------------
    def all_languages(self, available_translations):
        langs_to_process = set()
        for data in available_translations.values():
            langs_to_process.update(data.keys())
        return langs_to_process

    # -------------
    # node functions
    # -------------
    def create_node(self, node, mapping, lang) -> etree.Element:
        new_node = etree.Element(node.tag, attrib=node.attrib)
        new_node.set("systemLanguage", lang)
        original_id = node.get("id")

        if original_id:
            new_id = self.id_manager.allocate_clone(original_id, lang)
            new_node.set("id", new_id)

        tspans = node.xpath("./svg:tspan", namespaces={"svg": SVG_NS})

        if tspans:
            for tspan in tspans:
                new_tspan = etree.Element(tspan.tag, attrib=tspan.attrib)

                translated = self.get_key_lang(tspan.text, lang, mapping, normalize=True)
                new_tspan.text = translated or ""

                # Generate unique ID for tspan if needed
                original_tspan_id = tspan.get("id")
                if original_tspan_id:
                    new_tspan_id = self.id_manager.allocate_clone(original_tspan_id, lang)
                    new_tspan.set("id", new_tspan_id)

                new_node.append(new_tspan)

        else:
            translated = self.get_key_lang(node.text, lang, mapping, normalize=True)
            new_node.text = translated or ""

        return new_node

    def update_node(self, node, default_texts, available_translations, lang):
        tspans = node.xpath("./svg:tspan", namespaces={"svg": SVG_NS})

        if not tspans:
            return

        for i, tspan in enumerate(tspans):
            if i >= len(default_texts):
                logger.warning(
                    "Language node '%s' has more tspans than the default node; stopping at %d",
                    lang,
                    i,
                )
                break
            english_text = default_texts[i]

            text = self.get_key_lang(english_text, lang, available_translations)

            if text:
                tspan.text = text

    def get_key_lang(
        self,
        key: str | None,
        lang: str,
        data: dict[str, dict[str, str]],
        normalize: bool = False,
    ) -> str | None:

        def get_key(_key) -> str | None:
            if _key in data and lang in data[_key]:
                return data[_key][lang]
            return None

        if key is None:
            return None

        if normalize:
            key = normalize_text(key)

        result = get_key(key)

        if not result and self.config.case_insensitive:
            result = get_key(key.lower())

        return result


__all__ = [
    "SwitchProcessor",
]
