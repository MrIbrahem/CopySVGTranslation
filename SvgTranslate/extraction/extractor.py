"""Utilities for extracting translation data from SVG files."""

from pathlib import Path
import logging

from lxml import etree

from ..text_utils import normalize_text

logger = logging.getLogger(__name__)


def extract(svg_file_path, case_insensitive: bool = True):
    """Extract translations from an SVG file and return them as a dictionary."""
    svg_file_path = Path(svg_file_path)

    if not svg_file_path.exists():
        logger.error("SVG file not found: %s", svg_file_path)
        return None

    logger.debug("Extracting translations from %s", svg_file_path)

    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(str(svg_file_path), parser)
    root = tree.getroot()

    switches = root.xpath('//svg:switch', namespaces={'svg': 'http://www.w3.org/2000/svg'})
    logger.debug("Found %s switch elements", len(switches))

    translations = {"new": {"default_tspans_by_id": {}}, "old_way": {}}
    processed_switches = 0

    for switch in switches:
        text_elements = switch.xpath('./svg:text', namespaces={'svg': 'http://www.w3.org/2000/svg'})

        if not text_elements:
            continue

        switch_translations = {}
        tspans_by_id = {}
        default_texts = []

        for text_elem in text_elements:
            system_lang = text_elem.get('systemLanguage')
            if system_lang:
                continue

            tspans = text_elem.xpath('./svg:tspan', namespaces={'svg': 'http://www.w3.org/2000/svg'})
            if tspans:
                tspans_by_id = {tspan.get('id'): tspan.text.strip() for tspan in tspans if tspan.text}
                translations["new"]["default_tspans_by_id"].update(tspans_by_id)
                text_contents = [tspan.text.strip() if tspan.text else "" for tspan in tspans]
            else:
                text_contents = [text_elem.text.strip()] if text_elem.text else [""]

            default_texts = [normalize_text(text, case_insensitive) for text in text_contents]
            for text in default_texts:
                key = text.lower() if case_insensitive else text
                translations["new"].setdefault(key, {})

        for text_elem in text_elements:
            system_lang = text_elem.get('systemLanguage')
            if not system_lang:
                continue

            tspans = text_elem.xpath('./svg:tspan', namespaces={'svg': 'http://www.w3.org/2000/svg'})
            if tspans:
                tspans_to_id = {tspan.text.strip(): tspan.get('id') for tspan in tspans if tspan.text}
                text_contents = [tspan.text.strip() if tspan.text else "" for tspan in tspans]
            else:
                tspans_to_id = {}
                text_contents = [text_elem.text.strip()] if text_elem.text else [""]

            switch_translations[system_lang] = [normalize_text(text) for text in text_contents]

            for text in text_contents:
                normalized_translation = normalize_text(text)
                base_id = tspans_to_id.get(text.strip(), "").split("-")[0].strip()
                english_text = (
                    translations["new"]["default_tspans_by_id"].get(base_id)
                    or translations["new"]["default_tspans_by_id"].get(base_id.lower())
                )
                logger.debug("Mapping %s to %s", base_id, english_text)
                if not english_text:
                    continue

                store_key = english_text if english_text in translations["new"] else english_text.lower()
                if store_key in translations["new"]:
                    translations["new"][store_key][system_lang] = normalized_translation

        if default_texts and switch_translations:
            default_key = default_texts[0]
            translations["old_way"].setdefault(
                default_key,
                {"_texts": default_texts, "_translations": {}},
            )

            for lang, translated_texts in switch_translations.items():
                translations["old_way"][default_key]['_translations'][lang] = translated_texts

            processed_switches += 1
            logger.debug("Processed switch with default texts: %s", default_texts)

    logger.debug("Extracted translations for %s switches", processed_switches)

    all_languages = set()
    for text_dict in translations["old_way"].values():
        all_languages.update(text_dict.get("_translations", {}).keys())
    logger.debug("Found translations in %s languages: %s", len(all_languages), ", ".join(sorted(all_languages)))

    translations["title"] = {}
    for key, mapping in list(translations["new"].items()):
        if key == "default_tspans_by_id":
            continue
        if key and key[-4:].isdigit():
            year = key[-4:]
            if key != year and all(value[-4:].isdigit() and value[-4:] == year for value in mapping.values()):
                translations["title"][key[:-4]] = {lang: text[:-4] for lang, text in mapping.items()}

    if not translations["new"]["default_tspans_by_id"]:
        translations["new"].pop("default_tspans_by_id")

    if not translations["new"]:
        translations.pop("new")

    return translations
