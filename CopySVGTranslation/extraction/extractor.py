"""Utilities for extracting translation data from SVG files."""

from pathlib import Path
import logging

from lxml import etree

from ..text_utils import normalize_text
from ..titles import make_title_translations

logger = logging.getLogger("CopySVGTranslation")

def get_english_default_texts(text_elements, case_insensitive):
    new_keys = []
    default_tspans_by_id = {}

    for text_elem in text_elements:
        system_lang = text_elem.get('systemLanguage')
        if system_lang:
            continue

        tspans = text_elem.xpath('./svg:tspan', namespaces={'svg': 'http://www.w3.org/2000/svg'})
        text_contents = []
        # ---
        if tspans:
            tspans_by_id = {
                tspan.get('id'): tspan.text.strip()
                for tspan in tspans
                if tspan.text and tspan.get('id') and tspan.text.strip()
            }
            default_tspans_by_id.update(tspans_by_id)
            text_contents = [tspan.text.strip() for tspan in tspans if tspan.text]
            # ---
        else:
            text_contents = [text_elem.text.strip()] if text_elem.text else [""]

        default_texts = [normalize_text(text, case_insensitive) for text in text_contents]
        # for text in default_texts: key = text.lower() if case_insensitive else text
        new_keys.extend(default_texts)

    logger.debug(f"new_keys: {len(new_keys):,}, default_tspans_by_id: {len(default_tspans_by_id):,}")
    logger.debug(f"new_keys:{new_keys}")
    logger.debug(f"default_tspans_by_id:{default_tspans_by_id}")

    return new_keys, default_tspans_by_id


def extract(svg_file_path, case_insensitive: bool = True):
    """
    Extract translation strings from an SVG file into a structured dictionary.

    Parses the SVG, collects default (source) text and corresponding translations found in sibling text elements with a `systemLanguage` attribute, and returns a mapping suitable for localization workflows. Title-like entries that end with a four-digit year are separated into a `title` section with the year removed.

    Parameters:
        svg_file_path (str | Path): Path to the SVG file to process.
        case_insensitive (bool): If true, treat default text keys case-insensitively by lowercasing them.

    Returns:
        dict | None: A dictionary containing extracted translations (may include a "new" mapping of source text to per-language translations and a "title" mapping), or `None` if the file does not exist or could not be parsed.
    """
    svg_file_path = Path(str(svg_file_path))

    if not svg_file_path.exists():
        logger.error(f"SVG file not found: {svg_file_path}")
        return None

    logger.debug(f"Extracting translations from {svg_file_path}")

    # Parse SVG as XML
    parser = etree.XMLParser(remove_blank_text=True)

    try:
        tree = etree.parse(str(svg_file_path), parser)
    except (etree.XMLSyntaxError, OSError) as exc:
        logger.error(f"Failed to parse SVG file {svg_file_path}: {exc}")
        return None
    root = tree.getroot()

    # Find all switch elements
    switches = root.xpath('//svg:switch', namespaces={'svg': 'http://www.w3.org/2000/svg'})
    logger.debug(f"Found {len(switches)} switch elements")

    translations = {
        "new": {},
        "title": {},
        "tspans_by_id": {}
    }
    tspans_by_id = translations["tspans_by_id"]

    for switch in switches:
        # Find all text elements within this switch
        text_elements = switch.xpath('./svg:text', namespaces={'svg': 'http://www.w3.org/2000/svg'})

        if not text_elements:
            continue

        new_keys, default_tspans_by_id = get_english_default_texts(text_elements, case_insensitive)

        tspans_by_id.update(default_tspans_by_id)

        translations["new"].update({x: {} for x in new_keys if x not in translations["new"]})
        switch_translations = {}

        for text_elem in text_elements:
            system_lang = text_elem.get('systemLanguage')
            if not system_lang:
                continue

            tspans = text_elem.xpath('./svg:tspan', namespaces={'svg': 'http://www.w3.org/2000/svg'})
            if tspans:
                tspans_to_id = {tspan.text.strip(): tspan.get('id') for tspan in tspans if tspan.text and tspan.text.strip() and tspan.get('id')}
                # text_contents = [tspan.text.strip() if tspan.text else "" for tspan in tspans]
                text_contents = [tspan.text.strip() for tspan in tspans if tspan.text]
            else:
                tspans_to_id = {}
                text_contents = [text_elem.text.strip()] if text_elem.text else [""]

            switch_translations[system_lang] = [normalize_text(text) for text in text_contents]

            for text in text_contents:
                normalized_translation = normalize_text(text)
                base_id = tspans_to_id.get(text.strip(), "")
                if not base_id:
                    continue

                base_id = base_id.split("-")[0].strip()

                english_text = default_tspans_by_id.get(base_id) or default_tspans_by_id.get(base_id.lower())

                logger.debug(f"{base_id=}, {english_text=}")

                if not english_text:
                    continue

                store_key = english_text if english_text in translations["new"] else english_text.lower()
                if store_key in translations["new"]:
                    translations["new"][store_key][system_lang] = normalized_translation

    translations["title"] = make_title_translations(translations["new"])

    return translations
