"""Utilities for extracting translation data from SVG files."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from lxml import etree

from ..config import TranslationConfig
from ..io.svg_document import SvgDocument
from ..titles_workers import make_new_title_translations, make_title_translations
from ..utils import normalize_text

logger = logging.getLogger(__name__)


@dataclass
class ExtractorData:
    """Container for extracted SVG translation data."""

    new: dict[str, dict[str, str]] = field(default_factory=dict)
    title: dict[str, dict[str, str]] = field(default_factory=dict)
    title_new: dict[str, dict[str, str]] = field(default_factory=dict)
    tspans_by_id: dict[str, str] = field(default_factory=dict)
    error: str = ""

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


class SVGTranslationExtractor:
    """
    Extract translations from an SVG into a TranslationMapping.
    """

    def __init__(
        self,
        config: TranslationConfig | None = None,
    ) -> None:
        """ """
        self.config = config or TranslationConfig()

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

            default_texts = [normalize_text(text, self.config.case_insensitive) for text in text_contents]
            # for text in default_texts: key = text.lower() if self.config.case_insensitive else text
            new_keys.extend(default_texts)

        logger.debug(f"new_keys: {len(new_keys):,}, default_tspans_by_id: {len(default_tspans_by_id):,}")
        logger.debug(f"new_keys:{new_keys}")
        logger.debug(f"default_tspans_by_id:{default_tspans_by_id}")

        return new_keys, default_tspans_by_id

    def process_switch_translations(
        self,
        text_elements,
        default_tspans_by_id: dict[str, str],
        translations: ExtractorData,
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

                # store_key = english_text if english_text in new_translations else english_text.lower()
                store_key = normalize_text(english_text, self.config.case_insensitive)
                if store_key in translations.new:
                    translations.new[store_key][system_lang] = normalized_translation

        return switch_translations

    # ------------------------------------------------------------------
    # Per-switch logic
    # ------------------------------------------------------------------
    def process_switches(self, root: etree.Element, translations) -> None:
        # Find all switch elements
        switches = root.xpath("//svg:switch", namespaces={"svg": "http://www.w3.org/2000/svg"})
        logger.debug(f"Found {len(switches)} switch elements")

        for switch in switches:
            # Find all text elements within this switch
            text_elements = switch.xpath("./svg:text", namespaces={"svg": "http://www.w3.org/2000/svg"})

            if not text_elements:
                continue

            new_keys, default_tspans_by_id = self.get_english_default_texts(text_elements)

            translations.tspans_by_id.update(default_tspans_by_id)
            for x in new_keys:
                store_key = normalize_text(x, self.config.case_insensitive)
                if store_key not in translations.new:
                    translations.new[store_key] = {}

            self.process_switch_translations(text_elements, default_tspans_by_id, translations)

        if translations.new:
            translations.title = make_title_translations(translations.new)
            translations.title_new = make_new_title_translations(translations.new)

    def extract_from_root(self, root: etree._Element) -> ExtractorData:
        mapping = ExtractorData()
        self.process_switches(root, mapping)

        return mapping

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def extract(self, path: Path | str) -> ExtractorData:
        """
        Extract translation strings from an SVG file into a structured dictionary.
        """
        mapping = ExtractorData()
        logger.debug(f"Extracting translations from {path}")

        try:
            doc = SvgDocument.load(path, config=self.config)
        except FileNotFoundError:
            logger.error(f"SVG file not found: {path}")
            mapping.error = "File not found"
            return mapping
        except (etree.XMLSyntaxError, OSError) as exc:
            logger.error(f"Failed to parse SVG file {path}: {exc}")
            mapping.error = "Failed to parse SVG file"
            return mapping

        return self.extract_from_root(doc.root)


__all__ = [
    "SVGTranslationExtractor",
]
