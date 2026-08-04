# injection/switch_processor.py
from __future__ import annotations

import logging
from collections.abc import Mapping

from lxml import etree

from ..result import InjectorStats
from ..titles import get_new_titles_translations
from ..utils import (
    extract_text_from_node,
    normalize_text,
)
from ..utils.injection_utils import (
    generate_unique_id,
)

logger = logging.getLogger(__name__)
SVG_NS = "http://www.w3.org/2000/svg"


class SwitchProcessor:
    def __init__(self, overwrite: bool, case_insensitive: bool) -> None:
        self.overwrite = overwrite
        self.case_insensitive = case_insensitive

    def process(
        self,
        switch_element: etree._Element,
        mapping: Mapping,
        stats: InjectorStats,
        existing_ids: set[str],
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
        svg_ns = {"svg": "http://www.w3.org/2000/svg"}

        # all_mappings_title = mapping.get("title", {})
        all_mappings_title_new = mapping.get("title_new", {})
        all_mappings = dict(mapping.get("new", mapping))

        text_elements = switch_element.xpath("./svg:text", namespaces=svg_ns)
        if not text_elements:
            return

        default_texts = None
        default_node = None

        for text_elem in text_elements:
            system_lang = text_elem.get("systemLanguage")
            if system_lang:
                continue

            text_contents = extract_text_from_node(text_elem)
            default_texts = [normalize_text(text, self.case_insensitive) for text in text_contents]
            default_node = text_elem
            break

        if not default_texts or default_node is None:
            return

        new_titles_translations = get_new_titles_translations(all_mappings_title_new, default_texts)

        # all_mappings.update(titles_translations)
        # all_mappings.update(new_titles_translations)

        for key, translations in new_titles_translations.items():
            all_mappings.setdefault(key, {}).update(translations)

        # Determine translations for each text line
        available_translations = {}
        for text in default_texts:
            key = text.lower() if self.case_insensitive else text
            if key in all_mappings:
                available_translations[key] = all_mappings[key]
            else:
                logger.debug(f"No mapping for '{key}'")

        if not available_translations:
            return

        existing_languages = {t.get("systemLanguage") for t in text_elements if t.get("systemLanguage")}

        # We assume all texts share same set of languages
        all_langs = set()
        for data in available_translations.values():
            all_langs.update(data.keys())

        for lang in all_langs:
            if lang in existing_languages and not self.overwrite:
                stats.skipped_translations += 1
                continue

            # Create or update node
            if lang in existing_languages and self.overwrite:
                for text_elem in text_elements:
                    if text_elem.get("systemLanguage") != lang:
                        continue

                    tspans = text_elem.xpath("./svg:tspan", namespaces=svg_ns)
                    for i, tspan in enumerate(tspans):
                        if i >= len(default_texts):
                            logger.warning(
                                "Language node '%s' has more tspans than the default node; stopping at %d",
                                lang,
                                i,
                            )
                            break
                        english_text = default_texts[i]
                        lookup_key = english_text.lower() if self.case_insensitive else english_text
                        if english_text in available_translations and lang in available_translations[english_text]:
                            tspan.text = available_translations[english_text][lang]
                        elif lookup_key in available_translations and lang in available_translations[lookup_key]:
                            tspan.text = available_translations[lookup_key][lang]

                    stats.updated_translations += 1
                    break
                continue

            new_node = etree.Element(default_node.tag, attrib=default_node.attrib)
            new_node.set("systemLanguage", lang)
            original_id = default_node.get("id")

            if original_id:
                new_id = generate_unique_id(original_id, lang, existing_ids)
                new_node.set("id", new_id)
                existing_ids.add(new_id)

            tspans = default_node.xpath("./svg:tspan", namespaces=svg_ns)

            if tspans:
                for tspan in tspans:
                    new_tspan = etree.Element(tspan.tag, attrib=tspan.attrib)
                    english_text = normalize_text(tspan.text or "")
                    key = english_text.lower() if self.case_insensitive else english_text
                    translated = all_mappings.get(key, {}).get(lang, english_text)
                    new_tspan.text = translated

                    # Generate unique ID for tspan if needed
                    original_tspan_id = tspan.get("id")
                    if original_tspan_id:
                        new_tspan_id = generate_unique_id(original_tspan_id, lang, existing_ids)
                        new_tspan.set("id", new_tspan_id)
                        existing_ids.add(new_tspan_id)

                    new_node.append(new_tspan)

            else:
                english_text = normalize_text(default_node.text or "")
                key = english_text.lower() if self.case_insensitive else english_text
                new_node.text = all_mappings.get(key, {}).get(lang, english_text)

            switch_element.append(new_node)
            stats.inserted_translations += 1

        stats.processed_switches += 1
