"""Utilities for extracting translation data from SVG files."""

import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from lxml import etree

from ..titles import make_title_translations
from ..titles_new import make_new_title_translations
from ..utils import normalize_text

logger = logging.getLogger(__name__)


@dataclass
class Translations:
    """Container for extracted SVG translation data."""

    new: dict[str, dict[str, str]] = field(default_factory=dict)
    title: dict[str, Any] = field(default_factory=dict)
    title_new: dict[str, Any] = field(default_factory=dict)
    tspans_by_id: dict[str, str] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


class SVGTranslationExtractor:
    """Extracts translation data from an SVG file."""

    def __init__(self, svg_file_path: str | Path, case_insensitive: bool = True):
        """
        Parameters:
            svg_file_path (str | Path): Path to the SVG file to process.
            case_insensitive (bool): If True, default text keys are treated
                case-insensitively (lowercased).
        """
        self.svg_file_path = Path(str(svg_file_path))
        self.case_insensitive = case_insensitive
        self.translations = Translations()

    def get_english_default_texts(self, text_elements):
        """
        Collect the default (source) English texts from text elements that
        do not have a systemLanguage attribute, along with a mapping of
        tspan id -> default text for later lookup.
        """
        new_keys = []
        default_tspans_by_id = {}

        for text_elem in text_elements:
            system_lang = text_elem.get("systemLanguage")
            if system_lang:
                continue

            tspans = text_elem.xpath("./svg:tspan", namespaces={"svg": "http://www.w3.org/2000/svg"})
            text_contents = []
            # ---
            if tspans:
                tspans_by_id = {
                    tspan.get("id"): tspan.text.strip()
                    for tspan in tspans
                    if tspan.text and tspan.get("id") and tspan.text.strip()
                }
                default_tspans_by_id.update(tspans_by_id)
                text_contents = [tspan.text.strip() for tspan in tspans if tspan.text]
            else:
                text_contents = [text_elem.text.strip()] if text_elem.text else [""]

            default_texts = [normalize_text(text, self.case_insensitive) for text in text_contents]
            # for text in default_texts: key = text.lower() if self.case_insensitive else text
            new_keys.extend(default_texts)

        logger.debug(f"new_keys: {len(new_keys):,}, default_tspans_by_id: {len(default_tspans_by_id):,}")
        logger.debug(f"new_keys:{new_keys}")
        logger.debug(f"default_tspans_by_id:{default_tspans_by_id}")

        return new_keys, default_tspans_by_id

    def process_switch_translations(
        self,
        text_elements,
        default_tspans_by_id: dict[str, str],
    ) -> dict[str, list[str]]:
        """
        Process the text elements that carry a systemLanguage attribute
        within a single switch element, and update new_translations in
        place with the discovered translations, matched via tspan ids
        against the default English text.

        Parameters:
            text_elements: <text> elements inside a switch element.
            default_tspans_by_id: Mapping of id -> corresponding default
                English text.

        Returns:
            dict: Mapping of system language -> list of normalized texts
            for that language.
        """
        new_translations = self.translations.new
        switch_translations: dict[str, list[str]] = {}

        for text_elem in text_elements:
            system_lang = text_elem.get("systemLanguage")
            if not system_lang:
                continue

            tspans = text_elem.xpath("./svg:tspan", namespaces={"svg": "http://www.w3.org/2000/svg"})
            if tspans:
                tspans_to_id = {
                    tspan.text.strip(): tspan.get("id")
                    for tspan in tspans
                    if tspan.text and tspan.text.strip() and tspan.get("id")
                }
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

                store_key = english_text if english_text in new_translations else english_text.lower()
                if store_key in new_translations:
                    new_translations[store_key][system_lang] = normalized_translation

        return switch_translations

    def process_switches(self, root: etree.Element) -> None:
        # Find all switch elements
        switches = root.xpath("//svg:switch", namespaces={"svg": "http://www.w3.org/2000/svg"})
        logger.debug(f"Found {len(switches)} switch elements")

        for switch in switches:
            # Find all text elements within this switch
            text_elements = switch.xpath("./svg:text", namespaces={"svg": "http://www.w3.org/2000/svg"})

            if not text_elements:
                continue

            new_keys, default_tspans_by_id = self.get_english_default_texts(text_elements)

            self.translations.tspans_by_id.update(default_tspans_by_id)

            self.translations.new.update({x: {} for x in new_keys if x not in self.translations.new})

            self.process_switch_translations(text_elements, default_tspans_by_id)

    def extract(self) -> dict[str, Any] | None:
        """
        Extract translation strings from an SVG file into a structured dictionary.

        Parses the SVG, collects default (source) text and corresponding
        translations found in sibling text elements with a systemLanguage
        attribute, and returns a mapping suitable for localization workflows.
        Title-like entries that end with a four-digit year are separated
        into a "title" section with the year removed.

        Returns:
            dict | None: A dictionary containing extracted translations (may
            include a "new" mapping of source text to per-language
            translations and a "title" mapping), or None if the file does
            not exist or could not be parsed.
        """
        if not self.svg_file_path.exists():
            logger.error(f"SVG file not found: {self.svg_file_path}")
            return None

        logger.debug(f"Extracting translations from {self.svg_file_path}")

        # Parse SVG as XML
        parser = etree.XMLParser(remove_blank_text=True)

        try:
            tree = etree.parse(str(self.svg_file_path), parser)
        except (etree.XMLSyntaxError, OSError) as exc:
            logger.error(f"Failed to parse SVG file {self.svg_file_path}: {exc}")
            return None
        root = tree.getroot()

        self.process_switches(root)
        self.translations.title = make_title_translations(self.translations.new)
        self.translations.title_new = make_new_title_translations(self.translations.new)

        return self.translations.to_json()


def extract(
    svg_file_path: str | Path,
    case_insensitive: bool = True,
) -> dict[str, Any] | None:
    """
    Legacy function-style wrapper around SVGTranslationExtractor, kept for
    backward compatibility with existing callers.

    Parameters:
        svg_file_path (str | Path): Path to the SVG file to process.
        case_insensitive (bool): If true, treat default text keys
            case-insensitively by lowercasing them.

    Returns:
        dict | None: A dictionary containing extracted translations, or
        None if the file does not exist or could not be parsed.
    """
    extractor = SVGTranslationExtractor(
        svg_file_path,
        case_insensitive=case_insensitive,
    )
    result = extractor.extract()
    return result


__all__ = [
    "SVGTranslationExtractor",
    "extract",
]
