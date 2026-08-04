"""Utilities for extracting translation data from SVG files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from lxml import etree

from ..config import TranslationConfig
from ..core.mapping import TranslationMapping
from ..core import SwitchNode, TextNode
from ..io.svg_document import SvgDocument
from ..titles import YearTitleHandler
from ..utils.text import normalize_text
from .strategies import CompositeMatchingStrategy, MatchingStrategy

logger = logging.getLogger(__name__)
SVG_NS = {"svg": "http://www.w3.org/2000/svg"}


class SVGTranslationExtractor:
    """
    Extract translations from an SVG into a TranslationMapping.
    """

    def __init__(
        self,
        config: TranslationConfig | None = None,
        matching_strategy: MatchingStrategy | None = None,
    ) -> None:
        self.config = config or TranslationConfig()
        self.year_handler = YearTitleHandler(self.config)
        self.strategy = matching_strategy or CompositeMatchingStrategy()

    # ------------------------------------------------------------------
    # Per-switch logic
    # ------------------------------------------------------------------
    def _process_switch_legacy(
        self,
        switch: etree.Element,
        mapping: TranslationMapping,
    ) -> None:
        new_switch = SwitchNode(switch)
        # Return the default (no systemLanguage) text node, if any.
        default: TextNode | None = new_switch.default_text_node()
        if default is None:
            return

        # Find all text elements within this switch
        text_elements = switch.xpath("./svg:text", namespaces=SVG_NS)

        if not text_elements:
            return

        # Record diagnostic id → text (optional)
        new_keys, default_tspans_by_id = self.get_english_default_texts(text_elements)

        mapping.tspans_by_id.update(default_tspans_by_id)

        # Ensure keys exist in mapping.new
        for x in new_keys:
            key = normalize_text(x, self.config.case_insensitive)
            mapping.new.setdefault(key, {})

        self.process_switch_translations(text_elements, default_tspans_by_id, mapping)

    def extract_from_root(self, root: etree._Element) -> TranslationMapping:
        mapping = TranslationMapping()
        # Find all switch elements
        switches = root.xpath("//svg:switch", namespaces=SVG_NS)
        logger.debug("Found %d switch elements", len(switches))

        for switch_el in switches:
            # self._process_switch(SwitchNode(switch_el), mapping)
            self._process_switch_legacy(switch_el, mapping)

        if self.config.enable_year_titles and mapping.new:
            self.year_handler.build_templates(mapping)

        return mapping

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(self, path: Path | str) -> TranslationMapping:
        """
        Extract translation strings from an SVG file into a structured dictionary.
        """
        mapping = TranslationMapping()
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

    def extract_json(self, path: Path | str) -> dict[str, Any]:
        """
        Extract translation strings from an SVG file into a structured dictionary.
        """
        result = self.extract(path)

        return result.to_json()


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

            tspans = text_elem.xpath("./svg:tspan", namespaces=SVG_NS)
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
        mapping: TranslationMapping,
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

            tspans = text_elem.xpath("./svg:tspan", namespaces=SVG_NS)
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
                if store_key in mapping.new:
                    mapping.new[store_key][system_lang] = normalized_translation

        return switch_translations

__all__ = [
    "SVGTranslationExtractor",
]
